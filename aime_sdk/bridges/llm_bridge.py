#!/usr/bin/env python3
"""Go→Python LLM 桥接脚本。

Go 后端通过 callPython("aime_sdk/bridges/llm_bridge.py", input, timeout) 调用本脚本。
输入（stdin JSON）：
  {
    "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
    "model": "gemini-3.5-flash-native",   // 可选
    "temperature": 0.3,                    // 可选
    "max_tokens": 512                      // 可选
  }

输出（stdout JSON）：
  成功: {"content": "模型回复文本", "finish_reason": "STOP", "usage": {...}}
  失败: {"error": "错误描述", "error_type": "LLMResponseError|异常类名", "raw": {...}}

错误时 exit code = 0，通过 stdout JSON 的 "error" 字段传达（Go 侧统一检查该字段）。
"""
import json
import sys
import traceback
from pathlib import Path

sdk_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(sdk_root))

from aime_sdk.llm import llm_call  # noqa: E402
from utils.dynamic_ui import get_source_app_id  # noqa: E402


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "empty input", "error_type": "ValidationError"}))
        return

    try:
        params = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}", "error_type": "ValidationError"}))
        return

    messages = params.get("messages")
    if not messages:
        print(json.dumps({"error": "messages is required", "error_type": "ValidationError"}))
        return

    kwargs = {"app_id": get_source_app_id(), "messages": messages}
    if params.get("model"):
        kwargs["model"] = params["model"]
    if params.get("temperature") is not None:
        kwargs["temperature"] = params["temperature"]
    if params.get("max_tokens") is not None:
        kwargs["max_tokens"] = params["max_tokens"]

    try:
        result = llm_call(**kwargs)
    except Exception as e:
        tb = traceback.format_exc()
        sys.stderr.write(f"[llm_bridge] llm_call failed: {e}\n{tb}\n")
        print(json.dumps({
            "error": f"llm_call failed: {e}",
            "error_type": type(e).__name__,
            "traceback": tb,
        }, ensure_ascii=False))
        return

    if isinstance(result, str):
        result = {"content": result}

    # 配额超限、限流等业务错误不会抛异常，而是塞在返回体的 error 字段里
    if isinstance(result, dict) and result.get("error"):
        sys.stderr.write(f"[llm_bridge] llm_call returned error: {result['error']}\n")
        print(json.dumps({
            "error": str(result["error"]),
            "error_type": "LLMResponseError",
            "raw": result,
        }, ensure_ascii=False))
        return

    print(json.dumps({
        "content": result.get("content", ""),
        "finish_reason": result.get("finish_reason"),
        "usage": result.get("usage"),
        "raw": result,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
