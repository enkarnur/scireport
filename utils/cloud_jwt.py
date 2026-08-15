"""Process-local Cloud JWT cache backed by ``byted_aime_sdk``.

Credentials refresh five minutes before JWT expiry. Callers may force a refresh
after a confirmed authentication failure. Token values are never logged.
"""

import base64
import binascii
import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

from byted_aime_sdk import (
    CloudCredential,
    CredentialError,
    get_cloud_credential as _sdk_get_cloud_credential,
)
from utils.logger import log

_REFRESH_SKEW_SECONDS = 5 * 60
_CONTEXT_ENV_KEYS = (
    "AIME_CREDENTIAL_BROKER_URL",
    "AIME_CREDENTIAL_BROKER_TOKEN",
    "AIME_ASSISTANT_ID",
    "AIME_CURRENT_USER",
)


@dataclass
class _CacheEntry:
    credential: CloudCredential
    expires_at: float
    context_key: str


_cache_lock = threading.Lock()
_cache_entry: Optional[_CacheEntry] = None
_cache_generation = 0


def _context_key() -> str:
    raw = "\0".join(os.environ.get(key, "") for key in _CONTEXT_ENV_KEYS)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _jwt_expires_at(access_token: str) -> Optional[float]:
    """Read the unverified exp claim for cache expiry decisions only."""
    parts = access_token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        expires_at = float(data["exp"])
    except (
        binascii.Error,
        UnicodeDecodeError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None
    return expires_at


def _cache_is_fresh(entry: Optional[_CacheEntry], context_key: str, now: float) -> bool:
    return bool(
        entry
        and entry.context_key == context_key
        and now < entry.expires_at - _REFRESH_SKEW_SECONDS
    )


def _cache_is_unexpired(entry: Optional[_CacheEntry], context_key: str, now: float) -> bool:
    return bool(entry and entry.context_key == context_key and now < entry.expires_at)


def invalidate_cloud_credential() -> None:
    """Drop the process-local credential cache."""
    global _cache_entry, _cache_generation
    with _cache_lock:
        _cache_entry = None
        _cache_generation += 1
    log("[cloud-jwt] cache invalidated")


def get_cloud_credential(force_refresh: bool = False) -> CloudCredential:
    """Return a cached credential or fetch a current one from the runtime SDK.

    A normal proactive refresh may fall back to an unexpired cached credential
    when the SDK call fails. A forced refresh never falls back to cache.
    """
    global _cache_entry, _cache_generation

    context_key = _context_key()
    observed_generation = _cache_generation
    with _cache_lock:
        now = time.time()
        if (
            force_refresh
            and _cache_generation != observed_generation
            and _cache_is_unexpired(_cache_entry, context_key, now)
        ):
            log("[cloud-jwt] forced refresh coalesced")
            return _cache_entry.credential
        if not force_refresh and _cache_is_fresh(_cache_entry, context_key, now):
            remaining_seconds = max(0, int(_cache_entry.expires_at - now))
            log(f"[cloud-jwt] cache hit remaining_seconds={remaining_seconds}")
            return _cache_entry.credential

        stale_entry = (
            _cache_entry
            if _cache_is_unexpired(_cache_entry, context_key, now)
            else None
        )
        refresh_reason = "forced" if force_refresh else (
            "refresh_window" if stale_entry else "cache_miss"
        )
        started_at = time.monotonic()
        log(f"[cloud-jwt] refresh start reason={refresh_reason}")
        try:
            credential = _sdk_get_cloud_credential()
            access_token = (credential.access_token or "").strip()
            token_type = (credential.token_type or "").strip()
            if not access_token or not token_type:
                raise CredentialError(
                    "Cloud credential is missing access_token or token_type"
                )
            expires_at = _jwt_expires_at(access_token)
            if expires_at is not None and expires_at <= time.time():
                raise CredentialError("Cloud credential is already expired")
        except Exception as exc:
            duration_ms = round((time.monotonic() - started_at) * 1000)
            if not force_refresh and stale_entry is not None:
                remaining_seconds = max(0, int(stale_entry.expires_at - time.time()))
                log(
                    "[cloud-jwt] refresh failed, using unexpired cache "
                    f"duration_ms={duration_ms} remaining_seconds={remaining_seconds} "
                    f"error_type={type(exc).__name__}"
                )
                return stale_entry.credential
            log(
                "[cloud-jwt] refresh failed "
                f"reason={refresh_reason} duration_ms={duration_ms} "
                f"error_type={type(exc).__name__}"
            )
            raise

        duration_ms = round((time.monotonic() - started_at) * 1000)
        if expires_at is None:
            _cache_entry = None
            log(
                "[cloud-jwt] refresh success cacheable=false reason=missing_exp "
                f"duration_ms={duration_ms} token_type={token_type}"
            )
        else:
            _cache_entry = _CacheEntry(
                credential=credential,
                expires_at=expires_at,
                context_key=context_key,
            )
            _cache_generation += 1
            remaining_seconds = max(0, int(expires_at - time.time()))
            log(
                "[cloud-jwt] refresh success cacheable=true "
                f"duration_ms={duration_ms} remaining_seconds={remaining_seconds} "
                f"token_type={token_type}"
            )
        return credential


def get_jwt_token_from_sdk(force_refresh: bool = False) -> str:
    """Return the raw Cloud JWT via the cached ``byted_aime_sdk`` path.

    Used by long-running Service. Fetches through :func:`get_cloud_credential`,
    so the process-local cache and proactive refresh apply. The token value is
    never logged.
    """
    return get_cloud_credential(force_refresh=force_refresh).access_token


def get_jwt_token_from_env() -> str:
    """Return the raw user Cloud JWT injected into short-lived Command / Hook.

    Command and Hook processes receive a freshly injected credential per run via
    the ``AIME_USER_CLOUD_JWT`` environment variable, so they read it directly
    and skip the Service-side cache. When that variable is absent, fall back to
    the cached SDK path. Never log the value.
    """
    token = os.environ.get("AIME_USER_CLOUD_JWT", "").strip()
    if token:
        return token
    log("[cloud-jwt] user JWT env missing, falling back to runtime SDK")
    return get_jwt_token_from_sdk()


__all__ = [
    "CloudCredential",
    "CredentialError",
    "get_cloud_credential",
    "get_jwt_token_from_env",
    "get_jwt_token_from_sdk",
    "invalidate_cloud_credential",
]
