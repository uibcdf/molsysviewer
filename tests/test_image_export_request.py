from pathlib import Path

from molsysviewer import FigureSpec, MolSysView


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


def test_export_figure_uses_figure_defaults(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    fake_png = "data:image/png;base64,iVBORw0KGgo="
    calls = []

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-defaults.png"
    view.export.figure(str(outfile))

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls == [
        {
            "width_px": None,
            "height_px": None,
            "scale": 2.0,
            "transparent": False,
            "preset": "publication-light",
            "camera_snapshot": None,
            "skip_digestion": True,
        }
    ]


def test_export_figure_transparent_background_uses_current_preset(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-transparent.png"
    view.export.figure(str(outfile), background="transparent")

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls[0]["transparent"] is True
    assert calls[0]["preset"] == "current"


def test_export_figure_dark_background_maps_to_publication_dark(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-dark.png"
    view.export.figure(str(outfile), background="dark")

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls[0]["transparent"] is False
    assert calls[0]["preset"] == "publication-dark"


def test_export_figure_uses_figure_spec_defaults(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []
    spec = FigureSpec(width_px=1200, height_px=900, scale=3.0, background="dark", preset="publication-dark")

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-spec.png"
    view.export.figure(str(outfile), figure_spec=spec)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls == [
        {
            "width_px": 1200,
            "height_px": 900,
            "scale": 3.0,
            "transparent": False,
            "preset": "publication-dark",
            "camera_snapshot": None,
            "skip_digestion": True,
        }
    ]


def test_export_figure_allows_explicit_overrides_over_figure_spec(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []
    spec = FigureSpec(width_px=1200, height_px=900, scale=3.0, background="dark", preset="publication-dark")

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-spec-override.png"
    view.export.figure(str(outfile), figure_spec=spec, width_px=800, background="transparent")

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls == [
        {
            "width_px": 800,
            "height_px": 900,
            "scale": 3.0,
            "transparent": True,
            "preset": "current",
            "camera_snapshot": None,
            "skip_digestion": True,
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
