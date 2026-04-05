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


def test_figure_spec_from_view_captures_current_camera_snapshot(monkeypatch):
    view = MolSysView(debug_js=True)
    snapshot = {"target": [0, 0, 0], "position": [5, 5, 5], "up": [0, 1, 0]}

    monkeypatch.setattr(view, "get_camera_snapshot", lambda **kwargs: snapshot)

    spec = FigureSpec.from_view(
        view,
        width_px=1600,
        height_px=1200,
        scale=2.5,
        background="dark",
        preset="publication-dark",
    )

    assert spec.info() == {
        "width_px": 1600,
        "height_px": 1200,
        "scale": 2.5,
        "background": "dark",
        "preset": "publication-dark",
        "camera_snapshot": snapshot,
    }


def test_figure_spec_from_view_can_skip_camera_capture(monkeypatch):
    view = MolSysView(debug_js=True)
    monkeypatch.setattr(view, "get_camera_snapshot", lambda **kwargs: {"target": [1, 2, 3]})

    spec = FigureSpec.from_view(view, include_camera=False)

    assert spec.camera_snapshot is None


def test_figure_spec_with_overrides_returns_new_recipe():
    spec = FigureSpec(
        width_px=1200,
        height_px=900,
        scale=3.0,
        background="dark",
        preset="publication-dark",
        camera_snapshot={"target": [0, 0, 0]},
    )

    updated = spec.with_overrides(width_px=1800, background="white", include_camera_snapshot=False)

    assert updated is not spec
    assert updated.info() == {
        "width_px": 1800,
        "height_px": 900,
        "scale": 3.0,
        "background": "white",
        "preset": "publication-dark",
        "camera_snapshot": None,
    }
    assert spec.info()["camera_snapshot"] == {"target": [0, 0, 0]}


def test_export_figure_uses_camera_from_view_derived_figure_spec(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []
    snapshot = {"target": [0, 0, 0], "position": [9, 4, 1], "up": [0, 1, 0]}

    monkeypatch.setattr(view, "get_camera_snapshot", lambda **kwargs: snapshot)

    spec = FigureSpec.from_view(view, width_px=1400, height_px=1000)

    def fake_export_image(output_filename, **kwargs):
        calls.append(kwargs)
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    outfile = tmp_path / "figure-from-view.png"
    view.export.figure(str(outfile), figure_spec=spec)

    assert outfile.read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls[0]["camera_snapshot"] == snapshot
    assert calls[0]["width_px"] == 1400
    assert calls[0]["height_px"] == 1000


def test_figure_spec_build_variants_derives_named_recipes():
    spec = FigureSpec(width_px=1200, height_px=900, scale=3.0, background="white", preset="publication-light")

    variants = spec.build_variants(
        {
            "dark": {"background": "dark", "preset": "publication-dark"},
            "transparent": {"background": "transparent", "preset": "publication-light"},
        }
    )

    assert list(variants) == ["dark", "transparent"]
    assert variants["dark"].background == "dark"
    assert variants["dark"].preset == "publication-dark"
    assert variants["dark"].width_px == 1200
    assert variants["transparent"].background == "transparent"
    assert variants["transparent"].scale == 3.0


def test_export_figure_variants_writes_named_png_batch(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []

    def fake_export_image(output_filename, **kwargs):
        calls.append((output_filename, kwargs))
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    base = FigureSpec(width_px=1200, height_px=900, scale=2.5, background="white", preset="publication-light")
    variants = base.build_variants(
        {
            "dark": {"background": "dark", "preset": "publication-dark"},
            "transparent": {"background": "transparent"},
        }
    )

    outdir = tmp_path / "figures"
    written = view.export.figure_variants(str(outdir), variants=variants, stem="pocket")

    assert written == [
        str(outdir / "pocket-dark.png"),
        str(outdir / "pocket-transparent.png"),
    ]
    assert (outdir / "pocket-dark.png").read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert (outdir / "pocket-transparent.png").read_bytes() == b"\x89PNG\r\n\x1a\n"
    assert calls[0][1]["preset"] == "publication-dark"
    assert calls[1][1]["preset"] == "current"


def test_figure_spec_build_publication_variants_returns_standard_bundle():
    base = FigureSpec(width_px=1200, height_px=900, scale=2.5, background="white", preset="publication-light")

    variants = base.build_publication_variants(include_current=True)

    assert list(variants) == ["light", "dark", "transparent", "current"]
    assert variants["light"].background == "white"
    assert variants["light"].preset == "publication-light"
    assert variants["dark"].background == "dark"
    assert variants["dark"].preset == "publication-dark"
    assert variants["transparent"].background == "transparent"
    assert variants["current"].background == "current"
    assert variants["current"].preset == "current"


def test_export_figure_publication_set_writes_standard_bundle(monkeypatch, tmp_path: Path):
    view = MolSysView(debug_js=True)
    calls = []

    def fake_export_image(output_filename, **kwargs):
        calls.append((output_filename, kwargs))
        outfile = Path(output_filename)
        outfile.write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(view, "_export_image_impl", fake_export_image)

    base = FigureSpec.from_view(view, width_px=1600, height_px=1200)
    outdir = tmp_path / "publication-set"
    written = view.export.figure_publication_set(
        str(outdir),
        figure_spec=base,
        stem="binding-site",
        include_current=True,
    )

    assert written == [
        str(outdir / "binding-site-light.png"),
        str(outdir / "binding-site-dark.png"),
        str(outdir / "binding-site-transparent.png"),
        str(outdir / "binding-site-current.png"),
    ]
    assert calls[0][1]["preset"] == "publication-light"
    assert calls[1][1]["preset"] == "publication-dark"
    assert calls[2][1]["preset"] == "current"
    assert calls[3][1]["preset"] == "current"
    assert all(call[1]["camera_snapshot"] == base.camera_snapshot for call in calls)


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


def test_set_figure_spec_sends_correct_op():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    spec = FigureSpec(preset="publication-dark", scale=3.0)
    view.set_figure_spec(figure_spec=spec)

    assert len(sent) == 1
    msg = sent[0]
    assert msg["op"] == "set_figure_spec"
    assert msg["figure_preset"] == "publication-dark"
    assert msg["figure_scale"] == 3.0
    assert set(msg["figure_variants"]) == {"light", "dark", "transparent"}


def test_set_figure_spec_stored_and_included_in_export_messages():
    view = MolSysView(debug_js=True)
    sent = []
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    spec = FigureSpec(preset="publication-light", scale=2.0)
    view.set_figure_spec(figure_spec=spec)

    msgs = view._build_export_messages()  # noqa: SLF001
    ops = [m["op"] for m in msgs]
    assert "set_figure_spec" in ops
    figure_msg = next(m for m in msgs if m["op"] == "set_figure_spec")
    assert figure_msg["figure_preset"] == "publication-light"
    assert figure_msg["figure_scale"] == 2.0


def test_set_figure_spec_cleared_after_reset_viewer():
    view = MolSysView(debug_js=True)

    view.set_figure_spec(figure_spec=FigureSpec(preset="publication-light", scale=2.0))
    assert view._current_figure_spec is not None  # noqa: SLF001

    view.reset_viewer()

    # _current_figure_spec is cleared so no figure spec is appended at export time.
    assert view._current_figure_spec is None  # noqa: SLF001
    msgs = view._build_export_messages()  # noqa: SLF001
    # The last message in export should NOT be a set_figure_spec (it was cleared).
    if msgs:
        assert msgs[-1]["op"] != "set_figure_spec"
