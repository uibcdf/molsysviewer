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
    # Whole visibility always travels. The representation op travels only when
    # the whole was actually configured — projecting a pristine whole as an
    # explicit None clears the frontend's default and renders nothing. See
    # test_popup_snapshot_fidelity.py::test_a_pristine_whole_is_not_projected_as_an_explicit_none
    assert {"show_whole", "hide_whole"} & ops
    assert "set_whole_representation" not in ops
    view.whole.set_representation("cartoon")
    ops_configured = {m.get("op") for m in view.build_popup_scene_snapshot("canvas")}
    assert "set_whole_representation" in ops_configured


def _summary_ops_the_view_can_push(view) -> set[str]:
    """Derive the summary ops from the view's own `_sync_*_runtime` methods.

    Discovered rather than listed on purpose. `scene_contracts.md` Contract S1
    warns that a summary is `_send_runtime_only`, so a frontend that attaches
    later depends on canonical panel coverage rather than replay. A hardcoded
    list cannot notice a *new* domain: it would stay green while that panel
    section rendered blank on popout. This is the same shape as
    the digester-caller and Qt-manifest drifts: where two things must agree and
    nothing mechanically forces them to, they drift in silence.

    Each method is *invoked* and the op it actually emits is captured, rather
    than derived from its name: `_sync_addons_runtime` emits
    `set_addon_runtime_summary`, so a name-based rule would invent an op that
    does not exist and fail for the wrong reason.
    """
    ops: set[str] = set()
    original = view.widget.send
    was_ready = view._ready
    view._ready = True  # otherwise the sends are queued, not delivered
    for name in sorted(dir(type(view))):
        if not (name.startswith("_sync_") and name.endswith("_runtime")):
            continue
        captured: list[dict] = []
        # `captured` is rebound every iteration, so the lambda binds it as a default
        # rather than closing over the loop variable.
        view.widget.send = (
            lambda msg, *a, _c=captured, **k: _c.append(msg)
        )  # type: ignore[assignment]
        try:
            getattr(view, name)()
        finally:
            view.widget.send = original  # type: ignore[assignment]
        ops.update(m["op"] for m in captured if isinstance(m, dict) and "op" in m)
    view._ready = was_ready
    return ops


def test_every_summary_projection_reaches_the_panel_snapshot():
    view = _populated_view()
    ops = {m.get("op") for m in view.build_popup_scene_snapshot("panel")}
    expected = _summary_ops_the_view_can_push(view)
    assert expected, "no summary sync methods discovered — the derivation broke"
    for summary_op in sorted(expected):
        assert summary_op in ops, (
            f"panel snapshot is missing {summary_op}. Every "
            f"_sync_<domain>_runtime the view can push must also be projected "
            f"into the popup panel snapshot, or that section renders blank."
        )


def test_panel_snapshot_carries_authoritative_trajectory_state():
    view = _view()
    view.player.go_to_structure(3, skip_digestion=True)
    summary = next(
        message
        for message in view.build_popup_scene_snapshot("panel")
        if message.get("op") == "set_trajectory_summary"
    )

    assert summary == {
        "op": "set_trajectory_summary",
        "frame": 3,
        "frame_count": view.player.n_structures,
        "is_playing": False,
        "fps": 30,
        "step": 1,
        "mode": "loop",
        "direction": "forward",
    }


def test_every_summary_projection_is_resent_on_ready():
    """The other late-attaching frontend: a fresh canvas that emits `ready`.

    Contract S1 is outcome-based: the embedded-runtime profile must contain
    every summary. Derived the same way as above so a new domain cannot be
    added to one path and forgotten in the other.
    """
    view = _populated_view()
    sent: list[dict] = []
    view.widget.send = lambda msg, *a, **k: sent.append(msg)  # type: ignore[assignment]

    view._handle_frontend_event({"event": "ready"})

    ops = {m.get("op") for m in sent if isinstance(m, dict)}
    for summary_op in sorted(_summary_ops_the_view_can_push(view)):
        assert summary_op in ops, (
            f"the ready projection does not include {summary_op}; a freshly "
            f"attached frontend would render that panel section empty."
        )


def test_addon_context_items_reach_the_panel_without_breaking_purity():
    """The last panel projection the projector could not carry.

    `refresh_context_items` computes *and* pushes, so using it would have made
    the projector send. `build_context_items` is the pure half, split out for
    exactly this.
    """
    view = _populated_view()
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]
    view._ready = True  # noqa: SLF001

    ops = {m.get("op") for m in view.build_popup_scene_snapshot("panel")}
    assert "set_addon_context_items" in ops
    assert sent == [], "building the snapshot must not send anything"


def test_the_pure_builder_does_not_push_to_the_frontend():
    view = _populated_view()
    sent: list = []
    view.widget.send = lambda content, buffers=None: sent.append(content)  # type: ignore[assignment]
    view._ready = True  # noqa: SLF001

    items = view.addons.build_context_items({"atom_indices": [0, 1]})
    assert isinstance(items, list)
    assert sent == [], "build_context_items must be pure; refresh_context_items is the one that pushes"
