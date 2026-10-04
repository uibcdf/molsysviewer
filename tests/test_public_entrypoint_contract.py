"""The uniform public contract validates real input and offers an explicit bypass."""

import inspect
import warnings

import numpy as np
import pytest

import molsysviewer as msv


def test_annotations_add_is_the_only_general_constructor():
    view = msv.demo["dialanine"]
    assert not hasattr(view.annotations, "add_annotation")
    parameters = inspect.signature(view.annotations.add).parameters
    assert parameters["skip_digestion"].default is False
    assert "text" in parameters and "atom_indices" in parameters
    annotation = view.annotations.add("site", atom_indices=[0], tag="site")
    assert annotation is view.annotations["site"]
    with pytest.raises(Exception):
        view.annotations.add("invalid", offset_mode="unknown", atom_indices=[0])


def test_shape_constructor_and_handle_validate_units_and_allow_bypass():
    view = msv.demo["dialanine"]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        shape = view.shapes.add("sphere", center="[0, 0, 0] nm", radius="0.1 nm", tag="s")
        shape.set_radius("0.2 nm")
        shape.set_alpha(0.5)
        assert not any("DigestNotDigested" in type(w.message).__name__ for w in caught)
    with pytest.raises(Exception):
        shape.set_radius("2 ps")
    with pytest.raises(Exception):
        shape.set_alpha(2.0)
    shape.set_alpha(2.0, skip_digestion=True)
    assert view.shapes.records()[0]["options"]["alpha"] == 2.0
    assert shape.get_coordinates(skip_digestion=True) is not None
    view.export_state(skip_digestion=True)
    assert view.history.can_undo(skip_digestion=True)


def test_molecular_query_aliases_keep_boolean_attribute_semantics():
    view = msv.demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="r")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _check_molecular_query_aliases(view, region)
    assert not any("DigestNotDigested" in type(w.message).__name__ for w in caught)


def _check_molecular_query_aliases(view, region):
    for subject in (view.whole, region):
        np.testing.assert_array_equal(
            subject.get(element="group", index=True), subject.get(element="group", group_index=True)
        )
        np.testing.assert_array_equal(
            subject.get(element="group", residue_name=True), subject.get(element="group", group_name=True)
        )
        with pytest.raises(Exception):
            subject.get(element="group", group_index=[0])
        with pytest.raises(Exception):
            subject.get(element="group", name=True, group_name=True)


def test_public_color_normalization_does_not_recurse():
    assert msv.normalize_color("red") == 0xFF0000
    assert msv.normalize_colors(iter(["red", "blue"])) == [0xFF0000, 0x0000FF]
    assert msv.colors.normalize_color("blue", skip_digestion=True) == 0x0000FF
    assert msv.colors.normalize_colors(["red", "blue"]) == [0xFF0000, 0x0000FF]
    with pytest.raises(Exception):
        msv.normalize_color("not-a-color")


def test_named_shape_alias_validates_and_forwards_the_explicit_bypass():
    view = msv.demo["dialanine"]
    signature = inspect.signature(view.shapes.add_links)
    assert "atom_pairs" in signature.parameters and "args" not in signature.parameters
    links = view.shapes.add_links(atom_pairs=[[0, 1]], radius="0.02 nm", tag="links")
    assert links is view.shapes["links"]
    with pytest.raises(Exception):
        view.shapes.add_links(atom_pairs=[[0, 1]], radius="1 ps")


def test_annotation_camera_offset_info_is_detached():
    view = msv.demo["dialanine"]
    view.annotations.add("note", atom_indices=[0], offset=(1, 2, 3), tag="a")
    info = view.annotations.info("a")
    info["offset"][0] = 100
    assert view.annotations.info("a")["offset"][0] == 1


def test_exported_class_methods_validate_and_preserve_figure_overrides():
    view = msv.demo["dialanine"]
    assert msv.Style(representation="cartoon").info(skip_digestion=True)["representation"] == "cartoon"
    figure = msv.FigureSpec.from_view(view, width_px=400, scale=3.0, include_camera=False)
    assert figure.with_overrides().info()["width_px"] == 400
    assert figure.build_variants({"dark": {"background": "dark"}})["dark"].scale == 3.0
    with pytest.raises(Exception):
        msv.FigureSpec.from_view(view, include_camera="yes")
