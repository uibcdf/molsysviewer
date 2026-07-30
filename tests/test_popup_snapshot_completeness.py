"""R2 guard: the canonical projector must not silently go stale.

`popup_snapshot.py` regenerates ops for every kind of live scene content. Nothing
links it to the registries at compile time, so a new scene-object kind (or a
newly registered object that the projector forgets) would be dropped from popup
bootstrap in silence. This sweep turns that into a red test.
"""

import molsysmt as msm
import pyunitwizard as puw

from molsysviewer import MolSysView


def _view() -> MolSysView:
    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    return view


def _populated_view() -> MolSysView:
    """One live object of every kind the registries can hold."""
    view = _view()
    view.regions.add("atom_index < 6", tag="reg")
    view.layers.add("lay")
    view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="shp",
    )
    view.annotations.add_annotation("note", atom_indices=[0], tag="ann", skip_digestion=True)
    view.measurements.add_distance(
        selection_a=[0], selection_b=[1], tag="dist", skip_digestion=True
    )
    view.selections.add("sel", atom_indices=[0, 1])
    return view


def test_every_live_scene_object_appears_in_the_canvas_snapshot():
    view = _populated_view()
    snapshot = view.build_popup_scene_snapshot("canvas")
    serialized = repr(snapshot)

    missing = []
    for kind, tag in view._scene_objects:  # noqa: SLF001
        # Every live scene object must be reconstructible from the snapshot; its
        # tag appearing somewhere in the projection is the minimal evidence.
        if tag not in serialized:
            missing.append((kind, tag))
    assert not missing, f"canvas snapshot drops live scene objects: {missing}"


def test_every_live_registry_is_represented_in_the_canvas_snapshot():
    view = _populated_view()
    ops = {m.get("op") for m in view.build_popup_scene_snapshot("canvas")}

    # Each registry that holds live content must contribute to the projection.
    assert view._regions and "create_region" in ops  # noqa: SLF001
    assert list(view.layers.values()) and "create_layer" in ops
    assert view.selections.records(skip_digestion=True) and "save_selection" in ops
    assert view._current_molecular_projection is not None  # noqa: SLF001
    assert "load_molsys_payload" in ops
    # Whole is two ops (there is no whole-colour op in the protocol).
    assert "set_whole_representation" in ops
    assert {"show_whole", "hide_whole"} & ops


def test_every_summary_projection_reaches_the_panel_snapshot():
    view = _populated_view()
    ops = {m.get("op") for m in view.build_popup_scene_snapshot("panel")}
    # The panel is driven entirely by summaries; a new summary kind that the
    # projector forgets would leave that panel section blank on popout.
    for summary_op in (
        "set_region_summaries",
        "set_layer_summaries",
        "set_annotation_summaries",
        "set_measurement_summaries",
        "set_shape_summaries",
        "set_section_summaries",
        "set_whole_summary",
    ):
        assert summary_op in ops, f"panel snapshot is missing {summary_op}"
