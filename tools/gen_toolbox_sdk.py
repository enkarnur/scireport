#!/usr/bin/env python3
"""Regenerate the AIME Toolbox SDK snapshot committed under the skill.

This script is invoked in two contexts:

1. Manually by developers / CI to refresh the committed default snapshot
   under ``<skill>/aime_sdk/``.
2. Asynchronously from ``app/server-go/start.sh`` at devkit service
   startup, to keep the bundled snapshot in sync with the currently
   installed toolset in the runtime environment.

Design goals:

* Locate the skill root relative to this file (``<skill>/scripts/``) so
  the script works regardless of the caller's ``cwd``.
* Support ``--output <dir>`` to override the destination for special
  cases (mostly tests).
* Be atomic: generate into a temp dir first and only replace the real
  ``aime_sdk`` directory on success. A partial failure leaves the
  previously committed snapshot untouched.
* Never take down the parent process: exit non-zero on failure but keep
  stdout/stderr informative for background-task log files.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import List


# Only these toolsets are relevant for AIME App development. Generating the
# full toolset (files/terminal/...) just bloats the snapshot with tools that
# App code should not reach for. Keep the bundled SDK focused.
DEFAULT_IDENTIFIERS = [
    "agent",
    "codebase",
    "llm",
    # Lark toolsets
    "lark",
    "lark_bitable",
    "lark_card_message",
    "lark_common_toolset",
    "lark_creation",
    "lark_doc_toolset",
    "lark_download",
    "lark_im_message",
    "lark_sheets_update",
]


def _skill_root() -> Path:
    """Return the skill root directory (parent of ``scripts/``)."""
    return Path(__file__).resolve().parent.parent


def _default_output() -> Path:
    return _skill_root() / "aime_sdk"


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate the AIME Toolbox SDK snapshot for the skill."
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help=(
            "Target output directory. Defaults to <skill>/aime_sdk "
            "relative to this script."
        ),
    )
    parser.add_argument(
        "--identifiers",
        nargs="*",
        default=None,
        help=(
            "Toolset identifiers to include. When omitted, the focused "
            "default set is used: " + ", ".join(DEFAULT_IDENTIFIERS) + ". "
            "Pass 'all' to generate every available toolset."
        ),
    )
    return parser.parse_args(argv)


def _rewrite_response_format(root: Path) -> None:
    """Rewrite generated *.py so tools return raw payloads.

    The stock ``byted_aime_sdk`` code generator emits calls with
    ``response_format="text"`` and reads ``.result`` off the wrapper. We
    want callers to get the untransformed ``.data`` (AimeToolResultRaw),
    so patch every generated module in place.
    """
    for path in root.glob("*.py"):
        try:
            src = path.read_text(encoding="utf-8")
        except Exception:
            continue
        new_src = src.replace(
            'response_format="text",\n    ).result',
            'response_format="raw",\n    ).data',
        )
        # Also handle any stray "text"/.result variant just in case.
        new_src = new_src.replace(
            "response_format='text',\n    ).result",
            "response_format='raw',\n    ).data",
        )
        if new_src != src:
            path.write_text(new_src, encoding="utf-8")


def _atomic_replace(tmp_dir: Path, target: Path) -> None:
    """Replace ``target`` with ``tmp_dir`` as atomically as possible.

    On POSIX ``os.replace`` is atomic only for empty destinations or file
    replacements. For directories we fall back to a rename-swap: move
    the old dir aside, move the new one in, then delete the old one.
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        os.replace(tmp_dir, target)
        return

    backup = target.parent / (target.name + ".old")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    os.replace(target, backup)
    try:
        os.replace(tmp_dir, target)
    except Exception:
        # Best-effort rollback if the second move fails.
        if not target.exists():
            os.replace(backup, target)
        raise
    finally:
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    output = Path(args.output).resolve() if args.output else _default_output()

    try:
        from byted_aime_sdk import AimeToolbox
    except Exception:  # pragma: no cover - defensive
        print("[gen_toolbox_sdk] byted_aime_sdk import failed:", file=sys.stderr)
        traceback.print_exc()
        return 2

    tb = AimeToolbox()

    # Generate into a sibling temp dir under the same parent so that the
    # final atomic swap stays on the same filesystem.
    parent = output.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_root = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp.", dir=str(parent))
    )
    # The SDK generator writes directly into the directory we pass it;
    # we point it at a nested path inside tmp_root so we can atomically
    # move that nested path into place.
    tmp_output = tmp_root / output.name

    try:
        kwargs = {}
        # Resolve which toolsets to generate:
        #   - no --identifiers  -> focused DEFAULT_IDENTIFIERS
        #   - --identifiers all -> full toolset (no filter)
        #   - explicit list     -> exactly that list
        if args.identifiers is None:
            kwargs["identifiers"] = list(DEFAULT_IDENTIFIERS)
        elif [s.lower() for s in args.identifiers] == ["all"]:
            pass  # generate everything
        elif args.identifiers:
            kwargs["identifiers"] = list(args.identifiers)
        else:
            # --identifiers passed with no values: fall back to default set.
            kwargs["identifiers"] = list(DEFAULT_IDENTIFIERS)
        modules = tb.generate_sdk(str(tmp_output), **kwargs)

        # Post-process: byted_aime_sdk 默认模板用 response_format="text" 并
        # 取 .result；这里统一改为 "raw" + .data，让调用方拿到未加工的原始
        # 返回值（AimeToolResultRaw.data），避免文本化丢结构。
        _rewrite_response_format(tmp_output)

        if not tmp_output.exists() or not any(tmp_output.iterdir()):
            print(
                "[gen_toolbox_sdk] generator produced no output at "
                f"{tmp_output}",
                file=sys.stderr,
            )
            return 3

        _atomic_replace(tmp_output, output)
        print(
            f"[gen_toolbox_sdk] generated {len(modules)} module(s) into "
            f"{output}"
        )
        return 0
    except Exception:
        print("[gen_toolbox_sdk] generation failed:", file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        # Clean up the temp scratch dir if anything is left behind.
        if tmp_root.exists():
            shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
