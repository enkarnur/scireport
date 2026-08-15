"""AIME 应用服务调用工具。

用于 command / hook 脚本稳定调用“当前应用自身服务”的 /api 接口：
1. 自动从 AIME_PLUGIN_DIR/app.json 获取当前 plugin id；没有环境变量时从本文件路径反推插件目录；
2. 自动从 <AIME_WORKSPACE_PATH>/.aime/plugin_runtime/routes.json 解析 service endpoint；没有 workspace 环境变量时从插件安装路径反推；
3. 自动注入 JWT 鉴权头（/api 缺少 Authorization 会被服务端鉴权中间件返回 401）；
4. 自动处理网关 gzip 响应并解析 JSON。

用法示例：

    from utils.service_client import call_service, post_json

    items = call_service("/api/items").get("data", [])
    created = post_json("/api/items", {"title": "新任务"})["data"]

注意：不要手搓裸 urllib/fetch/curl，不要写死 localhost；调用 /api 必须带鉴权头。
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from utils.cloud_jwt import CredentialError, get_cloud_credential
from utils.http_helper import safe_read_response
from utils.logger import log


class ServiceClientError(Exception):
    """调用应用服务失败。"""


def infer_plugin_dir_from_file(file_path: str | None = None) -> str:
    """从当前工具文件路径反推插件根目录。

    模板布局固定为 <plugin>/utils/service_client.py；生成后的 CLI 位于同一插件目录下，
    因此即使缺少 AIME_PLUGIN_DIR，也可以用本文件位置稳定找到 app.json。
    """
    path = Path(file_path or __file__).resolve()
    if path.parent.name == "utils":
        return str(path.parent.parent)
    return str(path.parent)


def get_plugin_dir() -> str:
    """优先使用 AIME_PLUGIN_DIR；缺失时从 service_client.py 自举反推插件目录。"""
    plugin_dir = os.environ.get("AIME_PLUGIN_DIR", "").strip()
    if plugin_dir:
        return str(Path(plugin_dir).expanduser())
    inferred = infer_plugin_dir_from_file(__file__)
    log(f"[service_client] AIME_PLUGIN_DIR 为空，已从文件路径推断 plugin_dir={inferred}")
    return inferred


def infer_workspace_from_plugin_dir(plugin_dir: str) -> str:
    """从 <workspace>/.aime/plugins/<plugin> 形式的安装路径反推 workspace。"""
    try:
        path = Path(plugin_dir).expanduser().resolve()
    except Exception:
        return ""
    parts = path.parts
    # .../<workspace>/.aime/plugins/<plugin_dir>
    for i in range(len(parts) - 2):
        if parts[i] == ".aime" and parts[i + 1] == "plugins":
            return str(Path(*parts[:i]))
    return ""


def get_workspace_path(plugin_dir: str = "") -> str:
    """优先使用 AIME_WORKSPACE_PATH；缺失时从插件安装目录反推 workspace。"""
    workspace = os.environ.get("AIME_WORKSPACE_PATH", "").strip()
    if workspace:
        return str(Path(workspace).expanduser())
    inferred = infer_workspace_from_plugin_dir(plugin_dir or get_plugin_dir())
    if inferred:
        log(f"[service_client] AIME_WORKSPACE_PATH 为空，已从 plugin_dir 推断 workspace={inferred}")
    return inferred


def get_current_plugin_id() -> str:
    """从插件根目录 app.json 读取当前应用 id；失败返回空串，不抛异常。"""
    plugin_dir = get_plugin_dir()

    plugin_json_path = Path(plugin_dir).expanduser() / "app.json"
    try:
        with plugin_json_path.open("r", encoding="utf-8") as f:
            return str(json.load(f).get("id") or "").strip()
    except Exception as e:
        log(f"[service_client] 读取 app.json 失败: {plugin_json_path}, error={e}")
        return ""


def get_service_url(service_name: str | None = None, plugin_id: str | None = None) -> str:
    """从 routes.json 解析当前应用 service 的外部访问地址，失败返回空串。

    不传 service_name 时取该应用第一个带 url 的 service；返回值会去掉结尾斜杠。
    """
    plugin_dir = get_plugin_dir()
    resolved_plugin_id = (plugin_id or get_current_plugin_id() or "").strip()
    workspace = get_workspace_path(plugin_dir)

    if not resolved_plugin_id:
        log("[service_client] plugin_id 为空，无法解析 service url")
        return ""
    if not workspace:
        log("[service_client] AIME_WORKSPACE_PATH 为空，无法解析 routes.json")
        return ""

    runtime_path = Path(workspace).expanduser() / ".aime" / "plugin_runtime" / "routes.json"
    try:
        with runtime_path.open("r", encoding="utf-8") as f:
            plugins = json.load(f).get("plugins", [])
    except Exception as e:
        log(f"[service_client] 读取 routes.json 失败: {runtime_path}, error={e}")
        return ""

    for plugin in plugins:
        if str(plugin.get("id") or "").strip() != resolved_plugin_id:
            continue

        services = plugin.get("services", []) or []
        if service_name:
            for svc in services:
                if str(svc.get("name") or "").strip() == service_name and svc.get("url"):
                    return str(svc.get("url") or "").rstrip("/")
            log(f"[service_client] 未找到指定 service url: plugin_id={resolved_plugin_id}, service_name={service_name}")
            return ""

        for svc in services:
            if svc.get("url"):
                return str(svc.get("url") or "").rstrip("/")
        log(f"[service_client] 应用未配置可用 service url: plugin_id={resolved_plugin_id}")
        return ""

    log(f"[service_client] routes.json 中未找到应用: plugin_id={resolved_plugin_id}")
    return ""


def get_auth_headers(
    extra: dict | None = None,
    *,
    force_refresh: bool = False,
) -> dict:
    """构建调用 /api 所需的请求头，自动注入 JWT 鉴权头。"""
    headers = {"Content-Type": "application/json"}
    headers.update(extra or {})
    credential_error = None
    access_token = ""
    token_type = ""
    try:
        credential = get_cloud_credential(force_refresh=force_refresh)
        access_token = credential.access_token.strip()
        token_type = credential.token_type.strip()
    except CredentialError as exc:
        credential_error = exc

    if not access_token or not token_type:
        # Fallback for code executed by an App Skill.
        try:
            access_token = Path("/tmp/.cloud_token").read_text(encoding="utf-8").strip()
        except OSError:
            access_token = ""
        if access_token:
            token_type = "Byte-Cloud-JWT"
            log("[service_client] dynamic Cloud JWT unavailable; using legacy token file fallback")

    if not access_token or not token_type:
        if credential_error is not None:
            raise ServiceClientError(f"获取 Cloud JWT 失败：{credential_error}") from credential_error
        raise ServiceClientError("获取 Cloud JWT 失败：凭证缺少 access_token 或 token_type")
    headers["Authorization"] = f"{token_type} {access_token}"
    return headers


def _build_url(service_url: str, path: str, query: dict | None = None) -> str:
    if not path.startswith("/"):
        path = "/" + path
    url = f"{service_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
    return url


def call_service(path, method="GET", body=None, service_name=None, plugin_id=None, timeout=30, query=None) -> dict:
    """调用当前应用 service 的 /api 接口并返回 JSON dict。"""
    service_url = get_service_url(service_name=service_name, plugin_id=plugin_id)
    if not service_url:
        raise ServiceClientError("未找到应用运行时服务地址：请确认服务已启动，且 routes.json 中已生成当前应用的 service url；不要写死 localhost。")

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    url = _build_url(service_url, path, query=query)
    text = ""
    for attempt in range(2):
        force_refresh = attempt == 1
        headers = get_auth_headers(
            {"Accept-Encoding": "gzip"},
            force_refresh=force_refresh,
        )
        req = urllib.request.Request(
            url,
            data=data,
            method=method.upper(),
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = safe_read_response(resp)
            break
        except urllib.error.HTTPError as e:
            try:
                error_body = safe_read_response(e)
            except Exception:
                error_body = ""
            log(f"[service_client] HTTPError {e.code}: url={url}, body={error_body[:500]}")
            if e.code == 401 and attempt == 0:
                log("[service_client] authentication rejected; force refreshing Cloud JWT")
                continue
            if e.code in (401, 403):
                raise ServiceClientError(
                    f"鉴权失败 HTTP {e.code}：调用 /api 必须携带有效的 Cloud JWT；"
                    "Python 代码请通过 byted_aime_sdk / utils.cloud_jwt 获取，不要直读旧环境变量。"
                    f"响应：{error_body[:200]}"
                ) from e
            raise ServiceClientError(
                f"服务请求失败 HTTP {e.code}：{error_body[:300] or e.reason}"
            ) from e
        except urllib.error.URLError as e:
            log(f"[service_client] URLError: url={url}, error={e}")
            raise ServiceClientError(
                f"无法连接应用服务：{e.reason}；请确认 service url 来自 routes.json 且服务已启动。"
            ) from e
        except Exception as e:
            log(f"[service_client] 请求异常: url={url}, error={e}")
            raise ServiceClientError(f"调用应用服务失败：{e}") from e

    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        log(f"[service_client] JSON 解析失败: url={url}, body={text[:500]}")
        raise ServiceClientError(f"服务响应不是合法 JSON：{e}；响应片段：{text[:200]}") from e
    if not isinstance(parsed, dict):
        raise ServiceClientError(f"服务响应 JSON 顶层不是对象(dict)：{type(parsed).__name__}")
    return parsed


def get_json(path, **kwargs) -> dict:
    return call_service(path, method="GET", **kwargs)


def post_json(path, body=None, **kwargs) -> dict:
    return call_service(path, method="POST", body=body, **kwargs)


def put_json(path, body=None, **kwargs) -> dict:
    return call_service(path, method="PUT", body=body, **kwargs)


def delete(path, **kwargs) -> dict:
    return call_service(path, method="DELETE", **kwargs)


def notify_refresh(resource: str = "") -> None:
    """通知前端数据已变更，触发页面自动刷新。

    后端通过 WebSocket 推送 data-changed 事件给前端，前端监听后自动 re-fetch。
    前端未连接时静默忽略，不抛异常。
    """
    try:
        call_service("/api/_internal/notify-refresh", method="POST", body={"resource": resource})
    except ServiceClientError:
        pass


def list_routes(service_name: str | None = None, plugin_id: str | None = None) -> dict:
    """拉取本应用后端注册的全部业务路由清单。

    仅在 template_version >= 0.0.1 的应用中生效；老应用会命中 404。
    返回结构：
        {"template_version": "0.0.1", "routes": [{"method": "GET", "path": "/api/items", "summary": "...", ...}]}
    """
    try:
        return call_service(
            "/api/_meta/routes",
            method="GET",
            service_name=service_name,
            plugin_id=plugin_id,
        )
    except ServiceClientError as e:
        cause = e.__cause__
        if isinstance(cause, urllib.error.HTTPError) and cause.code == 404:
            raise ServiceClientError(
                "当前应用未提供 /api/_meta/routes，按 template_version=0.0.0 处理并使用老应用调用流程。"
            ) from e
        raise
