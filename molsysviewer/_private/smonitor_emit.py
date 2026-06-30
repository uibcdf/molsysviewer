from __future__ import annotations

from typing import Any, Dict, Optional

from smonitor.integrations import emit_from_catalog

from molsysviewer._private.smonitor import CATALOG, PACKAGE_ROOT, META


def message_from_catalog(
    entry_key: str,
    *,
    extra: Optional[Dict[str, Any]] = None,
    default_message: Optional[str] = None,
) -> str:
    entry = CATALOG.get(entry_key)
    if entry is None:
        return default_message or ""
    try:
        event = emit_from_catalog(
            entry,
            package_root=PACKAGE_ROOT,
            extra=extra,
            meta=META,
        )
        message = event.get("message") or default_message or ""
        hint = (event.get("extra") or {}).get("hint")
        if hint:
            message = f"{message} {hint}" if message else hint
        return message or (default_message or "")
    except Exception:
        return default_message or ""


def emit_suppressed_exception(
    location: str,
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    extra: Dict[str, Any] = {
        "location": str(location),
        "exception_type": type(exc).__name__,
        "reason": str(exc),
    }
    if context:
        extra.update(context)
    return message_from_catalog(
        "suppressed_exception",
        extra=extra,
        default_message=f"Recovered from suppressed exception in {location}: {exc}.",
    )
