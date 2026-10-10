"""Studio file intentions delegated to the public state/session owners."""

from pathlib import Path
from typing import Any, Mapping


def _file_request(content: Mapping[str, Any]) -> tuple[str, Path]:
    kind = content.get("file_kind")
    path = content.get("path")
    request_id = content.get("request_id")
    if kind not in ("state", "session"):
        raise ValueError("Choose a state JSON or an experimental session MSV file.")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Provide a file path in the running Python session.")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("File operations require a request identifier.")
    return kind, Path(path.strip()).expanduser()


def save_work_file(view: Any, content: Mapping[str, Any]) -> None:
    kind, path = _file_request(content)
    overwrite = content.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise ValueError("Overwrite must be an explicit boolean.")
    if path.exists() and not overwrite:
        raise ValueError("This file already exists. Allow overwrite or choose another path.")
    if kind == "state":
        view.save_state(path)
    else:
        view.save_session(path)


def restore_work_file(view: Any, content: Mapping[str, Any]) -> None:
    kind, path = _file_request(content)
    if content.get("confirmed") is not True:
        raise ValueError("Confirm restoration before replacing the current work.")
    if kind == "state":
        if view.molsys is None:
            raise ValueError("Load the matching molecular system before restoring a state JSON.")
        view.load_state(path, clear_first=True, on_conflict="raise")
    else:
        from ...session import load_session

        load_session(path, view=view)


HANDLERS = {"save_work_file": save_work_file, "restore_work_file": restore_work_file}
