#!/usr/bin/env python3
"""Command 示例 — 实现 /example 斜杠命令。

协议：stdin 接收 JSON（含 tool_input.args），stdout 输出 Markdown 文本。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.logger import log
from utils.service_client import call_service, notify_refresh


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(f"读取命令输入失败: {e}", file=sys.stderr)
        sys.exit(1)

    args_str = payload.get("tool_input", {}).get("args", "").strip()
    args = args_str.split() if args_str else []
    log(f"收到命令: args={args_str}", "command")

    if not args:
        print("用法: /example <子命令> [参数]")
        print()
        print("子命令:")
        print("  list          - 列出所有项目")
        print("  add <标题>    - 添加新项目")
        print("  done <id>     - 标记项目完成")
        print("  rm <id>       - 删除项目")
        return

    cmd = args[0]

    if cmd == "list":
        resp = call_service("/api/items")
        items = resp.get("data", [])
        if not items:
            print("当前没有项目。")
            return
        print("项目列表:")
        for row in items:
            print(f"- [{row.get('id')}] {row.get('title')} ({row.get('status')})")

    elif cmd == "add":
        if len(args) < 2:
            print("用法: /example add <标题>", file=sys.stderr)
            sys.exit(1)
        title = " ".join(args[1:])
        resp = call_service("/api/items", method="POST", body={"title": title, "status": "todo"})
        row = resp.get("data", {})
        notify_refresh("items")
        print(f"已创建项目：[{row.get('id')}] {row.get('title')}")

    elif cmd == "done":
        if len(args) != 2:
            print("用法: /example done <id>", file=sys.stderr)
            sys.exit(1)
        resp = call_service(f"/api/items/{args[1]}", method="PUT", body={"status": "done"})
        row = resp.get("data", {})
        notify_refresh("items")
        print(f"已完成项目：[{row.get('id')}] {row.get('title')}")

    elif cmd == "rm":
        if len(args) != 2:
            print("用法: /example rm <id>", file=sys.stderr)
            sys.exit(1)
        call_service(f"/api/items/{args[1]}", method="DELETE")
        notify_refresh("items")
        print(f"已删除项目：{args[1]}")

    else:
        print(f"未知子命令: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
