"""Tests for view.show_orientation_axes() and view.show_best_fit_plane()."""
from molsysviewer import demo


def test_show_orientation_axes_creates_region():
    view = demo["dialanine"]

    region = view.show_orientation_axes()

    assert region is not None
    assert region.tag.startswith("orientation-")
    assert region.tag in view.regions


def test_show_orientation_axes_sends_set_region_representation():
    view = demo["dialanine"]

    view.show_orientation_axes(tag="axes-test")

    ops = [m for m in view._message_history if m.get("op") == "set_region_representation"]  # noqa: SLF001
    assert any(m.get("representation") == "orientation" and m.get("tag") == "axes-test" for m in ops)


def test_show_orientation_axes_custom_tag():
    view = demo["dialanine"]

    region = view.show_orientation_axes(tag="my-axes")

    assert region.tag == "my-axes"
    assert "my-axes" in view.regions


def test_show_orientation_axes_alpha_forwarded():
    view = demo["dialanine"]

    view.show_orientation_axes(tag="axes-alpha", alpha=0.4)

    ops = [m for m in view._message_history  # noqa: SLF001
           if m.get("op") == "set_region_representation" and m.get("tag") == "axes-alpha"]
    assert len(ops) == 1
    assert ops[0].get("params", {}).get("alpha") == 0.4


def test_show_orientation_axes_sets_representation_on_region():
    view = demo["dialanine"]

    region = view.show_orientation_axes(tag="axes-repr")

    assert region.representation == "orientation"


def test_show_orientation_axes_region_can_be_hidden_and_deleted():
    view = demo["dialanine"]

    region = view.show_orientation_axes(tag="axes-lifecycle")
    region.hide()
    region.show()
    region.delete()

    assert "axes-lifecycle" not in view.regions


def test_show_best_fit_plane_creates_region():
    view = demo["dialanine"]

    region = view.show_best_fit_plane()

    assert region is not None
    assert region.tag.startswith("plane-")
    assert region.tag in view.regions


def test_show_best_fit_plane_sends_set_region_representation():
    view = demo["dialanine"]

    view.show_best_fit_plane(tag="plane-test")

    ops = [m for m in view._message_history if m.get("op") == "set_region_representation"]  # noqa: SLF001
    assert any(m.get("representation") == "plane" and m.get("tag") == "plane-test" for m in ops)


def test_show_best_fit_plane_custom_tag():
    view = demo["dialanine"]

    region = view.show_best_fit_plane(tag="my-plane")

    assert region.tag == "my-plane"
    assert "my-plane" in view.regions


def test_show_best_fit_plane_alpha_forwarded():
    view = demo["dialanine"]

    view.show_best_fit_plane(tag="plane-alpha", alpha=0.6)

    ops = [m for m in view._message_history  # noqa: SLF001
           if m.get("op") == "set_region_representation" and m.get("tag") == "plane-alpha"]
    assert len(ops) == 1
    assert ops[0].get("params", {}).get("alpha") == 0.6


def test_show_best_fit_plane_sets_representation_on_region():
    view = demo["dialanine"]

    region = view.show_best_fit_plane(tag="plane-repr")

    assert region.representation == "plane"


def test_show_best_fit_plane_region_can_be_hidden_and_deleted():
    view = demo["dialanine"]

    region = view.show_best_fit_plane(tag="plane-lifecycle")
    region.hide()
    region.show()
    region.delete()

    assert "plane-lifecycle" not in view.regions


def test_orientation_and_plane_do_not_pollute_allowed_representations():
    """Verify these helpers stay out of the public representation catalog."""
    from molsysviewer.viewer.representations import ALLOWED_REPRESENTATIONS

    assert "orientation" not in ALLOWED_REPRESENTATIONS
    assert "plane" not in ALLOWED_REPRESENTATIONS


def test_orientation_axes_and_plane_coexist_on_same_view():
    view = demo["dialanine"]

    r1 = view.show_orientation_axes(tag="axes-co")
    r2 = view.show_best_fit_plane(tag="plane-co")

    assert "axes-co" in view.regions
    assert "plane-co" in view.regions
    assert r1.representation == "orientation"
    assert r2.representation == "plane"
