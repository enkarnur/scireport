"""
AIME Toolset SDK: `llm`

llm model call toolset

Auto-generated Python SDK. Import the functions and call them directly:

    from aime_sdk.llm import llm_call
    result = llm_call(...)  # returns the tool text result as str

Each function forwards to the AIME tool runtime via byted_aime_sdk.call_aime_tool.
"""
from typing import Any, Dict, List, Optional  # noqa: F401
from byted_aime_sdk import call_aime_tool

_TOOLSET = 'llm'


def llm_call(
    *,
    app_id: str,
    messages: List[Dict[str, Any]],
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Direct LLM call tool that takes messages and parameters, returns full model response

    AIME tool: `llm_call`

    Args:
        app_id (str, required): Required, the application ID making this call
        messages (List[Dict[str, Any]], required): Required, list of messages in the conversation
        max_tokens (int, optional): Optional, maximum number of tokens to generate
        model (str, optional): Optional, model name to use for the LLM call
        temperature (float, optional): Optional, temperature for model response generation (0.0 to 2.0)

    Returns:
        Dict[str, Any]: The tool raw result.
    """
    _params: Dict[str, Any] = {}
    _params['app_id'] = app_id
    _params['messages'] = messages
    if max_tokens is not None:
        _params['max_tokens'] = max_tokens
    if model is not None:
        _params['model'] = model
    if temperature is not None:
        _params['temperature'] = temperature
    return call_aime_tool(
        toolset=_TOOLSET,
        tool_name='llm_call',
        parameters=_params,
        response_format="raw",
    ).data


__all__ = [
    'llm_call',
]
