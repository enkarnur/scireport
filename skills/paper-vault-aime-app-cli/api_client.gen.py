# CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
"""command / hook 调用本应用后端接口的 typed 封装（基于 utils.service_client）。

写操作（POST/PUT/PATCH/DELETE）成功后自动调用 notify_refresh，
通知已打开的前端页面刷新数据。前端自己调用 API 时不经过此层，不会触发多余刷新。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from utils.service_client import call_service, notify_refresh  # noqa: E402

def items_list(query=None) -> dict:
    """GET /api/items — 列出所有项目"""
    return call_service("/api/items", method="GET", query=query)


def items_create(body=None, query=None) -> dict:
    """POST /api/items — 创建项目"""
    result = call_service("/api/items", method="POST", body=body, query=query)
    notify_refresh("items")
    return result


def items_by_id_delete(id, query=None) -> dict:
    """DELETE /api/items/{id} — 删除项目"""
    result = call_service(f"/api/items/{id}", method="DELETE", query=query)
    notify_refresh("items")
    return result


def items_by_id_get(id, query=None) -> dict:
    """GET /api/items/{id} — 获取单个项目"""
    return call_service(f"/api/items/{id}", method="GET", query=query)


def items_by_id_update(id, body=None, query=None) -> dict:
    """PUT /api/items/{id} — 更新项目（字段可选）"""
    result = call_service(f"/api/items/{id}", method="PUT", body=body, query=query)
    notify_refresh("items")
    return result

