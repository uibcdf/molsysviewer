from pathlib import Path

from molsysviewer import MolSysView


def test_request_image_export_sends_message_when_ready():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    result = view._request_image_export(width_px=640, height_px=480, scale=2.0, transparent=True, timeout_s=0)  # noqa: SLF001

    assert result is None
    assert sent == [{"op": "request_image_export", "transparent": True, "scale": 2.0, "width": 640, "height": 480}]


def test_export_image_writes_png_bytes(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)

    fake_png = "data:image/png;base64,iVBORw0KGgo="

    def fake_request(**_kwargs):
        return {"event": "image_export", "format": "png", "data_uri": fake_png}

    monkeypatch.setattr(view, "_request_image_export", fake_request)

    outfile = tmp_path / "scene.png"
    view.export.image(str(outfile), width_px=640, height_px=480, scale=2.0, transparent=True)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"


def test_export_image_legacy_alias_warns(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)

    fake_png = "data:image/png;base64,iVBORw0KGgo="

    def fake_request(**_kwargs):
        return {"event": "image_export", "format": "png", "data_uri": fake_png}

    monkeypatch.setattr(view, "_request_image_export", fake_request)

    outfile = tmp_path / "legacy-scene.png"
    import warnings

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        view.export_image(str(outfile), width_px=640, height_px=480, scale=2.0, transparent=True)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert any(isinstance(record.message, DeprecationWarning) for record in records)


def test_frontend_image_export_event_is_recorded():
    view = MolSysView(debug_js=True)
    event = {
        "event": "image_export",
        "format": "png",
        "data_uri": "data:image/png;base64,iVBORw0KGgo=",
        "width": 640,
        "height": 480,
        "scale": 2.0,
    }

    view._handle_frontend_event(event)  # noqa: SLF001

    assert view._last_image_export_event == event  # noqa: SLF001
