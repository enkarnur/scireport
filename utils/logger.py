"""AIME AIApp 日志工具 — 供 commands、hooks、server 共用"""
import os
import datetime
import tempfile
from pathlib import Path


def _resolve_log_dir():
    runtime_dir = os.environ.get("AIME_PLUGIN_RUNTIME_DIR", "").strip()
    if runtime_dir:
        return Path(runtime_dir).expanduser() / "logs"

    workspace = os.environ.get("AIME_WORKSPACE_PATH", "").strip()
    plugin_dir = os.environ.get("AIME_PLUGIN_DIR", "").strip()
    if workspace and plugin_dir:
        install_id = Path(plugin_dir).name
        return Path(workspace).expanduser() / ".aime" / "plugin_runtime" / install_id / "logs"

    # 本地直接运行 CLI/测试时不要污染当前源码目录；没有运行时目录时写入系统临时目录。
    return Path(tempfile.gettempdir()) / "aime-plugin-logs"


def get_log_file(name="plugin"):
    """获取日志文件路径，自动创建目录"""
    log_dir = _resolve_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / f"{name}.log")


def log(msg, name="plugin"):
    """写日志到文件（静默失败）"""
    try:
        log_path = get_log_file(name)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass
