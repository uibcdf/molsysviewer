from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Ensure `pytest` and `python -m pytest` resolve the in-repo package the same way.
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)


def _close_registered_molsysviewer_widgets() -> None:
    from ipywidgets.widgets.widget import _instances

    from molsysviewer.addons import AddonPanelWidget
    from molsysviewer.widget import MolSysViewerWidget

    for widget in list(_instances.values()):
        if not isinstance(widget, (MolSysViewerWidget, AddonPanelWidget)):
            continue
        view_ref = getattr(widget, "_molsysviewer_view_ref", None)
        view = view_ref() if callable(view_ref) else None
        if view is not None:
            view.close()
            continue
        layout = getattr(widget, "layout", None)
        widget.close()
        if layout is not widget:
            close_layout = getattr(layout, "close", None)
            if callable(close_layout):
                close_layout()


@pytest.fixture(autouse=True)
def _close_molsysviewer_widgets_after_each_test():
    """Keep open AnyWidgets from retaining complete views between tests."""
    yield

    _close_registered_molsysviewer_widgets()


@pytest.fixture
def complete_structure_stream():
    """Play the frontend's half of an array-native structure handshake.

    Acknowledges begin and every chunk, then reports completion, exactly as
    `array-native-stream.ts` does — it builds the structure and *only then*
    notifies `structure_data_complete`. Tests that care about what the browser
    can actually draw need that distinction, because Python's scene messages are
    held until this point.
    """

    def _drive(view, max_steps: int = 512) -> None:
        for _ in range(max_steps):
            stream = view._binary_structure_stream  # noqa: SLF001
            if stream is None:
                return
            awaiting = stream["awaiting"]
            event = {
                "viewer_id": view._binary_viewer_id,  # noqa: SLF001
                "session_id": view._binary_session_id,  # noqa: SLF001
                "stream_id": "structures:main",
                "generation": stream["generation"],
            }
            if awaiting == "begin":
                event["event"] = "structure_data_begin_ack"
            elif isinstance(awaiting, tuple):
                event["event"] = "structure_data_chunk_ack"
                event["chunk_id"] = awaiting[1]
            elif awaiting == "complete":
                event["event"] = "structure_data_complete"
            else:  # pragma: no cover — an unknown state must not spin silently
                raise AssertionError(f"unexpected stream state {awaiting!r}")
            view._handle_frontend_event(event)  # noqa: SLF001
        raise AssertionError("the structure stream did not complete")

    return _drive
