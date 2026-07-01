from molsysviewer import MolSysView
from molsysviewer.widget import MolSysViewerWidget


def test_widget_state_syncs_small_bootstrap_not_full_runtime():
    widget = MolSysViewerWidget()
    state = widget.get_state(drop_defaults=False)

    assert "popup_js_source" not in state
    assert len(state["_esm"]) < 50_000
    assert "request_widget_runtime_source" in state["_esm"]
    assert len(MolSysViewerWidget._viewer_js_source) > 1_000_000


def test_popup_source_request_sends_before_ready_without_recording(monkeypatch):
    monkeypatch.setattr(MolSysViewerWidget, "_viewer_js_source", "export const popup = true;")
    view = MolSysView()
    sent = []
    view.widget.send = sent.append  # type: ignore[method-assign]
    # Do NOT force _ready: the source-request handshake happens before the
    # runtime loads, so _ready is still False. The source must be sent anyway.
    assert view._ready is False  # noqa: SLF001
    history_len = len(view._message_history)  # noqa: SLF001
    shape_history_len = len(view._shape_history)  # noqa: SLF001

    view._handle_frontend_event({"event": "request_popup_source"})  # noqa: SLF001

    assert sent == [{"op": "popup_source", "source": "export const popup = true;"}]
    # Runtime-only: the 6 MB source must never bloat the reproducible history.
    assert len(view._message_history) == history_len  # noqa: SLF001
    assert len(view._shape_history) == shape_history_len  # noqa: SLF001


def test_widget_runtime_source_request_sends_before_ready_without_recording(monkeypatch):
    # Regression: the lazy-load bootstrap asks for the runtime source *before*
    # the runtime exists, so _ready is False. If the response is gated on _ready
    # it is dropped, the bootstrap times out, and the cell renders blank. The
    # source must be sent immediately, regardless of _ready, and never recorded.
    monkeypatch.setattr(MolSysViewerWidget, "_viewer_js_source", "export default { render() {} };")
    view = MolSysView()
    sent = []
    view.widget.send = sent.append  # type: ignore[method-assign]
    assert view._ready is False  # noqa: SLF001
    history_len = len(view._message_history)  # noqa: SLF001
    shape_history_len = len(view._shape_history)  # noqa: SLF001

    view._handle_frontend_event({"event": "request_widget_runtime_source"})  # noqa: SLF001

    assert sent == [{"op": "widget_runtime_source", "source": "export default { render() {} };"}]
    assert len(view._message_history) == history_len  # noqa: SLF001
    assert len(view._shape_history) == shape_history_len  # noqa: SLF001
