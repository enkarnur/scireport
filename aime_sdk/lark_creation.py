"""
AIME Toolset SDK: `lark_creation`

lark_creation can do the following things:
- Generate a Lark/Feishu document from a html file or markdown file, please prepare the required pictures, charts and diagrams before using this tool.
- Update a Lark/Feishu document URL from a modified markdown file, please prepare the required pictures, charts and diagrams before using this tool.
- Convert csv、xlsx、xls files to Lark/Feishu sheets/table or Lark/Feishu Base. (将csv、xlsx、xls文件转换为飞书表格或多维表格)

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.lark_creation import lark_creation
    result = lark_creation(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'lark_creation'


def lark_creation(
    *,
    persona: str,
    task: str,
    output_language: str,
) -> Dict[str, Any]:
    """
    lark_creation can create Lark/Feishu Document, Lark/Feishu Sheets(飞书表格), or Lark/Feishu Base(飞书多维表格), **Do not create any lark.md files before using lark_creation tool.**:
    1. When creating a Lark/Feishu Document, input the materials needed for the document (such as search results, data analysis results, etc.), and lark_creation will automatically generate charts or images, organize content, and form a Feishu Doc with a clear structure, professional content, and rich styles.
    2. When creating a Lark/Feishu Sheets / Base, input the data to be written into the sheet, and lark_creation will generate files such as csv, xlsx, xls, etc. according to the data and requirements, and then convert them into Lark/Feishu Sheets / Base.
    lark_creation will return a Lark/Feishu link, they are the actual final Lark/Feishu documents or sheets. There is no need to further verify them. However, if the link url is not provided, it indicates there are some thing wrong and need to retry.

    AIME tool: `lark_creation`

    Args:
        persona (str, required): Persona to put at the very first of the system prompt. Describe the agent's role, capabilities, and any other relevant information. Should establish: 1) Specific expertise domain and professional level 2) Working methodology and quality standards 3) Problem-solving approach and attention to detail 4) Communication style that balances clarity with technical accuracy. The persona should inspire confidence while setting high performance expectations.
        task (str, required): A self contained task prompt that can be completed by the lark agent. The description should give out background context and the specific goals, but not detailed datapoints or libraries to use.
        output_language (str, required): The language of the final output Lark document

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['persona'] = persona
    _params['task'] = task
    _params['output_language'] = output_language
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='lark_creation',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'lark_creation',
]
