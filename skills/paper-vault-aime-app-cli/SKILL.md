---
name: paper-vault-aime-app-cli
description: 当 Agent 需要查看、调用或操作 「文研智库」 / 「Paper Vault」 / 「paper-vault」 这个 AIME 应用（app_id=app_cb75e3e2f3cf3421）的数据、后端接口或前端页面时使用；后端 API 操作不依赖页面连接，前端页面操作需要 page-control WebSocket 已连接
---

# 示例应用 Skill

通过 CLI 操作本应用的后端 API 和前端页面。CLI 内部自动处理服务寻址与鉴权，不要手写 curl/fetch/localhost。

## 后端 API

```bash
# 1. 查看全部接口（含参数、示例）
python3 cli.py api routes

# 2. 查看单个接口详情
python3 cli.py api routes "POST /api/items"

# 3. 调用接口
python3 cli.py api call GET  /api/items
python3 cli.py api call POST /api/items --body '{"title":"新任务"}'
python3 cli.py api call PUT  /api/items/1 --body '{"status":"done"}'
python3 cli.py api call DELETE /api/items/1
python3 cli.py api call GET  /api/items --query 'limit=10&status=done'
```

`call` 是 `api call` 的顶层快捷别名：`cli.py call POST /api/items --body '{...}'`。

路径参数：把 `{id}` 替换为真实值，例如 `/api/items/{id}` → `/api/items/1`。

接口变更时：改 `app/api/api.yaml` → 跑 `python3 tools/gen_api.py <plugin-dir>` 刷新生成产物。不要手动扩展 CLI。

## 前端 Page Control
禁止在开发过程中如：功能迭代优化/bugfix等场景下使用。

> **门禁（BLOCKING）**：除非用户明确要求使用控制应用前端页面，否则不得调用任何 `page` 命令。不要为了探测能力、展示控制条或验证开发结果而自行启用。

用户明确授权后的标准流程：

```bash
python3 cli.py page wait --timeout 3
python3 cli.py page control-start --zh "正在操作页面" --en "Operating"
python3 cli.py page describe          # 查看可用 action
python3 cli.py page state             # 页面状态快照
python3 cli.py page action dom.click --args '{"selector":"[data-testid=\"save-button\"]"}'
python3 cli.py page action nav.refresh
python3 cli.py page control-end
```

- `page wait` 超时说明用户未打开页面，提示其在 AIME 中打开/刷新应用。
- `page state` 和 `page describe` 分开执行，不要用 `&&` 合并。
- 数据变更走 `api call`，不要通过点击页面按钮间接调接口。
- `nav.refresh` 是软刷新（不断开 WebSocket），业务页需接入 `usePageControlRefresh` 才会更新数据。

## 约束

- 创建/更新/删除数据优先 `api call`，不通过页面按钮间接操作。
- 该 skill 仅供 Agent 操作应用数据/页面，禁止在功能开发/bugfix 场景中使用。
- 定位元素优先用稳定 `[data-testid="..."]`，不依赖 className 或 DOM 层级。
- `/api/items` 只是脚手架演示，真实业务应替换 `app/api/api.yaml` 后重新生成。
