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
def _capture_domain_protocol_for_tests(monkeypatch):
    """Capture domain sends for assertions without a production replay journal."""
    from molsysviewer import MolSysView
    from molsysviewer.viewer.history import HistoryMixin

    original_init = MolSysView.__init__
    original_send = HistoryMixin._send
    original_send_replay = HistoryMixin._send_replay

    def instrumented_init(self, *args, **kwargs):
        self._test_message_log = []
        original_init(self, *args, **kwargs)

    def instrumented_send(self, message):
        if message.get("op") == "clear_all":
            self._test_message_log.clear()
        self._test_message_log.append(message)
        return original_send(self, message)

    def instrumented_send_replay(self, message):
        self._test_message_log.append(message)
        return original_send_replay(self, message)

    monkeypatch.setattr(MolSysView, "__init__", instrumented_init)
    monkeypatch.setattr(HistoryMixin, "_send", instrumented_send)
    monkeypatch.setattr(HistoryMixin, "_send_replay", instrumented_send_replay)
    yield


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

    def _drive(view, max_steps: int = 512, target_endpoint_id=None) -> None:
        from molsysviewer.transport import TransferState

        for _ in range(max_steps):
            manager = view._structure_transfer_manager(target_endpoint_id)  # noqa: SLF001
            transfer = manager.active if manager is not None else None
            if transfer is None:
                return
            event = {
                "viewer_id": view._binary_viewer_id,  # noqa: SLF001
                "session_id": view._binary_session_id,  # noqa: SLF001
                "stream_id": transfer.stream_id,
                "generation": transfer.generation,
            }
            if transfer.target_endpoint_id is not None:
                event["target_endpoint_id"] = transfer.target_endpoint_id
            if transfer.state is TransferState.WAITING_BEGIN_ACK:
                event["event"] = "structure_data_begin_ack"
            elif transfer.state is TransferState.WAITING_CHUNK_ACK:
                event["event"] = "structure_data_chunk_ack"
                event["chunk_id"] = transfer.awaited_chunk
            elif transfer.state is TransferState.WAITING_COMPLETE:
                event["event"] = "structure_data_complete"
            else:  # pragma: no cover — an unknown state must not spin silently
                raise AssertionError(f"unexpected stream state {transfer.state!r}")
            view._handle_frontend_event(event)  # noqa: SLF001
        raise AssertionError("the structure stream did not complete")

    return _drive
