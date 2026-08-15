"""
AIME Toolset SDK: `lark_bitable`

bitable toolset

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_bitable import lark_bitable_ParseLarkWikiURL
    result = lark_bitable_ParseLarkWikiURL(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_bitable'


def lark_bitable_ParseLarkWikiURL() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_ParseLarkWikiURL`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_ParseLarkWikiURL',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_SearchBitableRecordByRecordIDs() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_SearchBitableRecordByRecordIDs`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_SearchBitableRecordByRecordIDs',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_UpdateBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_UpdateBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_UpdateBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_ListAppTableView() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_ListAppTableView`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_ListAppTableView',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_ListAppTableField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_ListAppTableField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_ListAppTableField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_DeleteAppTableField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_DeleteAppTableField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_DeleteAppTableField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_DeleteBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_DeleteBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_DeleteBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_UpdateBitableAppTable() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_UpdateBitableAppTable`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_UpdateBitableAppTable',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_GetAppTableForm() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_GetAppTableForm`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_GetAppTableForm',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_SearchBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_SearchBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_SearchBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_CreateAppTableView() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_CreateAppTableView`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_CreateAppTableView',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_UpdateAppTableField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_UpdateAppTableField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_UpdateAppTableField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_ListBitableAppTable() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_ListBitableAppTable`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_ListBitableAppTable',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_CreateBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_CreateBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_CreateBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_BatchUpdateBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_BatchUpdateBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_BatchUpdateBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_BatchDeleteBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_BatchDeleteBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_BatchDeleteBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_GetAppTableView() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_GetAppTableView`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_GetAppTableView',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_PatchAppTableForm() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_PatchAppTableForm`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_PatchAppTableForm',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_DownloadLarkAttachment() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_DownloadLarkAttachment`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_DownloadLarkAttachment',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_CreateBitableAppTable() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_CreateBitableAppTable`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_CreateBitableAppTable',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_SearchBitableRecordByFilter() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_SearchBitableRecordByFilter`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_SearchBitableRecordByFilter',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_PatchAppTableView() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_PatchAppTableView`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_PatchAppTableView',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_CreateAppTableField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_CreateAppTableField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_CreateAppTableField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_GetBitableInfo() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_GetBitableInfo`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_GetBitableInfo',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_BatchCreateBitableRecord() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_BatchCreateBitableRecord`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_BatchCreateBitableRecord',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_DeleteAppTableView() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_DeleteAppTableView`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_DeleteAppTableView',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_ListAppTableFormField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_ListAppTableFormField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_ListAppTableFormField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_PatchAppTableFormField() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_PatchAppTableFormField`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_PatchAppTableFormField',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_UploadFileAttachment() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_UploadFileAttachment`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_UploadFileAttachment',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_CreateBitableApp() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_CreateBitableApp`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_CreateBitableApp',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_DeleteBitableAppTable() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_DeleteBitableAppTable`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_DeleteBitableAppTable',
        parameters=_params,
        response_format="raw",
    ).data


def lark_bitable_SearchBitableRecordByViewID() -> Dict[str, Any]:
    """

    AIME tool: `lark_bitable_SearchBitableRecordByViewID`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_bitable_SearchBitableRecordByViewID',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_bitable_ParseLarkWikiURL',
    'lark_bitable_SearchBitableRecordByRecordIDs',
    'lark_bitable_UpdateBitableRecord',
    'lark_bitable_ListAppTableView',
    'lark_bitable_ListAppTableField',
    'lark_bitable_DeleteAppTableField',
    'lark_bitable_DeleteBitableRecord',
    'lark_bitable_UpdateBitableAppTable',
    'lark_bitable_GetAppTableForm',
    'lark_bitable_SearchBitableRecord',
    'lark_bitable_CreateAppTableView',
    'lark_bitable_UpdateAppTableField',
    'lark_bitable_ListBitableAppTable',
    'lark_bitable_CreateBitableRecord',
    'lark_bitable_BatchUpdateBitableRecord',
    'lark_bitable_BatchDeleteBitableRecord',
    'lark_bitable_GetAppTableView',
    'lark_bitable_PatchAppTableForm',
    'lark_bitable_DownloadLarkAttachment',
    'lark_bitable_CreateBitableAppTable',
    'lark_bitable_SearchBitableRecordByFilter',
    'lark_bitable_PatchAppTableView',
    'lark_bitable_CreateAppTableField',
    'lark_bitable_GetBitableInfo',
    'lark_bitable_BatchCreateBitableRecord',
    'lark_bitable_DeleteAppTableView',
    'lark_bitable_ListAppTableFormField',
    'lark_bitable_PatchAppTableFormField',
    'lark_bitable_UploadFileAttachment',
    'lark_bitable_CreateBitableApp',
    'lark_bitable_DeleteBitableAppTable',
    'lark_bitable_SearchBitableRecordByViewID',
]
