"""
AIME Platform API SDK: `assistant`

直接调用 AIME 平台 REST API，封装助理和 Lane 相关只读查询、Lane 重命名、
子任务列表（通过 assistant_id）以及定时任务列表（通过 space_id）。

与 aime_sdk 其他模块（llm, agent 等通过 call_aime_tool）不同，
本模块直接向 AIME 平台发起 HTTP 请求，通过 ``utils.cloud_jwt`` 获取 JWT 鉴权。

    from aime_sdk.assistant import get_assistant_list, get_p2p_lane, list_sub_tasks, list_cron_tasks

    # 枚举助理列表
    resp = get_assistant_list()
    asst = resp["assistants"][0]

    # 获取私聊 lane_id
    lane = get_p2p_lane(assistant_id=asst["id"])["lane"]

    # 列出子任务
    tasks = list_sub_tasks(assistant_id=asst["id"])["sub_tasks"]

    # 列出定时任务（需先拿 space_id）
    space_id = get_assistant_info(assistant_id=asst["id"])["assistant"]["space_id"]
    crons = list_cron_tasks(page_num=1, page_size=20, space_id=space_id)["cron_tasks"]

"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional  # noqa: F401

from utils.cloud_jwt import get_cloud_credential


# ── 私有辅助函数 ──────────────────────────────────────────────────────────────

def _get_platform_url() -> str:
    url = os.environ.get("APP_PLATFORM_URL", "").strip().rstrip("/")
    if url:
        return url
    host = os.environ.get("IRIS_RUNTIME_AIME_API_HOST", "aime.bytedance.net").strip()
    return f"https://{host}"


def _get_authorization() -> str:
    credential = get_cloud_credential()
    if not credential.token_type or not credential.access_token:
        raise RuntimeError("Cloud credential is missing token_type or access_token")
    return f"{credential.token_type} {credential.access_token}"


def _call_api(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base = _get_platform_url()
    url = f"{base}{path}"
    if params:
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            url = f"{url}?{urllib.parse.urlencode(filtered, doseq=True)}"

    headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
    headers["Authorization"] = _get_authorization()

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_bytes = b""
        try:
            body_bytes = e.read()
        except Exception:
            pass
        raise RuntimeError(
            f"AIME API 请求失败 HTTP {e.code}: {path}\n{body_bytes[:400].decode('utf-8', errors='replace')}"
        ) from e


# ── 助理信息 ──────────────────────────────────────────────────────────────────

def get_assistant_list(
    *,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    keyword: Optional[str] = None,
    disable_personal_assistant_pin: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    获取当前用户的助理列表（分页）。

    AIME API: GET /api/assistant/v2/assistants/list

    Args:
        cursor (str, optional): 游标，上次返回的 next_cursor，首次请求为空
        limit (int, optional): 每页数量，默认 20
        keyword (str, optional): 搜索关键词，按助理名称过滤
        disable_personal_assistant_pin (bool, optional): 是否禁用 Personal 类型置顶，默认 false

    Returns:
        Dict: {
            "assistants": [{"id", "bot_name", "status", "space_id", "bot_app_id", ...}],
            "next_cursor": str,
            "has_more": bool
        }
    """
    return _call_api("GET", "/api/assistant/v2/assistants/list", params={
        "cursor": cursor,
        "limit": limit,
        "keyword": keyword,
        "disable_personal_assistant_pin": disable_personal_assistant_pin,
    })


def get_assistant_info(
    *,
    assistant_id: str,
) -> Dict[str, Any]:
    """
    获取单个助理的详细信息。

    AIME API: GET /api/assistant/v2/assistants/{assistant_id}

    Args:
        assistant_id (str, required): 助理 ID

    Returns:
        Dict: {
            "assistant": {
                "id", "bot_name", "bot_app_id", "bot_avatar", "bot_description",
                "status", "space_id", "space_name", "creator", ...
            }
        }
    """
    return _call_api("GET", f"/api/assistant/v2/assistants/{assistant_id}")


def get_current_user_role(
    *,
    assistant_id: str,
) -> Dict[str, Any]:
    """
    获取当前用户在指定助理中的角色。

    AIME API: GET /api/assistant/v2/assistants/permission/role

    Args:
        assistant_id (str, required): 助理 ID

    Returns:
        Dict: {"role": int}  # 0=无角色, 1=Owner, 2=Admin, 3=Member
    """
    return _call_api("GET", "/api/assistant/v2/assistants/permission/role", params={
        "assistant_id": assistant_id,
    })


def get_assistant_workspace_list(
    *,
    start_id: Optional[str] = None,
    limit: Optional[int] = None,
    keyword: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取助理 workspace 列表（含 space_id 等信息，分页）。

    AIME API: GET /api/assistant/v2/assistants/workspace/list

    Args:
        start_id (str, optional): 游标，上一页最后一条的 id
        limit (int, optional): 每页数量，默认 20
        keyword (str, optional): 搜索关键词

    Returns:
        Dict: {
            "assistants": [...],
            "has_more": bool,
            "next_id": str
        }
    """
    return _call_api("GET", "/api/assistant/v2/assistants/workspace/list", params={
        "start_id": start_id,
        "limit": limit,
        "keyword": keyword,
    })


# ── Lane 查询 ─────────────────────────────────────────────────────────────────

def get_p2p_lane(
    *,
    assistant_id: str,
) -> Dict[str, Any]:
    """
    获取当前用户与指定助理的 P2P（私聊）Lane。
    这是获取 lane_id 最常用的方式。

    AIME API: GET /api/assistant/v2/assistants/{assistant_id}/p2p_lane

    Args:
        assistant_id (str, required): 助理 ID

    Returns:
        Dict: {
            "lane": {
                "lane_id": str,
                "lane_type": str,
                "name": str,
                "unread_message_count": int,
                "last_message_at": int
            }
        }
    """
    return _call_api("GET", f"/api/assistant/v2/assistants/{assistant_id}/p2p_lane")


def list_non_group_lanes(
    *,
    assistant_id: Optional[str] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    列出当前用户的私聊 Lane 列表（分页）。

    AIME API: GET /api/assistant/v2/lane/non_group_lanes

    Args:
        assistant_id (str, optional): 助理 ID，不传则查当前用户所有私聊 Lane
        limit (int, optional): 每页数量
        cursor (str, optional): 游标，上一页最后一条的 id

    Returns:
        Dict: {
            "lanes": [{"lane_id", "lane_type", "name", "unread_message_count", "last_message_at", ...}],
            "has_more": bool,
            "next_cursor": str
        }
    """
    return _call_api("GET", "/api/assistant/v2/lane/non_group_lanes", params={
        "assistant_id": assistant_id,
        "limit": limit,
        "cursor": cursor,
    })


def list_group_lanes(
    *,
    assistant_id: Optional[str] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """
    列出群聊 Lane 列表（分页）。

    AIME API: GET /api/assistant/v2/lane/group_lanes

    Args:
        assistant_id (str, optional): 助理 ID
        limit (int, optional): 每页数量
        cursor (str, optional): 游标，上一页最后一条的 id
        search (str, optional): 按群聊名称模糊搜索

    Returns:
        Dict: {
            "lanes": [{"lane_id", "lane_type", "name", "lark_group_url", "last_message_at", ...}],
            "has_more": bool,
            "next_cursor": str
        }
    """
    return _call_api("GET", "/api/assistant/v2/lane/group_lanes", params={
        "assistant_id": assistant_id,
        "limit": limit,
        "cursor": cursor,
        "search": search,
    })


def get_lane_config(
    *,
    assistant_id: str,
    lane_id: str,
) -> Dict[str, Any]:
    """
    获取指定 Lane 的配置项列表。

    AIME API: GET /api/assistant/v2/lane/config

    Args:
        assistant_id (str, required): 助理 ID
        lane_id (str, required): Lane ID

    Returns:
        Dict: {
            "configs": [{"file_name": str, "enabled": bool, "modifiable": bool, "tooltip": str}]
        }
    """
    return _call_api("GET", "/api/assistant/v2/lane/config", params={
        "assistant_id": assistant_id,
        "lane_id": lane_id,
    })


def get_top_unread_lanes(
    *,
    count: int,
) -> Dict[str, Any]:
    """
    获取未读消息数最多的 Lane 列表。

    AIME API: GET /api/assistant/v2/lane/top_unread_lanes

    Args:
        count (int, required): 返回条数

    Returns:
        Dict: {
            "lanes": [{
                "assistant_id": str,
                "lane_id": str,
                "lane_type": str,
                "name": str,
                "unread_message_count": int,
                "assistant_name": str
            }]
        }
    """
    return _call_api("GET", "/api/assistant/v2/lane/top_unread_lanes", params={
        "count": count,
    })


# ── Lane 写操作 ───────────────────────────────────────────────────────────────

def update_lane_name(
    *,
    assistant_id: str,
    lane_id: str,
    name: str,
) -> Dict[str, Any]:
    """
    重命名 Lane（私聊或群聊均可）。

    AIME API: POST /api/assistant/v2/lane/update_name

    Args:
        assistant_id (str, required): 助理 ID
        lane_id (str, required): Lane ID
        name (str, required): 新名称

    Returns:
        Dict: {} （空对象，成功即可）
    """
    return _call_api("POST", "/api/assistant/v2/lane/update_name", body={
        "assistant_id": assistant_id,
        "lane_id": lane_id,
        "name": name,
    })


# ── 子任务 ────────────────────────────────────────────────────────────────────

def list_sub_tasks(
    *,
    assistant_id: str,
    lane_id: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: Optional[int] = None,
    next_id: Optional[str] = None,
    status_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    列出助理下的子任务列表（分页），支持 lane_id 过滤、状态过滤、关键词搜索。

    AIME API: GET /api/assistant/v2/sub_tasks

    Args:
        assistant_id (str, required): 助理 ID，必传
        lane_id (str, optional): 泳道 ID，不传则查该助理下所有任务
        keyword (str, optional): 标题关键词，全文检索
        limit (int, optional): 每页数量，默认 20
        next_id (str, optional): 游标分页（上一页最后一条的 updated_at 时间戳，毫秒）
        status_list (list, optional): 按子任务状态过滤，如 ["running", "completed"]

    Returns:
        Dict: {
            "sub_tasks": [{
                "id": str,           # 对外唯一标识
                "name": str,
                "status": str,       # running / completed / failed / canceled 等
                "latest_action_summary": str,
                "created_at": int,
                "updated_at": int,
                "lane_id": str,
                "task_id": str,
                "external_link": str
            }],
            "has_more": bool,
            "next_id": str
        }
    """
    params: Dict[str, Any] = {
        "assistant_id": assistant_id,
        "lane_id": lane_id,
        "keyword": keyword,
        "limit": limit,
        "next_id": next_id,
    }
    if status_list is not None:
        params["status_list"] = status_list
    return _call_api("GET", "/api/assistant/v2/sub_tasks", params=params)


def get_sub_tasks_by_lane(
    *,
    assistant_id: str,
    lane_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取指定助理（+可选 lane）下当前活跃子任务的快照（轻量版，不分页）。

    AIME API: GET /api/assistant/v2/assistants/{assistant_id}/sub_tasks

    Args:
        assistant_id (str, required): 助理 ID
        lane_id (str, optional): 泳道 ID，不传则查所有

    Returns:
        Dict: {
            "sub_tasks": [{"id", "name", "status", "latest_action_summary", ...}]
        }
    """
    return _call_api(
        "GET",
        f"/api/assistant/v2/assistants/{assistant_id}/sub_tasks",
        params={"lane_id": lane_id},
    )


# ── 定时任务 ──────────────────────────────────────────────────────────────────

def list_cron_tasks(
    *,
    page_num: int,
    page_size: int,
    query: Optional[str] = None,
    space_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    列出定时任务列表（分页）。

    AIME API: GET /api/agents/v2/cron/task/list

    注意：定时任务通过 space_id 关联助理，space_id 来自
    get_assistant_info(assistant_id=...)["assistant"]["space_id"]。

    Args:
        page_num (int, required): 页码，从 1 开始
        page_size (int, required): 每页数量
        query (str, optional): 搜索关键词，按任务名称过滤
        space_id (str, optional): 助理空间 ID，不传则查当前用户所有定时任务

    Returns:
        Dict: {
            "cron_tasks": [{
                "uid": str,
                "name": str,
                "description": str,
                "schedule": str,          # 运行时间，格式：2023-12-25 12:00:00
                "schedule_type": int,     # 1=每日, 2=每周
                "task_status": int,       # 1=Running, 2=Stopped
                "last_run_status": int,   # 1=Success, 2=Failed, 3=Exception
                "last_run_err_msg": str,
                "timezone": str,
                "created_at": str,
                "updated_at": str
            }],
            "total": int
        }
    """
    return _call_api("GET", "/api/agents/v2/cron/task/list", params={
        "page_num": page_num,
        "page_size": page_size,
        "query": query,
        "space_id": space_id,
    })


def get_cron_task(
    *,
    uid: str,
    space_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取单个定时任务详情。

    AIME API: GET /api/agents/v2/cron/task/{uid}

    Args:
        uid (str, required): 定时任务 UID
        space_id (str, optional): 助理空间 ID

    Returns:
        Dict: {"cron_task": {...}}  # 完整的 CronTask 对象
    """
    return _call_api("GET", f"/api/agents/v2/cron/task/{uid}", params={
        "space_id": space_id,
    })


def list_cron_task_logs(
    *,
    uid: str,
    page_num: int,
    page_size: int,
    space_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    查看某定时任务的历史执行日志（分页）。

    AIME API: GET /api/agents/v2/cron/task/log/{uid}

    Args:
        uid (str, required): 定时任务 UID
        page_num (int, required): 页码，从 1 开始
        page_size (int, required): 每页数量
        space_id (str, optional): 助理空间 ID

    Returns:
        Dict: {
            "task_execution": [{
                "task_uid": str,
                "task_name": str,
                "execute_time": str,
                "run_status": int,
                "error_message": str,
                "session_id": str,
                "trigger_type": int,
                "execution_duration": float,
                "created_at": str
            }],
            "total": int,
            "enable_view": bool
        }
    """
    return _call_api("GET", f"/api/agents/v2/cron/task/log/{uid}", params={
        "page_num": page_num,
        "page_size": page_size,
        "space_id": space_id,
    })


__all__ = [
    # 助理信息
    "get_assistant_list",
    "get_assistant_info",
    "get_current_user_role",
    "get_assistant_workspace_list",
    # Lane 查询
    "get_p2p_lane",
    "list_non_group_lanes",
    "list_group_lanes",
    "get_lane_config",
    "get_top_unread_lanes",
    # Lane 写操作
    "update_lane_name",
    # 子任务
    "list_sub_tasks",
    "get_sub_tasks_by_lane",
    # 定时任务
    "list_cron_tasks",
    "get_cron_task",
    "list_cron_task_logs",
]
