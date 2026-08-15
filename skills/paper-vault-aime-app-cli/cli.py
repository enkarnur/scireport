#!/usr/bin/env python3
"""AIME App CLI — Agent 调用当前应用后端 API 与前端 page-control 的统一入口。"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qsl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from utils.service_client import ServiceClientError, call_service, notify_refresh


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def parse_json_object(raw: str, flag: str):
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{flag} 不是合法 JSON: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(parsed, dict):
        print(f"{flag} 必须是 JSON 对象", file=sys.stderr)
        sys.exit(2)
    return parsed


def parse_query(raw: str):
    return parse_qsl(raw, keep_blank_values=True) if raw else None


# ---- API group ---------------------------------------------------------

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PREFIXES = ("/api/_internal/", "/api/_meta/", "/api/page-control/", "/api/aime/", "/ws/")


def infer_resource(path: str) -> str:
    """从 API 路径推导资源名，如 /api/notes/123 → notes。"""
    for prefix in SKIP_PREFIXES:
        if path.startswith(prefix):
            return ""
    parts = [s for s in path.split("/") if s and s not in ("api",)]
    # 跳过路径参数片段（纯数字或 UUID 形态）
    return parts[0] if parts else ""


def cmd_api_call(args):
    method = args.method.upper()
    if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
        print(f"不支持的 method: {method}", file=sys.stderr)
        sys.exit(2)
    body = parse_json_object(args.body, "--body") if args.body else None
    resp = call_service(args.path, method=method, body=body, query=parse_query(args.query), timeout=args.timeout)
    if method in WRITE_METHODS:
        resource = infer_resource(args.path)
        if resource:
            notify_refresh(resource)
    print_json(resp)


def cmd_api_routes(args):
    """输出当前应用的全部业务接口。无参数时输出精简列表；指定 METHOD PATH 时输出该接口完整详情。"""
    details_path = Path(__file__).resolve().parent / "references" / "api-routes.details.json"
    if not details_path.exists():
        print_json({"ok": False, "error": "api-routes.details.json 不存在，请先运行 tools/gen_api.py 生成"})
        sys.exit(1)

    with details_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    routes_by_key = data.get("routes_by_key", {})

    if args.route_key:
        parts = args.route_key.strip().split(None, 1)
        if len(parts) != 2:
            print_json({"ok": False, "error": "格式应为 'METHOD PATH'，例如 'POST /api/items'"})
            sys.exit(2)
        key = f"{parts[0].upper()} {parts[1]}"
        if key not in routes_by_key:
            candidates = [k for k in routes_by_key if key in k]
            print_json({"ok": False, "error": f"未找到 '{args.route_key}'", "available": candidates or list(routes_by_key.keys())})
            sys.exit(1)
        print_json(routes_by_key[key])
    else:
        compact = []
        for key, route in routes_by_key.items():
            entry = {"method": route["method"], "path": route["path"], "summary": route.get("summary", "")}
            if route.get("body_params"):
                entry["body_params"] = route["body_params"]
            if route.get("query_params"):
                entry["query_params"] = route["query_params"]
            if route.get("request_example"):
                entry["request_example"] = route["request_example"]
            compact.append(entry)
        print_json({"route_count": len(compact), "routes": compact})


# ---- page-control group ------------------------------------------------


def page_call(path, method="GET", body=None, query=None, timeout=30):
    return call_service(path, method=method, body=body, query=query, timeout=timeout)


def cmd_page_sessions(_args):
    print_json(page_call("/api/page-control/sessions"))


def cmd_page_wait(args):
    print_json(page_call("/api/page-control/wait", query=[("timeout", str(args.timeout))], timeout=float(args.timeout) + 10))


def cmd_page_describe(_args):
    print_json(page_call("/api/page-control/describe", method="POST", body={}, timeout=15))


def cmd_page_state(_args):
    print_json(page_call("/api/page-control/state", method="POST", body={}, timeout=15))


def cmd_page_action(args):
    action_args = parse_json_object(args.args, "--args") if args.args else None
    payload = {"action": args.name, "timeout": args.timeout}
    if action_args is not None:
        payload["args"] = action_args
    print_json(page_call("/api/page-control/action", method="POST", body=payload, timeout=float(args.timeout) + 10))


def cmd_page_control_start(args):
    display = None
    if args.zh or args.en:
        display = {"zh": args.zh or "正在操作应用", "en": args.en or "Operating app"}
    payload = {"action": "__control_start__", "timeout": 10}
    if display:
        payload["args"] = {"display": display}
    print_json(page_call("/api/page-control/action", method="POST", body=payload, timeout=20))


def cmd_page_control_end(_args):
    print_json(page_call("/api/page-control/action", method="POST", body={"action": "__control_end__", "timeout": 10}, timeout=20))


# ---- subcommand registration -------------------------------------------


def add_api_subcommands(sub):
    p_api = sub.add_parser("api", help="后端 API 操作")
    api_sub = p_api.add_subparsers(dest="api_command", required=True)

    p_routes = api_sub.add_parser("routes", help="查看全部业务接口（含参数和示例）")
    p_routes.add_argument("route_key", nargs="?", default="", help="可选，指定 'METHOD PATH' 查看单个接口详情，如 'POST /api/items'")
    p_routes.set_defaults(func=cmd_api_routes)

    p_call = api_sub.add_parser("call", help="调用接口：METHOD PATH [--body] [--query]")
    p_call.add_argument("method", help="GET/POST/PUT/DELETE/PATCH")
    p_call.add_argument("path", help="接口路径，如 /api/items")
    p_call.add_argument("--body", default="", help="JSON 对象，用于 POST/PUT/PATCH")
    p_call.add_argument("--query", default="", help="查询串，如 limit=10&status=done")
    p_call.add_argument("--timeout", type=float, default=30, help="超时秒数（默认 30）")
    p_call.set_defaults(func=cmd_api_call)


def add_page_subcommands(sub):
    p_page = sub.add_parser("page", help="前端页面控制（需用户明确授权）")
    page_sub = p_page.add_subparsers(dest="page_command", required=True)

    page_sub.add_parser("sessions", help="列出在线 session").set_defaults(func=cmd_page_sessions)

    p_wait = page_sub.add_parser("wait", help="等待页面连接就绪")
    p_wait.add_argument("--timeout", type=int, default=3, help="秒（默认 3）")
    p_wait.set_defaults(func=cmd_page_wait)

    page_sub.add_parser("describe", help="列出页面支持的 action").set_defaults(func=cmd_page_describe)
    page_sub.add_parser("state", help="读取页面状态快照").set_defaults(func=cmd_page_state)

    p_start = page_sub.add_parser("control-start", help="显示控制状态条")
    p_start.add_argument("--zh", default="", help="中文文案")
    p_start.add_argument("--en", default="", help="英文文案")
    p_start.set_defaults(func=cmd_page_control_start)

    page_sub.add_parser("control-end", help="收起控制状态条").set_defaults(func=cmd_page_control_end)

    p_action = page_sub.add_parser("action", help="派发 action")
    p_action.add_argument("name", help="如 nav.goto / nav.refresh / dom.click")
    p_action.add_argument("--args", default="", help='JSON 参数，如 \'{"selector":"[data-testid=save]"}\'')
    p_action.add_argument("--timeout", type=int, default=15, help="秒（默认 15）")
    p_action.set_defaults(func=cmd_page_action)


def main():
    parser = argparse.ArgumentParser(description="AIME App CLI")
    sub = parser.add_subparsers(dest="command")

    add_api_subcommands(sub)
    add_page_subcommands(sub)

    # 顶层 call 快捷别名
    p_call = sub.add_parser("call", help="api call 的快捷别名")
    p_call.add_argument("method")
    p_call.add_argument("path")
    p_call.add_argument("--body", default="")
    p_call.add_argument("--query", default="")
    p_call.add_argument("--timeout", type=float, default=30)
    p_call.set_defaults(func=cmd_api_call)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    try:
        args.func(args)
    except ServiceClientError as exc:
        print_json({"ok": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
