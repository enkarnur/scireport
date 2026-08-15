"""
AIME Toolset SDK: `lark_card_message`

lark card message toolset

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_card_message import lark_send_card_message
    result = lark_send_card_message(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_card_message'


def lark_send_card_message(
    *,
    receiver_id: str,
    id_type: str,
    content: str,
) -> Dict[str, Any]:
    """
    Send Lark card message to specified user or group chat. Supports sending messages via email or group chat ID.

    AIME tool: `lark_send_card_message`

    Args:
        receiver_id (str, required): Required, receiver ID, can be email (e.g. username@bytedance.com) or group chat ID
        id_type (str, required): Required, receiver ID type, optional values: 'email' or 'chat_id', default is 'email'
        content (str, required): Required, card content, supports Markdown format

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['receiver_id'] = receiver_id
    _params['id_type'] = id_type
    _params['content'] = content
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_send_card_message',
        parameters=_params,
        response_format="raw",
    ).data


def lark_upload_image(
    *,
    file_path: str,
    image_type: str,
) -> Dict[str, Any]:
    """
    Upload an image to Lark and return the image key. Supports uploading images from local file system.

    AIME tool: `lark_upload_image`

    Args:
        file_path (str, required): Required, absolute path to the image file
        image_type (str, required): Optional, image type, can be 'message' (for sending messages) or 'avatar' (for setting avatar), default is 'message'

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['file_path'] = file_path
    _params['image_type'] = image_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_upload_image',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_send_card_message',
    'lark_upload_image',
]
