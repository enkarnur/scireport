---
name: paper-vault-aime-app-cli
description: 管理与研析文献库。当用户需要查询论文、回答文献问题、检索或定位批注、生成和查看文献报告时使用。
---

# 文研智库 Agent 操作指南

通过 CLI 调用文研智库 Service。CLI 自动处理服务寻址、鉴权和写操作后的页面刷新；禁止使用 curl、裸 fetch、localhost 或页面点击替代业务 API。

## 标准工作流

1. 先读 `references/api-routes.index.json` 定位接口。
2. 需要确认参数时，在 `references/api-routes.details.json` 查看对应 `METHOD PATH`。
3. 执行通用 CLI：

```bash
python3 skills/paper-vault-aime-app-cli/cli.py api call <METHOD> <PATH> [--body '<JSON对象>'] [--query 'k=v&k2=v2']
```

CLI 输出始终为 JSON。路径中的 `{paperId}`、`{annotationId}`、`{reportId}` 必须替换为真实 ID。

## 代表性操作

```bash
# 检索文献库
python3 skills/paper-vault-aime-app-cli/cli.py api call GET /api/papers --query 'query=检索增强&limit=20'

# 获取单篇论文的结构化研析与页级文本
python3 skills/paper-vault-aime-app-cli/cli.py api call GET /api/papers/<paperId>

# 基于全部就绪论文和批注回答问题
python3 skills/paper-vault-aime-app-cli/cli.py api call POST /api/qa/ask --body '{"question":"这些论文的主要方法是什么？","includeAnnotations":true}'

# 检索并定位批注
python3 skills/paper-vault-aime-app-cli/cli.py api call GET /api/annotations --query 'keyword=基线&paperId=<paperId>'

# 生成系统综述报告
python3 skills/paper-vault-aime-app-cli/cli.py api call POST /api/reports --body '{"title":"研究综述","template":"systematic-review","paperIds":["<paperId>"],"researchQuestion":"核心研究问题","language":"zh-CN"}'

# 查看报告详情与引用线索
python3 skills/paper-vault-aime-app-cli/cli.py api call GET /api/reports/<reportId>
```

## 回答与定位要求

- 问答优先调用 `POST /api/qa/ask`，保留并向用户展示返回的 `citations`，不要编造论文结论或页码。
- 定位批注时展示论文标题、页码、章节和 quote；需要完整上下文时再读取论文详情。
- 报告生成后返回报告 ID 和状态；可引导用户打开 `/reports/<reportId>`。论文详情使用 `/papers/<paperId>`，文献库与问答入口分别为 `/library`、`/ask`。
- 创建、更新、删除、问答和报告生成必须经生成客户端/通用 CLI；其写操作会自动 `notify_refresh`，不要重复通知。
- PDF 原文件只在用户浏览器本地处理；不要索取、保存或输出 GitHub Token 或任何凭据。

## Page Control 边界

只有用户明确要求操控已打开的前端页面时，才可使用 `python3 skills/paper-vault-aime-app-cli/cli.py page ...`。日常查询和数据变更一律使用 `api call`，开发、调试或验证阶段不得调用 Page Control。
