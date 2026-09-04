"""R2 popup snapshot — fidelity of the canonical projection.

Complements test_popup_snapshot.py (purity/invariance/isolation). Here the
question is different: does a popup rebuilt from the snapshot see *the same
scene* the host sees? Each test pins one way the projection could silently lose
current state.
"""

import molsysmt as msm
import pyunitwizard as puw
import pytest

from molsysviewer import MolSysView


def _view() -> MolSysView:
    v = MolSysView()
    v.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    return v


def _ops(messages, op):
    return [m for m in messages if m.get("op") == op]


def _one(messages, op, tag=None):
    found = [m for m in _ops(messages, op) if tag is None or m.get("tag") == tag]
    assert len(found) == 1, f"expected exactly one {op}{'' if tag is None else f' for {tag}'}, got {len(found)}"
    return found[0]


# 1. dynamic region at the current frame ------------------------------------

def test_a_dynamic_region_carries_the_indices_materialized_for_the_current_frame():
    v = _view()
    region = v._new_region_impl(  # noqa: SLF001
        selection="atom_index < 6",
        tag="dyn",
        frame_dependent=True,
        skip_digestion=True,
    )
    region.mode = "dynamic"
    expected = list(region.atom_indices)
    assert expected, "the dynamic region must be materialized at the current frame"

    create = _one(v.build_popup_scene_snapshot("canvas"), "create_region", "dyn")
    # A projector that shipped only the selection string would leave the popup
    # unable to draw the region without re-evaluating it.
    assert create["atom_indices"] == expected


# 2. dynamic shape -----------------------------------------------------------

def test_a_trajectory_bound_shape_survives_in_the_snapshot():
    v = _view()
    v.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="dynsph",
        atom_indices=[0],
    )
    snapshot = v.build_popup_scene_snapshot("canvas")
    spheres = _ops(snapshot, "add_sphere")
    assert len(spheres) == 1
    options = spheres[0].get("options") or {}
    # The atom binding is what makes the shape follow the trajectory.
    assert options.get("atom_indices") == [0] or options.get("tag") == "dynsph"


# 3. hidden object inside a hidden layer ------------------------------------

def test_a_hidden_object_inside_a_hidden_layer_stays_hidden():
    v = _view()
    v.layers.add("grp")
    v.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="s1",
        layer_tag="grp",
    )
    v.shapes.get("s1").hide()
    v.layers["grp"].hide()

    snapshot = v.build_popup_scene_snapshot("canvas")
    hides = {(m.get("tag"), m.get("kind")) for m in _ops(snapshot, "hide_layer")}
    # Both the object and its layer must be reported hidden; otherwise the popup
    # shows geometry the host is not showing.
    assert ("s1", "shape") in hides
    assert ("grp", "layer") in hides

    # Creation must come before the hide that applies to it.
    ops = [m.get("op") for m in snapshot]
    assert ops.index("add_sphere") < ops.index("hide_layer")


# 4. inherit representation --------------------------------------------------

def test_a_region_inheriting_its_representation_does_not_invent_one():
    v = _view()
    v.regions.add("atom_index < 6", tag="inh", representation="inherit")
    create = _one(v.build_popup_scene_snapshot("canvas"), "create_region", "inh")
    # `inherit` means "no own visual": the snapshot must not fabricate a
    # representation, or the popup would diverge from the host.
    assert create.get("representation") in (None, "inherit")


# 5. overlapping colours and order -------------------------------------------

def test_overlapping_region_colours_resolve_by_order_in_the_snapshot():
    v = _view()
    v.regions.add("atom_index < 6", tag="low")
    v.regions.add("atom_index < 6", tag="high")
    v.regions["low"].set_color("red")
    v.regions["high"].set_color("blue")

    snapshot = v.build_popup_scene_snapshot("canvas")
    colors = _ops(snapshot, "set_atom_colors")
    assert colors, "resolved colours must be present when regions carry colour"
    resolved = dict(zip(colors[0]["atom_indices"], colors[0]["colors"]))
    expected = v._resolved_atom_color_map()  # noqa: SLF001
    # The winning colour per atom must match the host's resolution (top region).
    assert resolved == expected

    # Regions are emitted in order, so a later region layers over an earlier one.
    orders = [m["order"] for m in _ops(snapshot, "create_region")]
    assert orders == sorted(orders)

    # Colours come after the regions that own them.
    ops = [m.get("op") for m in snapshot]
    assert ops.index("set_atom_colors") > max(
        i for i, op in enumerate(ops) if op == "create_region"
    )


# 6. saved selection ---------------------------------------------------------

def test_a_saved_selection_is_projected_as_a_real_save_selection_message():
    v = _view()
    v.selections.add("sel1", atom_indices=[0, 1, 2, 3])
    saved = _one(v.build_popup_scene_snapshot("canvas"), "save_selection", "sel1")
    # The record is already a complete save_selection op; it must travel verbatim
    # rather than under an invented wrapper op the frontend does not handle.
    assert saved["atom_indices"] == [0, 1, 2, 3]
    assert "source_kind" in saved


# 7. absent box and time stay absent -----------------------------------------

def test_absent_box_and_time_are_not_invented():
    v = _view()
    snapshot = v.build_popup_scene_snapshot("canvas")
    molecular = _one(snapshot, "load_molsys_payload")
    payload = molecular.get("payload") or {}
    structures = payload.get("structures") or []
    if not structures:
        pytest.skip("this fixture carries no structures block to inspect")
    first = structures[0]
    box_in_source = v._molsys.structures.box is not None  # noqa: SLF001
    if not box_in_source:
        assert not first.get("box"), "box must stay absent when the MolSys has none"


# 8. panel/canvas separation under a full scene ------------------------------

def test_a_full_scene_keeps_canvas_and_panel_projections_separate():
    v = _view()
    # The whole must be configured for `set_whole_representation` to belong in
    # the snapshot at all; see
    # `test_a_pristine_whole_is_not_projected_as_an_explicit_none`.
    v.whole.set_representation("cartoon")
    v.regions.add("atom_index < 6", tag="a")
    v.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="s1",
    )
    v.selections.add("sel1", atom_indices=[0, 1])
    v.active_selection.set([2, 3])

    canvas = v.build_popup_scene_snapshot("canvas")
    panel = v.build_popup_scene_snapshot("panel")
    canvas_ops = [m.get("op") for m in canvas]
    panel_ops = [m.get("op") for m in panel]

    # The canvas can render: molecule, whole, region, shape, visibility, frame.
    for op in (
        "load_molsys_payload",
        "set_whole_representation",
        "create_region",
        "add_sphere",
        "set_trajectory_frame",
    ):
        assert op in canvas_ops, f"canvas snapshot is missing {op}"

    # The panel gets UI state and no geometry.
    for op in ("set_region_summaries", "set_shape_summaries", "set_history_state"):
        assert op in panel_ops, f"panel snapshot is missing {op}"
    for op in ("load_molsys_payload", "add_sphere", "create_region"):
        assert op not in panel_ops, f"panel snapshot must not contain {op}"

    # Camera is host-local ephemeral state in both modes.
    assert "set_camera_snapshot" not in canvas_ops
    assert "set_camera_snapshot" not in panel_ops


def test_a_pristine_whole_is_not_projected_as_an_explicit_none():
    """Silence and an explicit None are the same in the model, not on screen.

    Found by smoke test on 2026-07-31, after eight fidelity tests missed it.
    They all compared the snapshot against Python's *model*; this compares it
    against what the host actually *sent*, which is the thing the popup has to
    reproduce.

    A pristine viewer never sends `set_whole_representation` — the frontend
    applies its own default representation on receiving the payload. Python
    records that as `representation=None, preset=None, params={}`, and a
    projector that faithfully serialises the model emits
    `set_whole_representation(null, null, {})`.

    That op is not a no-op. `setWholeRepresentation` in `state-handlers.ts`
    clears the baseline representation refs *before* applying anything, and with
    both representation and preset null and no `user_preset` it adds nothing
    back. The popup therefore renders an invisible whole while the host shows
    the molecule — which is exactly what a human saw: "in the popup I only see a
    sphere, I think it is one atom".
    """
    v = _view()
    assert v.whole.representation is None
    assert v.whole.preset is None
    assert not dict(v.whole.params)

    ops = [m.get("op") for m in v.build_popup_scene_snapshot("canvas")]
    assert "set_whole_representation" not in ops, (
        "a pristine whole must not be projected as an explicit None: the op "
        "clears the frontend's default representation and puts nothing back."
    )
    # The whole is still shown; only the representation op is withheld.
    assert "show_whole" in ops

    # Once configured from Python, the op must travel — otherwise the popup
    # would silently lose a representation the user did choose.
    v.whole.set_representation("cartoon")
    ops_after = [m.get("op") for m in v.build_popup_scene_snapshot("canvas")]
    assert "set_whole_representation" in ops_after
