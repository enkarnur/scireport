"""加载生成的 api_client.gen.py 模块。

skills 目录含连字符、文件名带 .gen，不能直接 import。
本模块封装 importlib 样板，command / hook / skill 脚本一行导入即可：

    from utils.api_client import api

    result = api.items_list(session)
"""

import importlib.util
from pathlib import Path

_PLUGIN_DIR = Path(__file__).resolve().parent.parent
_CANDIDATES = sorted(_PLUGIN_DIR.glob("skills/*/api_client.gen.py"))

if not _CANDIDATES:
    raise ImportError(
        f"未找到 api_client.gen.py，请先运行 tools/gen_api.py 生成：{_PLUGIN_DIR}/skills/*/api_client.gen.py"
    )

if len(_CANDIDATES) > 1:
    cands = ', '.join(str(p.relative_to(_PLUGIN_DIR)) for p in _CANDIDATES)
    raise ImportError(f"检测到多个 api_client.gen.py（候选：{cands}），无法自动选择")

_path = _CANDIDATES[0]
_spec = importlib.util.spec_from_file_location("api_client_gen", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"无法从 {_path} 创建模块 spec（spec/loader 为空）")
api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)
