import pytest

from molsysviewer import MolSysView, pyunitwizard as puw
from molsysviewer.layers import LayersManager
from molsysviewer.demo import demo


CANONICAL_MANAGER_METHODS = (
    "add",
    "tags",
    "count",
    "records",
    "info",
    "contains",
    "get",
    "delete",
    "clear",
    "set_tag",
)


def test_scene_managers_expose_canonical_callable_surface():
    view = MolSysView()

    for manager in (
        view.regions,
        view.selections,
        view.shapes,
        view.annotations,
        view.measurements,
        view.layers,
    ):
        for name in CANONICAL_MANAGER_METHODS:
            assert callable(getattr(manager, name)), f"{type(manager).__name__}.{name} is not callable"


def test_info_of_a_single_tag_returns_a_dict_in_every_domain():
    view = demo["dialanine"]
    view.regions.add(atom_indices=[0], tag="r")
    view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), tag="s")
    view.annotations.add("site", atom_indices=[0], tag="a")
    view.measurements.add("distance", [0], [1], tag="d")
    view.layers.add("L", skip_digestion=True)

    for manager, tag in (
        (view.regions, "r"),
        (view.shapes, "s"),
        (view.annotations, "a"),
        (view.measurements, "d"),
        (view.layers, "L"),
    ):
        assert isinstance(manager.info(tag), dict)
        assert isinstance(manager.info(), list)


def test_info_of_a_missing_tag_raises_valueerror_in_every_domain():
    view = MolSysView()

    for manager in (
        view.regions,
        view.shapes,
        view.annotations,
        view.measurements,
        view.layers,
    ):
        with pytest.raises(ValueError):
            manager.info("does-not-exist")


def test_layers_manager_add_preserves_kind_and_explicit_meta():
    view = MolSysView()

    layer = view.layers.add("analysis", kind="shape", meta={"owner": "test"}, skip_digestion=True)

    assert view.layers["analysis"] is layer
    assert isinstance(view.layers, LayersManager)
    assert isinstance(view.layers, dict)
    assert layer.kind == "shape"
    assert layer.meta == {"owner": "test"}
    assert view.layers.records(skip_digestion=True) == [
        {
            "tag": "analysis",
            "kind": "shape",
            "meta": {"owner": "test"},
            "provenance": "user",
            "visible": True,
            "n_members": 0,
        }
    ]

    view.layers.clear("analysis", skip_digestion=True)
    assert view.layers.count(skip_digestion=True) == 0


def test_user_layer_survives_becoming_empty_but_auto_layer_does_not():
    view = demo["dialanine"]
    user_layer = view.layers.add("analysis", skip_digestion=True)
    annotation = view.annotations.add("site", atom_indices=[0], tag="site1")

    user_layer.attach(annotation)
    user_layer.detach(annotation)

    assert view.layers.get("analysis") is user_layer
    assert user_layer.provenance == "user"

    annotation.delete(skip_digestion=True)
    assert view.layers.get("site1") is None

    explicitly_grouped = view.annotations.add(
        "grouped",
        atom_indices=[0],
        tag="site2",
        layer_tag="named-group",
    )
    explicitly_grouped.delete(skip_digestion=True)
    assert view.layers["named-group"].provenance == "user"
    assert view.layers["named-group"].members == {}


def test_layers_manager_add_rejects_misspelled_keyword():
    view = MolSysView()

    with pytest.raises(TypeError):
        view.layers.add("analysis", kidn="shape", skip_digestion=True)


def test_layers_manager_rejects_duplicate_tag_within_its_domain():
    view = MolSysView()
    view.layers.add("analysis", skip_digestion=True)

    with pytest.raises(ValueError):
        view.layers.add("analysis", skip_digestion=True)


def test_retired_layer_and_shape_aliases_are_absent():
    view = MolSysView()

    assert not hasattr(view, "new_layer")
    assert not hasattr(view.shapes, "add_gaussian_isosurface")
    assert not hasattr(view.shapes.blobs, "add_gaussian_isosurface")


def test_shapes_manager_lifecycle_targets_only_namesake_shape():
    view = demo["dialanine"]
    shape = view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site1",
    )
    annotation = view.annotations.add_annotation("site", atom_indices=[0], tag="site1")

    view.shapes.hide("site1", skip_digestion=True)
    assert shape._hidden is True  # noqa: SLF001
    assert annotation._hidden is False  # noqa: SLF001

    view.shapes.show("site1", skip_digestion=True)
    view.shapes.set_tag("site1", "sphere1", skip_digestion=True)
    assert view.shapes.get("sphere1") is shape
    assert view.annotations.get("site1") is annotation

    view.shapes.delete("sphere1", skip_digestion=True)
    assert view.shapes.get("sphere1") is None
    assert view.annotations.get("site1") is annotation


def test_shapes_manager_count_records_and_generic_add_are_live():
    view = MolSysView()

    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="sphere1",
        skip_digestion=True,
    )

    assert view.shapes.count(skip_digestion=True) == 1
    assert view.shapes.records(skip_digestion=True)[0]["options"]["tag"] == "sphere1"
    assert view.shapes.get("sphere1", skip_digestion=True) is shape


def test_annotations_and_measurements_generic_add_dispatch_to_real_constructors():
    view = demo["dialanine"]

    annotation = view.annotations.add("site", atom_indices=[0], tag="site1")
    measurement = view.measurements.add("distance", [0], [1], tag="distance1")

    assert view.annotations.get("site1") is annotation
    assert view.measurements.get("distance1") is measurement
