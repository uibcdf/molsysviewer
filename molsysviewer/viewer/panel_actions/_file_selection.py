"""Read-only acquisition of molecular input paths in the owning Python host."""

from __future__ import annotations

import heapq
import os
from pathlib import Path

_PAGE_SIZE = 80


def _directory_page(directory, show_hidden=False, after=None):
    """Scan names with bounded retained entries; never read molecular file bytes."""
    if not isinstance(directory, str) or not isinstance(show_hidden, bool):
        raise ValueError("Provide a Python-host directory and an explicit hidden-files choice.")
    base = Path(directory or ".").expanduser().resolve(strict=True)
    if not base.is_dir():
        raise ValueError("Choose a directory in the running Python session.")
    cursor = None
    if after is not None:
        if not (
            isinstance(after, list)
            and len(after) == 3
            and type(after[0]) is int
            and after[0] in (0, 1)
            and all(isinstance(value, str) for value in after[1:])
        ):
            raise ValueError("Invalid file-list page cursor.")
        cursor = tuple(after)

    def candidates(entries):
        for entry in entries:
            if not show_hidden and entry.name.startswith("."):
                continue
            try:
                directory_entry = entry.is_dir()
                if not directory_entry and not entry.is_file():
                    continue
            except OSError:
                continue  # A removed/unresolvable directory entry is not a selectable file.
            key = (0 if directory_entry else 1, entry.name.casefold(), entry.name)
            if cursor is None or key > cursor:
                yield key

    with os.scandir(base) as entries:
        page = heapq.nsmallest(_PAGE_SIZE + 1, candidates(entries))
    shown = page[:_PAGE_SIZE]
    return {
        "kind": "directory",
        "directory": str(base),
        "parent": str(base.parent) if base.parent != base else None,
        "entries": [
            {"name": name, "path": str(base / name), "is_directory": kind == 0} for kind, _folded, name in shown
        ],
        "next_cursor": list(shown[-1]) if len(page) > _PAGE_SIZE else None,
    }


def _browse_load_files(view, content):
    request_id = content.get("request_id")
    try:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("File selection requires a nonempty request identifier.")
        picker = getattr(view, "_studio_file_picker", None)
        if callable(picker):
            # Qt owns the modal window and its lifetime. Selecting paths does not load them.
            paths = picker()
            if not isinstance(paths, (list, tuple)) or any(not isinstance(path, str) for path in paths):
                raise ValueError("The native file picker must return a list of paths.")
            result = {"kind": "selection", "paths": list(paths)}
        else:
            result = _directory_page(
                content.get("directory", ""), content.get("show_hidden", False), content.get("after")
            )
    except Exception as exc:
        view._send_runtime_only(
            {"op": "system_file_browse_result", "request_id": request_id, "ok": False, "error_message": str(exc)}
        )
        raise
    else:
        view._send_runtime_only({"op": "system_file_browse_result", "request_id": request_id, "ok": True, **result})


HANDLERS = {"browse_load_files": _browse_load_files}
