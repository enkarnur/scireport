"""
AIME Toolset SDK: `lark_common_toolset`

Lark common can do the following things:
- Lark document/sheet/bitable downloader
  * For bitable (multi-dimensional table): only downloads the original table as a single CSV file, without views or other tables. Consider using lark_bitable skill tools for comprehensive bitable analysis.
- Download a skipped Lark document image/media by token
- Convert csv、xlsx、xls files to Lark/Feishu sheets/table or Lark/Feishu Base. (将csv、xlsx、xls文件转换为飞书表格或多维表格)
- Batch move existing Lark documents to a specified folder, wiki node, or user's personal space, with optional secure label setting. Auto-transfers ownership if owned by system account. (批量迁移飞书文档到指定文件夹、知识空间节点或用户个人空间，自动处理系统账号文档的所有权转移)
- Validate template reports in Feishu template scenarios to ensure they meet all template requirements.
- Get Lark user info by extracted user id from email or get all members info of a chat group by chat_id
- Get current user's avatar and download locally

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_common_toolset import lark_download
    result = lark_download(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_common_toolset'


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


def lark_media_download(
    *,
    file_token: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Download one skipped Lark document image/media by file token into the workspace. Use this when lark_download returns a skipped image placeholder with download_tool=lark_media_download.

    AIME tool: `lark_media_download`

    Args:
        file_token (str, required): Required, file token from the skipped image placeholder, for example token=<TOKEN>
        output_path (str, optional): Optional workspace-relative output path. Defaults to lark_media/<sanitized_token>; lark-cli appends an extension when needed.

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['file_token'] = file_token
    if output_path is not None:
        _params['output_path'] = output_path
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_media_download',
        parameters=_params,
        response_format="raw",
    ).data


def create_lark_table(
    *,
    file_path: str,
    title: str,
    table_type: str,
) -> Dict[str, Any]:
    """
    将文件转换为飞书表格或多维表格。支持以下格式：(1. 飞书表格(sheets/table)：支持 xlsx、csv、xls 文件 (2. 飞书多维表格(Base)：支持 xlsx、csv 文件。
    Convert files to Lark sheets/table or Lark Base. Supported formats: (1. Lark Sheets: supports xlsx, csv, xls files (2. Lark Base: supports xlsx, csv files

    AIME tool: `create_lark_table`

    Args:
        file_path (str, required): 必填，文件绝对路径，支持多种文件格式：1. xlsx、csv、xls文件转飞书表格；2. xlsx、csv文件转飞书多维表格。比如：/workspace/iris_e7c707a5-ae78-42d0-b045-1882a9f0a4d7/data.csv，注意：1. 禁止填url 2. 文件路径必须真实存在（提前使用命令行工具确认文件路径）
        title (str, required): 必填，表格标题
        table_type (str, required): 可选，指定转换的目标表格类型，可选值：sheets(电子表格)、base(多维表格)，默认根据文件类型自动选择

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['file_path'] = file_path
    _params['title'] = title
    _params['table_type'] = table_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='create_lark_table',
        parameters=_params,
        response_format="raw",
    ).data


def move_lark_doc(
    *,
    document_urls: List[str],
    target_type: str,
    target_location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    批量迁移已有飞书文档到指定目录（文件夹、知识空间节点或用户个人空间）。如果文档所有者是系统账号（aime），会自动先转移所有权给用户再执行后续操作。Move existing Lark documents to a specified folder, wiki node, or user's personal space in batch.

    AIME tool: `move_lark_doc`

    Args:
        document_urls (List[str], required): 必填，待迁移的飞书文档 URL 列表，如 ["https://bytedance.larkoffice.com/docx/xxx", "https://bytedance.larkoffice.com/sheets/yyy"]
        target_type (str, required): 必填，目标类型：personal（转移到用户个人空间）、folder（移动到指定文件夹）、wiki（移动到指定知识空间节点）
        target_location (str, optional): 可选，目标位置的 token。target_type 为 folder 时填文件夹 token，为 wiki 时填知识空间节点 token，为 personal 时不需要填

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_urls'] = document_urls
    _params['target_type'] = target_type
    if target_location is not None:
        _params['target_location'] = target_location
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='move_lark_doc',
        parameters=_params,
        response_format="raw",
    ).data


def copy_lark_doc(
    *,
    document_url: str,
    name: str,
    folder_token: str,
) -> Dict[str, Any]:
    """
    复制飞书文档（doc/docx/sheet/bitable/mindnote/slides/file 等），将源文档复制到指定文件夹中（不支持复制文件夹）。完整复制整个文档，包括其中的图片，公式，关系，视图（仅多维表格）等，在需要创建副本的场景（例如缺乏直接编辑权限）需要使用此工具

    AIME tool: `copy_lark_doc`

    Args:
        document_url (str, required): 必填，待复制的飞书文档 URL，例如 https://bytedance.larkoffice.com/docx/xxx 或 https://bytedance.larkoffice.com/sheets/yyy
        name (str, required): 可选，复制后文件的新名称；不填默认使用源文件名加 (副本) 后缀
        folder_token (str, required): 可选，目标文件夹 token；不填则复制到「我的空间」根目录

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['name'] = name
    _params['folder_token'] = folder_token
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='copy_lark_doc',
        parameters=_params,
        response_format="raw",
    ).data


def lark_user_info(
    *,
    chat_id: Optional[str] = None,
    emails: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    get Lark user info by emails, or get all members info of a chat group by chat_id. If the result indicates the user is not visible to the bot, stop immediately and inform the user — do not attempt any other tools to work around this.

    AIME tool: `lark_user_info`

    Args:
        chat_id (str, optional): optional, chat id, e.g oc_1234567890. either emails or chat_id is required
        emails (List[str], optional): optional, email array, e.g ['zhangsan.001@bytedance.com']. either emails or chat_id is required

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    if chat_id is not None:
        _params['chat_id'] = chat_id
    if emails is not None:
        _params['emails'] = emails
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_user_info',
        parameters=_params,
        response_format="raw",
    ).data


def lark_get_avatar() -> Dict[str, Any]:
    """
    get current user's Lark avatar url and download locally

    AIME tool: `lark_get_avatar`

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_get_avatar',
        parameters=_params,
        response_format="raw",
    ).data


def validate_template_report(
    *,
    report_path: str,
    template_path: str,
    validation_round: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate whether a generated report meets the requirements of a Lark/Feishu document template. This tool is specifically designed for Feishu template scenarios. DO NOT use this tool in technical solution/proposal generation scenarios. It compares the template file and the generated report file to check completeness, structure consistency, placeholder replacement, format correctness, and content quality. Use this tool in the final validation task before creating the Lark document to ensure the report fully satisfies all template requirements. The tool will return detailed validation results including any issues found and suggestions for improvement.

    AIME tool: `validate_template_report`

    Args:
        report_path (str, required): 必填，生成的报告文件路径 (*.lark.md)
        template_path (str, required): 必填，模版文件路径 (*.lark.md)
        validation_round (int, optional): 可选，当前是第几轮验证（默认为1）。轮次越高，验证越宽容，避免反复修改

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['report_path'] = report_path
    _params['template_path'] = template_path
    if validation_round is not None:
        _params['validation_round'] = validation_round
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='validate_template_report',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_download',
    'lark_media_download',
    'create_lark_table',
    'move_lark_doc',
    'copy_lark_doc',
    'lark_user_info',
    'lark_get_avatar',
    'validate_template_report',
]
