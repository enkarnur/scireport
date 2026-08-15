"""AIME App Dynamic UI sender with a guaranteed source app identity."""

import json
import os
from pathlib import Path

from byted_aime_sdk import send_dynamic_ui as _raw_send_dynamic_ui


def _require_app_id(sender):
    """Locally monkey-patch the SDK callable with a non-bypassable invariant.

    Only this module may import the raw Dynamic UI SDK.  The generated App's
    business directories use ``send_app_dynamic_ui`` below; tests may replace
    ``_raw_send_dynamic_ui`` and assert that the proxy never reaches it without
    a non-empty source identity.
    """
    def guarded_send_dynamic_ui(*args, **kwargs):
        app_id = str(kwargs.get("app_id") or "").strip()
        if not app_id:
            raise RuntimeError(
                "Dynamic UI 代理拒绝调用裸 SDK：必须传入非空 app_id"
            )
        return sender(*args, **kwargs)

    return guarded_send_dynamic_ui


_send_dynamic_ui = _require_app_id(_raw_send_dynamic_ui)


def _manifest_app_id():
    """Load the App-owned identity instead of trusting a caller override."""
    app_json = Path(__file__).resolve().parent.parent / "app.json"
    try:
        app_id = str(json.loads(app_json.read_text(encoding="utf-8")).get("id") or "").strip()
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法读取来源 App ID: {app_json}") from exc
    if not app_id:
        raise RuntimeError(f"来源 App 缺少非空 app.json.id: {app_json}")
    return app_id


def get_source_app_id():
    """Resolve one canonical source ID and reject a conflicting runtime env."""
    app_id = _manifest_app_id()
    runtime_app_id = os.environ.get("AIME_APP_ID", "").strip()
    if runtime_app_id and runtime_app_id != app_id:
        raise RuntimeError(
            "AIME_APP_ID 与当前 app.json.id 不一致，拒绝以环境变量覆盖发卡来源身份"
        )
    return app_id


def send_app_dynamic_ui(**kwargs):
    """发送 Dynamic UI，并自动附带来源 App ID。

    缺少 app_id 时，会导致前端对话流卡片中的卡片调用 openApp 时无法打开右侧 Canvas 应用页面(安全限制)。
    """
    source_app_id = get_source_app_id()
    requested_app_id = str(kwargs.pop("app_id", "") or "").strip()
    if requested_app_id and requested_app_id != source_app_id:
        raise RuntimeError(
            "Dynamic UI app_id 必须与当前 App 来源身份一致，不能通过封装跨 App 发卡"
        )
    return _send_dynamic_ui(app_id=source_app_id, **kwargs)
