import pytest

from molsysviewer import MolSysView


def test_zoom_sends_message(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view._molsys = object()

    monkeypatch.setattr("molsysviewer.viewer.msm.select", lambda *_args, **_kwargs: [2, 3, 4])

    view.zoom(selection=[2, 3, 4], duration_ms=100, extra_radius=2.5, min_radius=0.5)

    msg = view._pending_messages[-1]  # noqa: SLF001
    assert msg["op"] == "zoom"
    assert msg["atom_indices"] == [2, 3, 4]
    assert msg["options"] == {"duration_ms": 100, "extra_radius": 2.5, "min_radius": 0.5}


def test_zoom_requires_loaded_system():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        view.zoom(selection="all")
