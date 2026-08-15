"""
AIME Toolset SDK: `agent`

create and run a agent to finish you task with llm

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.agent import create_task
    result = create_task(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'agent'


def create_task(
    *,
    app_id: str,
    task_id_prefix: str,
    task_title: str,
    task_type: str,
    content: str,
    difficulty: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a sub-task to handle the user request. Returns task_id and task_uuid immediately; use task_uuid with get_task_result.

    AIME tool: `create_task`

    Args:
        app_id (str, required): the application ID that owns this task
        task_id_prefix (str, required): a prefix of the task ID, the real task ID will append a random string as suffix
        task_title (str, required): a concise, plain-text title summarizing the task
        task_type (str, required): the type of the task, can be 'subagent'
        content (str, required): the user's original message passed through verbatim
        difficulty (str, required): the difficulty level: 'low', 'medium', or 'high'
        context (str, optional): (optional) background information from the conversation that the task needs

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['app_id'] = app_id
    _params['task_id_prefix'] = task_id_prefix
    _params['task_title'] = task_title
    _params['task_type'] = task_type
    _params['content'] = content
    _params['difficulty'] = difficulty
    if context is not None:
        _params['context'] = context
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='create_task',
        parameters=_params,
        response_format="raw",
    ).data


def update_task(
    *,
    app_id: str,
    task_id: str,
    content: str,
    context: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing task with new requirements. Returns immediately; use get_task_result to poll for completion.

    AIME tool: `update_task`

    Args:
        app_id (str, required): the application ID that owns this task
        task_id (str, required): the ID of the task to update
        content (str, required): new requirements or instructions for the task
        context (str, optional): (optional) background information from the conversation that the task needs
        difficulty (str, optional): (optional) updated difficulty level: 'low', 'medium', or 'high'

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['app_id'] = app_id
    _params['task_id'] = task_id
    _params['content'] = content
    if context is not None:
        _params['context'] = context
    if difficulty is not None:
        _params['difficulty'] = difficulty
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='update_task',
        parameters=_params,
        response_format="raw",
    ).data


def get_task_result(
    *,
    app_id: str,
    task_uuid: str,
) -> Dict[str, Any]:
    """
    Get the result of a task by task_uuid. Returns status and content when the task is completed.

    AIME tool: `get_task_result`

    Args:
        app_id (str, required): the application ID that owns this task
        task_uuid (str, required): the UUID returned by create_task

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['app_id'] = app_id
    _params['task_uuid'] = task_uuid
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='get_task_result',
        parameters=_params,
        response_format="raw",
    ).data


def list_tasks() -> Dict[str, Any]:
    """
    List all tasks and their current status.

    AIME tool: `list_tasks`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='list_tasks',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'create_task',
    'update_task',
    'get_task_result',
    'list_tasks',
]
