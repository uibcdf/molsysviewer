"""Private, string-compatible native status messages with explicit semantics."""

from __future__ import annotations


class _StatusMessage(str):
    def __new__(cls, message: str, kind: str = "info"):
        if kind not in {"info", "progress", "error", "ready"}:
            raise ValueError(f"Unsupported Qt status kind: {kind!r}")
        result = super().__new__(cls, message)
        result.kind = kind
        return result


# Native-only capabilities, not scene state or widget preferences.
_HOST_SHORTCUTS = (
    ("Ctrl+N", "Clear to an empty view"),
    ("Ctrl+O", "Open a file, replacing the system"),
    ("Ctrl+Shift+R", "Restore the last recorded source"),
    ("Ctrl+W", "Close the window"),
    ("Ctrl+1 / Ctrl+2", "Open Studio / Add-ons"),
    ("Ctrl+Shift+S", "Export HTML"),
    ("Ctrl+Shift+E", "Export a figure"),
    ("Ctrl+Shift+D", "Read or copy the last status message"),
)
