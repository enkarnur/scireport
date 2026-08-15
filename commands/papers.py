#!/usr/bin/env python3
"""面向用户的 /papers 命令：查询文献、知识库问答与报告生成。"""
import html
import importlib.util
import json
import shlex
import sys
import uuid
from pathlib import Path
from urllib.parse import quote

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))
from utils.dynamic_ui import send_app_dynamic_ui
from utils.logger import log
from utils.service_client import ServiceClientError


def load_api():
    path = PLUGIN_DIR / "skills" / "paper-vault-aime-app-cli" / "api_client.gen.py"
    spec = importlib.util.spec_from_file_location("paper_vault_api_client_gen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载生成的 API 客户端")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = load_api()


def help_text():
    return """## 文研智库命令

- `/papers help`：查看帮助
- `/papers list [关键词]`：列出或检索文献
- `/papers ask <问题>`：基于全部就绪文献与批注回答问题
- `/papers report <标题> --papers <论文ID,论文ID> [--template systematic-review|comparison|evidence-summary] [--question 研究问题]`：生成报告

提示：导入 PDF、选择问答范围和管理报告可在应用页面中完成。"""


def send_result_card(title, description, path):
    """每个结果事件仅推送一次卡片；Command 运行在主会话。"""
    config = json.loads((PLUGIN_DIR / "app.json").read_text(encoding="utf-8"))
    template = (PLUGIN_DIR / "app" / "cards" / "event-notification.html").read_text(encoding="utf-8")
    card = template.replace("{{APP_ID}}", str(config["id"]))
    card = card.replace("{{EVENT_TITLE}}", html.escape(title))
    card = card.replace("{{EVENT_DESCRIPTION}}", html.escape(description))
    card = card.replace("{{DETAIL_PATH}}", path.replace("\\", "").replace('"', ""))
    output = PLUGIN_DIR / "output" / f"papers-{uuid.uuid4().hex}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(card, encoding="utf-8")
    send_app_dynamic_ui(uri=str(output), title=title, display_mode=0)


def parse_report_args(tokens):
    title_parts, paper_ids = [], []
    template, question = "systematic-review", ""
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in {"--papers", "--template", "--question"}:
            if i + 1 >= len(tokens):
                raise ValueError(f"{token} 缺少参数")
            value = tokens[i + 1]
            if token == "--papers":
                paper_ids = [item.strip() for item in value.split(",") if item.strip()]
            elif token == "--template":
                template = value
            else:
                question = value
            i += 2
        else:
            title_parts.append(token)
            i += 1
    title = " ".join(title_parts).strip()
    if not title or not paper_ids:
        raise ValueError("请提供报告标题和 --papers <论文ID,论文ID>")
    if template not in {"systematic-review", "comparison", "evidence-summary"}:
        raise ValueError("不支持的模板")
    return title, paper_ids, template, question


def main():
    try:
        payload = json.load(sys.stdin)
        raw = payload.get("tool_input", {}).get("args", "").strip()
        tokens = shlex.split(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"❌ 命令参数无效：{exc}", file=sys.stderr)
        sys.exit(2)

    log(f"收到 /papers 命令: args={raw}", "command")
    if not tokens or tokens[0].lower() == "help":
        print(help_text())
        return

    command, rest = tokens[0].lower(), tokens[1:]
    try:
        if command == "list":
            query = [("limit", "50")]
            if rest:
                query.append(("query", " ".join(rest)))
            response = api.papers_list(query=query)
            papers = response.get("data", [])
            if not papers:
                print("文献库中没有匹配的论文。可打开文献库导入 PDF。")
                send_result_card("未找到文献", "可打开文献库导入或调整检索词。", "/library")
                return
            print(f"## 文献库（{response.get('total', len(papers))} 篇）\n")
            for paper in papers:
                authors = "、".join(paper.get("authors") or []) or "作者未知"
                print(f"- **{paper.get('title', '未命名')}**（{paper.get('year') or '年份未知'}，{authors}）`{paper.get('id')}` · {paper.get('processingStatus', 'unknown')}")
            send_result_card("文献检索完成", f"找到 {response.get('total', len(papers))} 篇文献。", "/library")

        elif command == "ask":
            question = " ".join(rest).strip()
            if not question:
                raise ValueError("用法：/papers ask <问题>")
            result = api.qa_ask_create(body={"question": question, "includeAnnotations": True}).get("data", {})
            print(f"## 回答\n\n{result.get('answer', '暂无答案')}")
            citations = result.get("citations") or []
            if citations:
                print("\n### 依据")
                for item in citations[:8]:
                    where = f"第 {item.get('pageNumber')} 页" if item.get("pageNumber") else item.get("section", "原文")
                    print(f"- {item.get('paperTitle', item.get('paperId', '论文'))} · {where}：{item.get('quote', '')}")
            send_result_card("文献库问答已完成", f"返回 {len(citations)} 条可核验引用线索。", "/ask")

        elif command == "report":
            title, paper_ids, template, question = parse_report_args(rest)
            body = {"title": title, "template": template, "paperIds": paper_ids, "language": "zh-CN"}
            if question:
                body["researchQuestion"] = question
            report = api.reports_create(body=body).get("data", {})
            report_id = str(report.get("id", ""))
            print(f"✅ 报告 **{report.get('title', title)}** 已创建，状态：`{report.get('status', 'generating')}`，ID：`{report_id}`")
            path = f"/reports/{quote(report_id, safe='')}" if report_id else "/reports"
            send_result_card("文献报告已创建", f"《{report.get('title', title)}》正在生成，可进入详情查看进度。", path)

        else:
            print(f"❌ 未知子命令：{command}\n\n{help_text()}", file=sys.stderr)
            sys.exit(2)
    except (ServiceClientError, ValueError, KeyError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
