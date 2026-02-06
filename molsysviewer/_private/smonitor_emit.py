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
