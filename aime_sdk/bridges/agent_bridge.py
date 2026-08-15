#!/usr/bin/env python3
"""Go→Python Agent 子任务桥接脚本。

Go 后端通过 callPython("aime_sdk/bridges/agent_bridge.py", input, timeout) 调用本脚本。

输入（stdin JSON）：
  action=create:
    {"action": "create", "content": str, "title": str?, "difficulty": str?, "context": str?,
     "task_id_prefix": str?, "task_type": str?}
  action=result:
    {"action": "result", "task_uuid": str}

输出（stdout JSON）：
  成功(create): {"task_id": "...", "task_uuid": "...", "_raw": {...}}
  成功(result): {"status": "...", "content": "...", "_raw": {...}}
  失败: {"error": "错误描述", "error_type": "AgentResponseError|异常类名"}

错误时 exit code = 0，通过 stdout JSON 的 "error" 字段传达。
"""
import json
import sys
import traceback
from pathlib import Path

sdk_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(sdk_root))

from aime_sdk.agent import create_task, get_task_result  # noqa: E402
from utils.dynamic_ui import get_source_app_id  # noqa: E402


def do_create(payload: dict, app_id: str) -> dict:
    content = (payload.get("content") or "").strip()
    if not content:
        return {"error": "content is required", "error_type": "ValidationError"}

    resp = create_task(
        app_id=app_id,
        task_id_prefix=(payload.get("task_id_prefix") or "app_task").strip(),
        task_title=(payload.get("title") or "Agent 子任务").strip(),
        task_type=(payload.get("task_type") or "subagent").strip(),
        content=content,
        difficulty=(payload.get("difficulty") or "low").strip(),
        context=payload.get("context") or None,
    )

    if isinstance(resp, dict) and resp.get("error"):
        sys.stderr.write(f"[agent_bridge] create_task returned error: {resp['error']}\n")
        return {"error": str(resp["error"]), "error_type": "AgentResponseError", "_raw": resp}

    return {
        "task_id": resp.get("task_id") or resp.get("taskId") or "",
        "task_uuid": resp.get("task_uuid") or resp.get("taskUuid") or "",
        "_raw": resp,
    }


def do_result(payload: dict, app_id: str) -> dict:
    task_uuid = (payload.get("task_uuid") or "").strip()
    if not task_uuid:
        return {"error": "task_uuid is required", "error_type": "ValidationError"}

    resp = get_task_result(app_id=app_id, task_uuid=task_uuid)

    if isinstance(resp, dict) and resp.get("error") and not resp.get("status"):
        sys.stderr.write(f"[agent_bridge] get_task_result returned error: {resp['error']}\n")
        return {"error": str(resp["error"]), "error_type": "AgentResponseError", "_raw": resp}

    return {
        "status": resp.get("status", "unknown"),
        "content": resp.get("content", ""),
        "_raw": resp,
    }


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "empty input", "error_type": "ValidationError"}))
        return

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}", "error_type": "ValidationError"}))
        return

    app_id = get_source_app_id()
    action = (payload.get("action") or "").strip()

    try:
        if action == "create":
            out = do_create(payload, app_id)
        elif action == "result":
            out = do_result(payload, app_id)
        else:
            out = {"error": f"unknown action: {action}", "error_type": "ValidationError"}
    except Exception as exc:
        tb = traceback.format_exc()
        sys.stderr.write(f"[agent_bridge] {action} failed: {exc}\n{tb}\n")
        out = {
            "error": f"agent bridge failed: {exc}",
            "error_type": type(exc).__name__,
            "traceback": tb,
        }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
