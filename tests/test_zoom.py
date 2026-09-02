import pytest
from molsysviewer.demo import demo

from molsysviewer import MolSysView


def _recording_view():
    """A viewer on a real system whose outbound messages are captured."""
    view = demo["dialanine"]
    sent: list[dict] = []
    view.widget.send = lambda msg, *a, **k: sent.append(msg)  # type: ignore[attr-defined]
    view._ready = True  # noqa: SLF001
    view._sent = sent  # noqa: SLF001
    return view


def test_zoom_sends_message(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view._molsys = object()

    monkeypatch.setattr("molsysviewer.viewer.camera.msm.select", lambda *_args, **_kwargs: [2, 3, 4])

    view.zoom(
        selection=[2, 3, 4],
        duration="100 ms",
        extra_radius="2.5 angstroms",
        min_radius="0.5 angstroms",
    )

    msg = view._test_message_log[-1]  # noqa: SLF001
    assert msg["op"] == "zoom"
    assert msg["atom_indices"] == [2, 3, 4]
    assert msg["options"] == {"duration_ms": 100, "extra_radius": 2.5, "min_radius": 0.5}


def test_zoom_requires_loaded_system():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        view.zoom(selection="all")


def test_focus_on_object_agrees_with_the_object_s_own_focus():
    """Two paths to the same camera move, and they used to disagree by a factor of ten.

    `camera.focus_on_object` is digested, so its `extra_radius` and `duration` arrive as
    quantities; the object's own `focus()` is not, and read the same arguments as plain
    numbers -- `float(extra_radius)` added to a radius in **nanometres**, while the
    digester read a bare number as **angstroms**. `focus_on_object` on a shape therefore
    raised `DimensionalityError` with its own default argument, and the paths that did not
    raise applied the wrong scale silently (uibcdf/molsysviewer#69).

    This asserts they now produce the same message, which is the only way to state
    "these two agree" without repeating the arithmetic in the test.
    """
    from molsysviewer._pyunitwizard import puw

    view = _recording_view()
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="s1",
    )

    view._sent.clear()  # noqa: SLF001
    view.camera.focus_on_object("s1", kind="shape")
    through_camera = [m for m in view._sent if m.get("op") == "zoom_to_position"][-1]  # noqa: SLF001

    view._sent.clear()  # noqa: SLF001
    shape.focus()
    through_object = [m for m in view._sent if m.get("op") == "zoom_to_position"][-1]  # noqa: SLF001

    assert through_camera == through_object


def test_a_camera_padding_without_units_is_refused():
    """The units policy, applied to the argument that was breaking it.

    `extra_radius` accepted a quantity of any dimensionality (seconds standardized to
    picoseconds), read the string "4.0" as four *radians*, and returned a non-numeric
    string unchanged. It is a length; requiring the unit is what keeps the nm/angstrom
    factor of ten from being applied in silence.
    """
    from molsysviewer._pyunitwizard import puw

    view = _recording_view()

    from molsysviewer._private.exceptions import ArgumentError

    for refused in (2.5, "2.5", "not a length", puw.quantity(3.0, "seconds")):
        with pytest.raises(ArgumentError):
            view.zoom(selection=[2, 3, 4], extra_radius=refused)

    view.zoom(selection=[2, 3, 4], extra_radius="2.5 angstroms")
