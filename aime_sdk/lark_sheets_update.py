"""
AIME Toolset SDK: `lark_sheets_update`

Lark Sheets Update Tools:
	- Operate sheets: create/copy/delete sheet
	- Initialize first row/column headers from local xlsx
	- Update a specific sheet by aligning rows/cols and batch updating cell ranges
	- Accepts wiki links as input for updates. Ensure the wiki link represents a Sheets document—either via link resolution or by attempting a download: if the downloaded file is xlsx, treat it as Sheets and proceed with the update flow.
	- Dependency: If "lark_sheets_update" is selected, you MUST also select the "lark" tool (for underlying download/create lark sheets).

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_sheets_update import mcp_lark_sheets_update_lark_sheet_ops
    result = mcp_lark_sheets_update_lark_sheet_ops(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_sheets_update'


def mcp_lark_sheets_update_lark_sheet_ops(
    *,
    document_url: str,
    operation: str,
    title: str,
    index: int,
    source_sheet_name: str,
) -> Dict[str, Any]:
    """
    Operate lark sheets: create/copy/delete sheet within a spreadsheet by URL

    AIME tool: `mcp:lark_sheets_update_lark_sheet_ops`

    Args:
        document_url (str, required): 必填，要操作的飞书表格链接，如 https://bytedance.larkoffice.com/sheets/XXX
        operation (str, required): 必填，操作类型：create/copy/delete
        title (str, required): 选填，新建或复制时的工作表标题
        index (int, required): 选填，插入位置索引(从0开始)
        source_sheet_name (str, required): 选填，复制/删除时的源sheet名称

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['operation'] = operation
    _params['title'] = title
    _params['index'] = index
    _params['source_sheet_name'] = source_sheet_name
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:lark_sheets_update_lark_sheet_ops',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_lark_sheets_update_lark_init_sheet_headers(
    *,
    document_url: str,
    sheet_name: str,
    dimension: str,
    source_file_path: str,
) -> Dict[str, Any]:
    """
    Insert first row or column or both, then batch update headers from source xlsx

    AIME tool: `mcp:lark_sheets_update_lark_init_sheet_headers`

    Args:
        document_url (str, required): 必填，飞书表格链接
        sheet_name (str, required): 必填，工作表名称
        dimension (str, required): 必填，ROWS/COLUMNS/BOTH
        source_file_path (str, required): 必填，源xlsx文件绝对路径

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['sheet_name'] = sheet_name
    _params['dimension'] = dimension
    _params['source_file_path'] = source_file_path
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:lark_sheets_update_lark_init_sheet_headers',
        parameters=_params,
        response_format="raw",
    ).data


def mcp_lark_sheets_update_lark_update_sheet(
    *,
    document_url: str,
    sheet_name: str,
    source_file_path: str,
) -> Dict[str, Any]:
    """
    Update a specific sheet within Lark spreadsheet from a source xlsx: align rows/cols then batch update cell ranges

    AIME tool: `mcp:lark_sheets_update_lark_update_sheet`

    Args:
        document_url (str, required): 必填，待更新的飞书表格链接
        sheet_name (str, required): 必填，工作表名称
        source_file_path (str, required): 必填，源xlsx文件绝对路径

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['sheet_name'] = sheet_name
    _params['source_file_path'] = source_file_path
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='mcp:lark_sheets_update_lark_update_sheet',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'mcp_lark_sheets_update_lark_sheet_ops',
    'mcp_lark_sheets_update_lark_init_sheet_headers',
    'mcp_lark_sheets_update_lark_update_sheet',
]
