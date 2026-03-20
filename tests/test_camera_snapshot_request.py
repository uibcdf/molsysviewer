from molsysviewer import MolSysView


def test_request_camera_snapshot_sends_message_when_ready(monkeypatch):
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    result = view._request_camera_snapshot(timeout_s=0)  # noqa: SLF001

    assert result is True
    assert sent == [{"op": "request_camera_snapshot"}]


def test_write_html_requests_camera_snapshot_when_ready(monkeypatch, tmp_path):
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda _msg: None  # type: ignore[assignment]

    called = {}

    def fake_request():
        called["requested"] = True
        return True

    monkeypatch.setattr(view, "_request_camera_snapshot", fake_request)
    monkeypatch.setattr(view, "_build_standalone_html", lambda *args, **kwargs: "HTML")

    outfile = tmp_path / "out.html"
    view.export.html(str(outfile))

    assert called.get("requested") is True
