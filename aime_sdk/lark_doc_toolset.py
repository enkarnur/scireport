"""
AIME Toolset SDK: `lark_doc_toolset`

Lark doc can do the following things:
- Lark document downloader
- Download a skipped Lark document image/media by token
- Generate a Lark/Feishu document from a markdown file
- Update an existing Lark document by modifying specific blocks. Each block is marked with <!-- BLOCK_N | block_id --> at the start and <!-- END_BLOCK_N --> at the end. Supports update (modify content or delete when content is empty) and insert operations
- Mark specified comments as resolved in a Lark document.

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_doc_toolset import lark_download
    result = lark_download(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_doc_toolset'


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


def create_lark_doc(
    *,
    file_path: str,
    title: str,
    secure_label: Optional[str] = None,
    target_location: Optional[str] = None,
    target_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Lark document based on a Markdown file (.lark.md), whenever possible, prioritize using .lark.md files, the .lark.md file content must strictly follow Feishu/lark specific rules, as list in Lark Markdown Formatting. Do not call this tool multiple times in a single task. This will return a Lark/Feishu link, they are the actual final Lark/Feishu documents. There is no need to further verify them. By default, documents are saved in the system cloud drive. Set a target location (folder, wiki node, or personal space) only when the user explicitly requests it. Set the secure label (L2-L4) only when the user explicitly requests a document security label; otherwise omit secure_label. Never infer a secure label from the document content or prior tool calls. Do not set L1 as the secure label.

    AIME tool: `create_lark_doc`

    Args:
        file_path (str, required): 必填，文件绝对路径，支持 Markdown文件（.lark.md），比如：/workspace/iris_e7c707a5-ae78-42d0-b045-1882a9f0a4d7/demo.lark.md，注意：1. 禁止填url 2. 尽量优先使用 .lark.md 文件，文件内容必须遵循 Feishu/lark specific rules, as list in Lark Markdown Formatting
        title (str, required): 必填，文档标题。注意：1. 标题中务必不要包含用户的名字 2. 标题避免冗长 3. 在标题中减少使用括号、冒号等，最多使用一次 4. 标题中不要包含额外说明
        secure_label (str, optional): 可选，仅当用户明确指定文档密级时传入；用户未指定时必须省略，不得根据文档内容或历史工具调用自行选择。仅支持 L2（内部）、L3（保密）、L4（机密）；不允许设置为 L1（公开）
        target_location (str, optional): 可选，目标位置的 token，可以是文件夹 token 或 wiki 节点 token。target_type 为 folder 或 wiki 时必填
        target_type (str, optional): 可选，目标类型：personal（转移到用户个人空间）、folder（移动到指定文件夹）、wiki（移动到指定知识空间节点）。不填则文档保留在系统云盘中

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['file_path'] = file_path
    _params['title'] = title
    if secure_label is not None:
        _params['secure_label'] = secure_label
    if target_location is not None:
        _params['target_location'] = target_location
    if target_type is not None:
        _params['target_type'] = target_type
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='create_lark_doc',
        parameters=_params,
        response_format="raw",
    ).data


def update_lark_doc(
    *,
    document_url: str,
    modifications: List[Dict[str, Any]],
    markdown_file_path: str,
) -> Dict[str, Any]:
    """
    Update an existing Lark document by modifying specific blocks. Existing blocks are wrapped with <!-- BLOCK_N | block_id --> and <!-- END_BLOCK_N --> markers, while new content for insert operations is raw content without any block markers. For insert operations, new content is inserted AFTER the specified block's END marker (<!-- END_BLOCK_N -->). Supports update (modify content or delete when content is empty) and insert operations.

    AIME tool: `update_lark_doc`

    Args:
        document_url (str, required): 必填，要更新的飞书文档完整链接，比如：https://bytedance.larkoffice.com/docx/TIPddm2mLog88Sxeq7JccYL3nJh
        modifications (List[Dict[str, Any]], required): 必填，block 修改列表。支持 update（更新/删除）和 insert（插入）两种操作
        markdown_file_path (str, required): 选填，修改内容来源的 Markdown 文件路径，用于处理图片等相对路径资源

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['modifications'] = modifications
    _params['markdown_file_path'] = markdown_file_path
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='update_lark_doc',
        parameters=_params,
        response_format="raw",
    ).data


def resolve_lark_doc_comments(
    *,
    document_url: str,
    comment_ids: List[str],
) -> Dict[str, Any]:
    """
    Mark specified comments as resolved in a Lark document. Use after handling feedback from document comments.

    AIME tool: `resolve_lark_doc_comments`

    Args:
        document_url (str, required): 必填，飞书文档完整链接，比如：https://bytedance.larkoffice.com/docx/TIPddm2mLog88Sxeq7JccYL3nJh
        comment_ids (List[str], required): 必填，要标记为已解决的飞书文档评论 ID 列表

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['document_url'] = document_url
    _params['comment_ids'] = comment_ids
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='resolve_lark_doc_comments',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_download',
    'lark_media_download',
    'create_lark_doc',
    'update_lark_doc',
    'resolve_lark_doc_comments',
]
