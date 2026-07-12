from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


def _view():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None
    return view


def test_same_tag_in_two_scene_object_domains_mutates_only_target_domain():
    view = _view()
    shape = view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), tag="site1")
    annotation = view.annotations.add_annotation(
        "site",
        atom_indices=[0],
        tag="site1",
    )

    shape.hide(skip_digestion=True)

    assert view.shapes["site1"] is shape
    assert view.annotations["site1"] is annotation
    assert view.layers["site1"].members == {
        ("shape", "site1"): shape,
        ("annotation", "site1"): annotation,
    }
    assert shape._hidden is True  # noqa: SLF001
    assert annotation._hidden is False  # noqa: SLF001


def test_renaming_shape_does_not_rewrite_same_tag_annotation_history():
    view = _view()
    shape = view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), tag="site1")
    view.annotations.add_annotation("site", atom_indices=[0], tag="site1")

    shape.set_tag("sphere1", skip_digestion=True)

    assert any(record.get("tag") == "site1" for record in view._annotation_history)  # noqa: SLF001
    assert all(record.get("tag") != "site1" for record in view._shape_history)  # noqa: SLF001


def test_renaming_shape_does_not_rewrite_same_tag_annotation_layer_tag():
    # A rename rewrites `options["layer_tag"]` across the histories, which is a
    # different channel from the record's `tag`. Kind-blind rewriting corrupts the
    # namesake's layer membership — and it does so silently: the replay, the HTML
    # export and the popup all read these histories.
    view = _view()
    shape = view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), tag="site1")
    view.annotations.add_annotation("site", atom_indices=[0], tag="site1")

    shape.set_tag("sphere1", skip_digestion=True)

    annotation_layer_tags = [
        record.get("options", {}).get("layer_tag") for record in view._annotation_history  # noqa: SLF001
    ]
    shape_layer_tags = [
        record.get("options", {}).get("layer_tag") for record in view._shape_history  # noqa: SLF001
    ]
    assert annotation_layer_tags == ["site1"], "the shape's rename bled into the annotation"
    assert shape_layer_tags == ["sphere1"], "the shape's own layer_tag was not rewritten"
