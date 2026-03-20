from pathlib import Path

from molsysviewer import MolSysView


def test_request_image_export_sends_message_when_ready():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    result = view._request_image_export(width_px=640, height_px=480, scale=2.0, transparent=True, timeout_s=0)  # noqa: SLF001

    assert result is None
    assert sent == [{"op": "request_image_export", "transparent": True, "scale": 2.0, "preset": "current", "width": 640, "height": 480}]


def test_request_image_export_includes_camera_snapshot_when_provided():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []
    snapshot = {"target": [0, 0, 0], "position": [10, 5, 3], "up": [0, 1, 0]}

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    result = view._request_image_export(camera_snapshot=snapshot, timeout_s=0)  # noqa: SLF001

    assert result is None
    assert sent == [{"op": "request_image_export", "transparent": False, "scale": 1.0, "preset": "current", "camera_snapshot": snapshot}]


def test_request_image_export_includes_preset_when_provided():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    result = view._request_image_export(preset="publication-light", timeout_s=0)  # noqa: SLF001

    assert result is None
    assert sent == [{"op": "request_image_export", "transparent": False, "scale": 1.0, "preset": "publication-light"}]


def test_export_image_writes_png_bytes(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)

    fake_png = "data:image/png;base64,iVBORw0KGgo="

    def fake_request(**_kwargs):
        return {"event": "image_export", "format": "png", "data_uri": fake_png}

    monkeypatch.setattr(view, "_request_image_export", fake_request)

    outfile = tmp_path / "scene.png"
    view.export.image(str(outfile), width_px=640, height_px=480, scale=2.0, transparent=True)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"


def test_export_image_forwards_camera_snapshot(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    fake_png = "data:image/png;base64,iVBORw0KGgo="
    calls = []
    snapshot = {"target": [0, 0, 0], "position": [1, 1, 1], "up": [0, 1, 0]}

    def fake_request(**kwargs):
        calls.append(kwargs)
        return {"event": "image_export", "format": "png", "data_uri": fake_png}

    monkeypatch.setattr(view, "_request_image_export", fake_request)

    outfile = tmp_path / "camera-scene.png"
    view.export.image(str(outfile), camera_snapshot=snapshot)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls == [
        {
            "width_px": None,
            "height_px": None,
            "scale": 1.0,
            "transparent": False,
            "preset": "current",
            "camera_snapshot": snapshot,
        }
    ]


def test_export_image_forwards_preset(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    fake_png = "data:image/png;base64,iVBORw0KGgo="
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return {"event": "image_export", "format": "png", "data_uri": fake_png}

    monkeypatch.setattr(view, "_request_image_export", fake_request)

    outfile = tmp_path / "publication-scene.png"
    view.export.image(str(outfile), preset="publication-dark")

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls == [
        {
            "width_px": None,
            "height_px": None,
            "scale": 1.0,
            "transparent": False,
            "preset": "publication-dark",
            "camera_snapshot": None,
        }
    ]


def test_frontend_image_export_event_is_recorded():
    view = MolSysView(debug_js=True)
    event = {
        "event": "image_export",
        "format": "png",
        "data_uri": "data:image/png;base64,iVBORw0KGgo=",
        "width": 640,
        "height": 480,
        "scale": 2.0,
        "preset": "publication-light",
    }

    view._handle_frontend_event(event)  # noqa: SLF001

    assert view._last_image_export_event == event  # noqa: SLF001
