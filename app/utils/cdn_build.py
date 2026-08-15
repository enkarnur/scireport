#!/usr/bin/env python3
"""Runtime frontend build with optional CDN resource sync.

This script lives under `app/utils/` and is invoked by `app/frontend/package.json`
after the public `build` command passes TypeScript checking. It invokes Vite
directly so CDN fallback does not repeat that check.
"""
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

CDN_FILE_RECORD_REL_PATH = "app/data/cdn_file_record.json"
CDN_STATIC_EXTENSIONS = {
    ".js",
    ".mjs",
    ".cjs",
    ".css",
    ".map",
    ".json",
    ".txt",
    ".wasm",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
    ".svg",
    ".ico",
    ".bmp",
    ".cur",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp3",
    ".mp4",
    ".webm",
    ".ogg",
    ".wav",
}


class CdnBuildError(Exception):
    """CDN build/sync failed; caller should fallback to normal build."""


def log(message: str) -> None:
    print(f"[cdn-build] {message}", flush=True)


def run(cmd: list[str], cwd: Path, desc: str) -> None:
    log(desc)
    result = subprocess.run(cmd, cwd=str(cwd), text=True)
    if result.returncode != 0:
        raise CdnBuildError(f"command failed ({result.returncode}): {' '.join(cmd)}")


def plugin_dir() -> Path:
    return APP_ROOT


def app_json_path(root: Path) -> Path | None:
    for name in ("app.json", "plugin.json"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def load_app_json(root: Path) -> dict:
    path = app_json_path(root)
    if not path:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CdnBuildError(f"read {path.name} failed: {exc}") from exc


def normalize_cdn_prefix(item: str) -> str:
    normalized = item.strip().rstrip("/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def cdn_prefixes(app_json: dict) -> list[str]:
    prefixes: list[str] = []
    seen = set()
    for svc in app_json.get("services") or []:
        raw = svc.get("upload_to_cdn") or []
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, str):
                continue
            prefix = normalize_cdn_prefix(item)
            if prefix and prefix not in seen:
                seen.add(prefix)
                prefixes.append(prefix)
    return prefixes


def is_static_file(rel_path: str) -> bool:
    return Path(rel_path).suffix.lower() in CDN_STATIC_EXTENSIONS


def collect_current_cdn_files(root: Path, prefixes: list[str]) -> tuple[list[str], list[str], list[str]]:
    files: list[str] = []
    seen = set()
    hit = set()
    root_resolved = root.resolve()

    for prefix in prefixes:
        target = (root / prefix).resolve()
        try:
            target.relative_to(root_resolved)
        except ValueError:
            continue

        candidates: list[Path] = []
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            for walk_root, _, filenames in os.walk(str(target)):
                candidates.extend(Path(walk_root) / filename for filename in filenames)

        for candidate in candidates:
            rel = candidate.relative_to(root).as_posix()
            if not is_static_file(rel):
                continue
            hit.add(prefix)
            if rel in seen:
                continue
            seen.add(rel)
            files.append(rel)

    hit_prefixes = [prefix for prefix in prefixes if prefix in hit]
    miss_prefixes = [prefix for prefix in prefixes if prefix not in hit]
    return sorted(files), hit_prefixes, miss_prefixes


def resource_source_path(resource) -> str:
    if not isinstance(resource, dict):
        return ""
    return str(
        resource.get("source_path")
        or resource.get("SourcePath")
        or resource.get("sourcePath")
        or resource.get("path")
        or ""
    ).strip().lstrip("/")


def record_path(root: Path) -> Path:
    return root / CDN_FILE_RECORD_REL_PATH


def load_record(root: Path) -> list[str]:
    path = record_path(root)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"read record failed, treat as empty: {exc}")
        return []

    raw_files = []
    if isinstance(data, list):
        raw_files = data
    elif isinstance(data, dict):
        raw_files = data.get("files") or data.get("resources") or data.get("uploaded_files") or []

    files: list[str] = []
    seen = set()
    for item in raw_files:
        path_value = item if isinstance(item, str) else resource_source_path(item)
        path_value = str(path_value or "").strip().lstrip("/")
        if path_value and path_value not in seen:
            seen.add(path_value)
            files.append(path_value)
    return files


def write_record(root: Path, files: list[str]) -> None:
    normalized: list[str] = []
    seen = set()
    for item in files:
        path_value = str(item or "").strip().lstrip("/")
        if path_value and path_value not in seen:
            seen.add(path_value)
            normalized.append(path_value)
    path = record_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(normalized), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def persistent_record_path() -> Path | None:
    """容器维度的 CDN 记录路径，落在 AIME_PLUGIN_DATA_DIR/cdn_file_record.json。

    该目录是应用独占的持久卷，即使代码目录被删除（新版本重装等）也不会丢失，
    避免下次上传时把已经上过 CDN 的资源当成新增再全量上传一次。
    """
    data_dir = os.environ.get("AIME_PLUGIN_DATA_DIR", "").strip()
    if not data_dir:
        return None
    return Path(data_dir) / "cdn_file_record.json"


def load_persistent_record() -> list[str]:
    """读取容器维度持久化的 CDN 记录，缺失/损坏都按空处理。"""
    path = persistent_record_path()
    if path is None or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"read persistent record failed, treat as empty: {exc}")
        return []

    raw_files = []
    if isinstance(data, list):
        raw_files = data
    elif isinstance(data, dict):
        raw_files = data.get("files") or data.get("resources") or data.get("uploaded_files") or []

    files: list[str] = []
    seen = set()
    for item in raw_files:
        path_value = item if isinstance(item, str) else resource_source_path(item)
        path_value = str(path_value or "").strip().lstrip("/")
        if path_value and path_value not in seen:
            seen.add(path_value)
            files.append(path_value)
    return files


def write_persistent_record(files: list[str]) -> None:
    """覆盖写入容器维度的 CDN 记录。写失败仅打 log，不影响主流程。"""
    path = persistent_record_path()
    if path is None:
        return
    normalized: list[str] = []
    seen = set()
    for item in files:
        path_value = str(item or "").strip().lstrip("/")
        if path_value and path_value not in seen:
            seen.add(path_value)
            normalized.append(path_value)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sorted(normalized), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        log(f"write persistent record failed: {exc}")


def _workspace_path(root: Path) -> Path | None:
    workspace = os.environ.get("AIME_WORKSPACE_PATH", "").strip()
    if workspace:
        return Path(workspace).expanduser().resolve()
    resolved = root.resolve()
    parts = resolved.parts
    for index in range(len(parts) - 2):
        if parts[index] == ".aime" and parts[index + 1] == "plugins":
            return Path(*parts[:index])
    return None


def _devkit_dir(root: Path) -> Path | None:
    workspace = _workspace_path(root)
    if workspace is None:
        return None

    routes_path = workspace / ".aime" / "plugin_runtime" / "routes.json"
    try:
        plugins = json.loads(routes_path.read_text(encoding="utf-8")).get("plugins") or []
    except Exception:
        plugins = []
    for plugin in plugins:
        if not isinstance(plugin, dict) or plugin.get("disabled"):
            continue
        if str(plugin.get("name") or "").strip() != "aime-app-devkit":
            continue
        path = Path(str(plugin.get("dir") or "").strip()).expanduser()
        if not path.is_absolute():
            path = workspace / path
        if path.is_dir():
            return path.resolve()

    plugins_dir = workspace / ".aime" / "plugins"
    try:
        candidates = plugins_dir.iterdir()
    except OSError:
        return None
    for path in candidates:
        if not path.is_dir():
            continue
        try:
            app = json.loads((path / "app.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(app.get("name") or "").strip() == "aime-app-devkit":
            return path.resolve()
    return None


def _cli_path() -> str:
    root = Path(__file__).resolve().parents[2]
    candidates = [root / "bin" / "aime-platform-cli"]
    for c in candidates:
        if c.is_file():
            return str(c)
    env_path = os.environ.get("AIME_PLATFORM_CLI_PATH", "").strip()
    if env_path and Path(env_path).is_file():
        return env_path
    devkit_dir = _devkit_dir(root)
    if devkit_dir is not None:
        devkit_server = devkit_dir / "app" / "server-go" / "bin" / "server"
        if devkit_server.is_file():
            return str(devkit_server)
    import shutil
    for name in ("server", "aime-platform-cli"):
        found = shutil.which(name)
        if found:
            return found
    raise CdnBuildError("server binary not found")


def _call_cli(args: list[str], timeout: int = 120) -> str:
    result = subprocess.run(
        [_cli_path()] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise CdnBuildError(f"cli failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _call_cli_json(args: list[str], timeout: int = 120) -> dict:
    return json.loads(_call_cli(args, timeout=timeout))


def authorization_value() -> str:
    try:
        from utils.cloud_jwt import get_cloud_credential
    except ImportError as exc:
        raise CdnBuildError("runtime Cloud JWT SDK is unavailable") from exc

    credential = get_cloud_credential()
    if not credential.access_token or not credential.token_type:
        raise CdnBuildError("cloud credential is missing access_token or token_type")
    return f"{credential.token_type} {credential.access_token}"


def is_i18n_env() -> bool:
    """非 CN 主站（aime.bytedance.net）都视为 i18n 环境。

    i18n 环境下 CDN 相关失败不允许降级为 normal build，直接抛错让 start.sh 一并失败，
    避免海外场景下静默降级导致资源没上到 CDN。
    """
    host = os.environ.get("IRIS_RUNTIME_AIME_API_HOST", "").strip().lower()
    if host and host != "aime.bytedance.net":
        return True
    override = os.environ.get("APP_PLATFORM_URL", "").strip().lower()
    if override and "aime.bytedance.net" not in override:
        return True
    return False



def platform_headers() -> dict[str, str]:
    return {"Authorization": authorization_value()}



def make_resource_zip(root: Path, source_paths: list[str]) -> Path:
    tmp_dir = Path(tempfile.mkdtemp(prefix="aime-cdn-build-"))
    zip_path = tmp_dir / f"{root.name}.zip"
    root_resolved = root.resolve()
    include_paths = set(source_paths)

    manifest = app_json_path(root)
    if manifest:
        include_paths.add(manifest.relative_to(root).as_posix())
    record = record_path(root)
    if record.is_file():
        include_paths.add(record.relative_to(root).as_posix())

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(include_paths):
            candidate = (root / rel).resolve()
            try:
                candidate.relative_to(root_resolved)
            except ValueError:
                continue
            if not candidate.is_file():
                continue
            zf.write(str(candidate), f"{root.name}/{rel}")
    if zip_path.stat().st_size <= 0:
        raise CdnBuildError("created empty resource zip")
    return zip_path


def upload_zip(root: Path, zip_path: Path) -> str:
    result = _call_cli_json(
        ["upload-package", "--file", str(zip_path), "--token", authorization_value()],
        timeout=180,
    )
    url = result.get("url", "")
    if not url:
        raise CdnBuildError("upload-package returned no url")
    return url


def upload_resources(app_id: str, app_package_url: str) -> tuple[list[dict], int, int]:
    result = _call_cli_json(
        [
            "upload-resources",
            "--app-id", app_id,
            "--app-package-url", app_package_url,
            "--token", authorization_value(),
        ],
        timeout=600
    )
    resources = result.get("resources", [])
    uploaded_count = result.get("uploaded_count", 0)
    skipped_count = result.get("skipped_count", 0)
    return resources, uploaded_count, skipped_count


def normal_build(frontend_dir: Path) -> None:
    run(["pnpm", "exec", "vite", "build"], cwd=frontend_dir, desc="fallback normal build")


def cdn_build(frontend_dir: Path) -> None:
    run(["pnpm", "exec", "vite", "build", "--mode", "cdn"], cwd=frontend_dir, desc="cdn build")


def main() -> int:
    root = plugin_dir()
    frontend_dir = root / "app" / "frontend"
    app_json = load_app_json(root)
    prefixes = cdn_prefixes(app_json)
    if not prefixes or not app_json.get("id"):
        log("mode=normal reason=no_upload_to_cdn_or_app_id")
        normal_build(frontend_dir)
        return 0

    try:
        cdn_build(frontend_dir)
        current_files, hit_prefixes, miss_prefixes = collect_current_cdn_files(root, prefixes)
        if miss_prefixes:
            log("miss_prefixes=" + ",".join(miss_prefixes))
        if not hit_prefixes or not current_files:
            log("mode=cdn current=0 skip_upload=true")
            return 0

        recorded_code = load_record(root)
        recorded_persistent = load_persistent_record()
        # 容器维度的 cdn_file_record.json 与代码目录下的记录取并集，避免代码目录
        # 被清空/重装后重新上传时把已经上过 CDN 的资源当成新增再全量上传一次。
        # 合并结果立即回写代码目录下的记录，让打进 zip 的记录也是并集。
        recorded = set(recorded_code) | set(recorded_persistent)
        if recorded and set(recorded_code) != recorded:
            write_record(root, sorted(recorded))
        excluded_files = [path for path in current_files if path in recorded]
        pending_files = [path for path in current_files if path not in recorded]
        log(
            f"mode=cdn current={len(current_files)} excluded={len(excluded_files)} "
            f"pending={len(pending_files)}"
        )

        if not pending_files:
            write_record(root, excluded_files)
            write_persistent_record(excluded_files)
            log("skip_upload=true reason=no_pending_files")
            return 0

        zip_path = make_resource_zip(root, current_files)
        app_package_url = upload_zip(root, zip_path)
        resources, uploaded_count, skipped_count = upload_resources(str(app_json.get("id") or ""), app_package_url)
        uploaded_files = [resource_source_path(item) for item in resources]
        uploaded_files = [path for path in uploaded_files if path]
        if not uploaded_files:
            raise CdnBuildError("upload_resources returned no uploaded resource paths")
        write_record(root, [*excluded_files, *uploaded_files])
        write_persistent_record([*excluded_files, *uploaded_files])
        log(
            f"uploaded_count={uploaded_count} skipped_count={skipped_count} "
            f"resources={len(resources)}"
        )
        return 0
    except Exception as exc:
        if is_i18n_env():
            log(f"strict=true no_fallback reason={exc}")
            raise
        log(f"fallback reason={exc}")
        normal_build(frontend_dir)
        return 0


if __name__ == "__main__":
    sys.exit(main())
