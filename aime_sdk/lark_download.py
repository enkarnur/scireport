"""
AIME Toolset SDK: `lark_download`

lark_download can download Lark document/sheet

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_download import lark_download
    result = lark_download(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_download'


def lark_download(
    *,
    document_url: str,
) -> Dict[str, Any]:
    """
    download file from the lark url, save locally, and return file path list, example: ["doc_title_xxx.lark.md", "sheet_title_xxx.xlsx"]

    AIME tool: `lark_download`

    Args:
        document_url (str, required): required, lark document/sheet url, example: https://domain.larkoffice.com/docx/CCzFdEVGXoyLpmxxxxxx, https://bytedance.larkoffice.com/sheets/xxxxx?sheet=xxxxx

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_download',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_download',
]
