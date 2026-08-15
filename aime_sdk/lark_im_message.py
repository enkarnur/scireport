"""
AIME Toolset SDK: `lark_im_message`

lark im message toolset

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_im_message import lark_im_send_message
    result = lark_im_send_message(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_im_message'


def lark_im_send_message(
    *,
    receive_id: str,
    receive_id_type: str,
    msg_type: str,
    content: str,
) -> Dict[str, Any]:
    """
    Send various types of Lark messages (text, post, interactive, image, file, share_chat, etc.) to specified user or group chat.

    AIME tool: `lark_im_send_message`

    Args:
        receive_id (str, required): Required, receiver ID, can be email, chat_id, open_id, user_id, or union_id
        receive_id_type (str, required): Optional, receiver ID type, optional values: 'email', 'chat_id', 'open_id', 'user_id', 'union_id', default is 'email'
        msg_type (str, required): Required, message type: 'text', 'post', 'interactive', 'image', 'file', 'audio', 'media', 'sticker', 'system', 'share_chat'
        content (str, required): Required, message content in JSON string format (escaped)

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['receive_id'] = receive_id
    _params['receive_id_type'] = receive_id_type
    _params['msg_type'] = msg_type
    _params['content'] = content
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_send_message',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_upload_resource(
    *,
    file_path: str,
    resource_type: str,
) -> Dict[str, Any]:
    """
    Upload an image or file to Lark IM and return the resource key.

    AIME tool: `lark_im_upload_resource`

    Args:
        file_path (str, required): Required, absolute path to the file
        resource_type (str, required): Required, resource type: 'image' or 'file'

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['file_path'] = file_path
    _params['resource_type'] = resource_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_upload_resource',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_create_card(
    *,
    card_json: str,
) -> Dict[str, Any]:
    """
    Create a Lark card entity and return the card_id. Must be called before sending interactive card messages.

    AIME tool: `lark_im_create_card`

    Args:
        card_json (str, required): Required, card content in JSON string format (schema 2.0)

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['card_json'] = card_json
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_create_card',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_download_resource(
    *,
    message_id: str,
    file_key: str,
    type: str,
) -> Dict[str, Any]:
    """
    Download a Lark IM message resource to the workspace. Files are downloaded by Range chunks with the current user's access token.

    AIME tool: `lark_im_download_resource`

    Args:
        message_id (str, required): Required, message ID containing the resource, such as om_xxx
        file_key (str, required): Required, message resource key, such as img_xxx or file_xxx
        type (str, required): Required, resource type: image or file

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['message_id'] = message_id
    _params['file_key'] = file_key
    _params['type'] = type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_download_resource',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_message_forward(
    *,
    message_id: str,
    receive_id: str,
    receive_id_type: str,
) -> Dict[str, Any]:
    """
    Forward a message to a specified receiver.

    AIME tool: `lark_im_message_forward`

    Args:
        message_id (str, required): Required, message ID to forward (om_xxx)
        receive_id (str, required): Required, target receiver ID
        receive_id_type (str, required): Optional, chat_id (default) or open_id

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['message_id'] = message_id
    _params['receive_id'] = receive_id
    _params['receive_id_type'] = receive_id_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_message_forward',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_message_merge_forward(
    *,
    message_id_list: List[str],
    receive_id: str,
    receive_id_type: str,
) -> Dict[str, Any]:
    """
    Merge forward multiple messages to a specified receiver.

    AIME tool: `lark_im_message_merge_forward`

    Args:
        message_id_list (List[str], required): Required, list of message IDs to forward
        receive_id (str, required): Required, target receiver ID
        receive_id_type (str, required): Optional, chat_id (default) or open_id

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['message_id_list'] = message_id_list
    _params['receive_id'] = receive_id
    _params['receive_id_type'] = receive_id_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_message_merge_forward',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_thread_forward(
    *,
    thread_id: str,
    receive_id: str,
    receive_id_type: str,
) -> Dict[str, Any]:
    """
    Forward a thread (topic) to a specified receiver.

    AIME tool: `lark_im_thread_forward`

    Args:
        thread_id (str, required): Required, thread ID to forward (omt_xxx)
        receive_id (str, required): Required, target receiver ID
        receive_id_type (str, required): Optional, chat_id (default) or open_id

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['thread_id'] = thread_id
    _params['receive_id'] = receive_id
    _params['receive_id_type'] = receive_id_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_thread_forward',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_chat_create(
    *,
    name: str,
    description: str,
    user_id_list: List[str],
    bot_id_list: List[str],
    owner_id: str,
    chat_type: str,
) -> Dict[str, Any]:
    """
    Create a new Lark group chat.

    AIME tool: `lark_im_chat_create`

    Args:
        name (str, required): Optional, group name (required for public groups)
        description (str, required): Optional, group description
        user_id_list (List[str], required): Optional, user open_id list (max 50)
        bot_id_list (List[str], required): Optional, bot app ID list (max 5)
        owner_id (str, required): Optional, owner open_id
        chat_type (str, required): Optional, private (default) or public

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['name'] = name
    _params['description'] = description
    _params['user_id_list'] = user_id_list
    _params['bot_id_list'] = bot_id_list
    _params['owner_id'] = owner_id
    _params['chat_type'] = chat_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_chat_create',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_chat_members_add(
    *,
    chat_id: str,
    id_list: List[str],
    member_id_type: str,
) -> Dict[str, Any]:
    """
    Add members to a Lark group chat.

    AIME tool: `lark_im_chat_members_add`

    Args:
        chat_id (str, required): Required, chat ID (oc_xxx)
        id_list (List[str], required): Required, member ID list (ou_xxx)
        member_id_type (str, required): Optional, default open_id

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['chat_id'] = chat_id
    _params['id_list'] = id_list
    _params['member_id_type'] = member_id_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_chat_members_add',
        parameters=_params,
        response_format="raw",
    ).data


def lark_im_chat_get_share_link(
    *,
    chat_id: str,
    validity_period: str,
) -> Dict[str, Any]:
    """
    Get a Lark group chat share link without sending a message. Use this when the user only wants the group share link.

    AIME tool: `lark_im_chat_get_share_link`

    Args:
        chat_id (str, required): Required, chat ID (oc_xxx) to generate a share link for
        validity_period (str, required): Optional, share link validity period: week, year, or permanently. Default is week

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['chat_id'] = chat_id
    _params['validity_period'] = validity_period
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_im_chat_get_share_link',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_im_send_message',
    'lark_im_upload_resource',
    'lark_im_create_card',
    'lark_im_download_resource',
    'lark_im_message_forward',
    'lark_im_message_merge_forward',
    'lark_im_thread_forward',
    'lark_im_chat_create',
    'lark_im_chat_members_add',
    'lark_im_chat_get_share_link',
]
