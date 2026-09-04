from __future__ import annotations

import warnings


from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _region(view, indices, tag, **kw):
    return view.regions.add(atom_indices=list(indices), tag=tag, skip_digestion=True, **kw)


def test_set_layer_creates_group_and_registers_membership():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    assert r.layer is None

    r.set_layer("site", skip_digestion=True)
    assert r.layer == "site"
    # The layer group now exists and lists the region among its members.
    assert "site" in view.layers
    layer = view.layers["site"]
    assert "A" in layer.regions
    assert ("region", "A") in layer.members


def test_layer_hide_and_show_apply_to_member_regions():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    assert r.visible is True

    view.layers["site"].hide(skip_digestion=True)
    assert r.visible is False
    view.layers["site"].show(skip_digestion=True)
    assert r.visible is True


def test_layer_delete_removes_member_regions():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)

    view.layers["site"].delete(skip_digestion=True)
    assert "A" not in view.regions
    assert "site" not in view.layers


def test_layer_toggle_of_visualless_region_is_quiet():
    view = _mute(demo["dialanine"])
    # A region without its own representation (Contract A).
    r = _region(view, [0, 1, 2], "A")
    assert r.representation is None
    r.set_layer("site", skip_digestion=True)

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning would fail the test
        view.layers["site"].hide(skip_digestion=True)
        view.layers["site"].show(skip_digestion=True)
    assert r.visible is True


def test_moving_a_region_preserves_the_emptied_user_layer():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("first", skip_digestion=True)
    assert "first" in view.layers

    r.set_layer("second", skip_digestion=True)
    assert r.layer == "second"
    assert "first" in view.layers
    assert view.layers["first"].provenance == "user"
    assert view.layers["first"].members == {}
    assert "second" in view.layers


def test_deleting_a_region_preserves_its_empty_user_layer():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    r.delete(skip_digestion=True)
    assert view.layers["site"].provenance == "user"
    assert view.layers["site"].members == {}


def test_remove_from_layer_detaches_and_preserves_user_layer():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    r.remove_from_layer(skip_digestion=True)
    assert r.layer is None
    assert view.layers["site"].provenance == "user"
    assert view.layers["site"].members == {}


def test_layer_membership_survives_a_state_round_trip():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    state = view.export_state()
    assert next(rec for rec in state["regions"] if rec["tag"] == "A")["layer"] == "site"

    fresh = _mute(demo["dialanine"])
    fresh.import_state(state)
    assert fresh.regions["A"].layer == "site"
    assert "A" in fresh.layers["site"].regions


def test_set_layer_is_undoable():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    assert view.regions["A"].layer == "site"

    view.history.undo()
    assert view.regions["A"].layer is None
    assert "site" not in view.layers


def test_set_layer_accepts_a_layer_object():
    view = _mute(demo["dialanine"])
    layer = view.layers.add("site")
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer(layer, skip_digestion=True)
    assert r.layer == "site"
    assert "A" in view.layers["site"].regions


def test_region_summary_runtime_record_carries_layer():
    view = _mute(demo["dialanine"])
    sent = []
    view._send_runtime_only = lambda m: sent.append(m)  # noqa: SLF001
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    summaries = [m for m in sent if m.get("op") == "set_region_summaries"]
    record = next(rec for rec in summaries[-1]["regions"] if rec["tag"] == "A")
    assert record["layer"] == "site"


def _action(view, action, **content):
    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action", "action": action, **content,
    })


def test_context_action_assigns_and_detaches_region_layer():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "A", representation="cartoon")
    view.layers.add("site", skip_digestion=True)
    _action(view, "add_member_to_layer", layer="site", member_kind="region", member_tag="A")
    assert view.regions["A"].layer == "site"
    _action(view, "remove_member_from_layer", layer="site", member_kind="region", member_tag="A")
    assert view.regions["A"].layer is None
    assert view.layers["site"].provenance == "user"


def test_context_action_set_layer_visibility_and_delete_contents():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "A", representation="cartoon")
    view.layers.add("site", skip_digestion=True)
    _action(view, "add_member_to_layer", layer="site", member_kind="region", member_tag="A")

    _action(view, "set_layer_visibility", tag="site", hidden=True)
    assert view.regions["A"].visible is False
    _action(view, "set_layer_visibility", tag="site")  # toggle back
    assert view.regions["A"].visible is True

    _action(view, "delete_layer_and_contents", tag="site")
    assert "A" not in view.regions
    assert "site" not in view.layers


def test_context_action_remove_region_from_layer():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "A", representation="cartoon")
    view.layers.add("site", skip_digestion=True)
    _action(view, "add_member_to_layer", layer="site", member_kind="region", member_tag="A")
    _action(view, "remove_member_from_layer", layer="site", member_kind="region", member_tag="A")
    assert view.regions["A"].layer is None


def test_layer_summary_contains_only_intrinsic_state_and_ready_projects_it():
    view = _mute(demo["dialanine"])
    view.layers.add("empty", skip_digestion=True)
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # noqa: SLF001

    view._sync_layer_summaries_runtime()  # noqa: SLF001
    assert sent[-1] == {
        "op": "set_layer_summaries",
        "layers": [{"tag": "empty", "provenance": "user", "hidden": False}],
    }

    sent.clear()
    view.widget.send = lambda message: sent.append(dict(message))  # type: ignore[method-assign]
    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001
    assert any(message.get("op") == "set_layer_summaries" for message in sent)


def test_panel_assigns_a_region_through_the_region_membership_channel():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "shared", representation="cartoon")
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="shared",
        skip_digestion=True,
    )
    view.layers.add("site", skip_digestion=True)

    _action(
        view,
        "add_member_to_layer",
        layer="site",
        member_kind="region",
        member_tag="shared",
    )

    assert view.regions["shared"].layer == "site"
    assert view.shapes.get("shared", skip_digestion=True).layer_tag == "shared"


def test_panel_removes_same_tag_members_by_domain_without_touching_namesake():
    view = _mute(demo["dialanine"])
    region = _region(view, [0, 1, 2], "shared", representation="cartoon")
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="shared",
        skip_digestion=True,
    )
    region.set_layer("site", skip_digestion=True)
    shape.set_layer_tag("site", skip_digestion=True)

    _action(
        view,
        "remove_member_from_layer",
        layer="site",
        member_kind="shape",
        member_tag="shared",
    )

    assert view.regions["shared"].layer == "site"
    assert view.shapes.get("shared", skip_digestion=True).layer_tag == "shared"


def test_ungroup_layer_preserves_mixed_members_and_dissolves_group():
    view = _mute(demo["dialanine"])
    region = _region(view, [0, 1, 2], "A", representation="cartoon")
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="marker",
        skip_digestion=True,
    )
    region.set_layer("site", skip_digestion=True)
    shape.set_layer_tag("site", skip_digestion=True)

    _action(view, "ungroup_layer", tag="site")

    assert "A" in view.regions
    assert view.shapes.get("marker", skip_digestion=True) is shape
    assert view.regions["A"].layer is None
    assert view.shapes.get("marker", skip_digestion=True).layer_tag == "marker"
    assert "site" not in view.layers


def test_delete_layer_and_contents_destroys_mixed_members():
    view = _mute(demo["dialanine"])
    region = _region(view, [0, 1, 2], "A", representation="cartoon")
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="marker",
        skip_digestion=True,
    )
    region.set_layer("site", skip_digestion=True)
    shape.set_layer_tag("site", skip_digestion=True)

    _action(view, "delete_layer_and_contents", tag="site")

    assert "A" not in view.regions
    assert view.shapes.get("marker", skip_digestion=True) is None
    assert "site" not in view.layers


def test_panel_creates_and_renames_an_empty_user_layer():
    view = _mute(demo["dialanine"])
    _action(view, "create_layer", tag="site")
    assert view.layers["site"].provenance == "user"
    assert view.layers["site"].members == {}

    _action(view, "rename_layer", tag="site", new_tag="pocket")
    assert "site" not in view.layers
    assert view.layers["pocket"].members == {}


def test_renaming_a_layer_keeps_its_regions():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    view.layers["site"].set_tag("pocket", skip_digestion=True)
    assert r.layer == "pocket"
    assert "pocket" in view.layers
    assert "A" in view.layers["pocket"].regions


def test_renaming_a_mixed_layer_republishes_both_membership_channels():
    view = _mute(demo["dialanine"])
    region = _region(view, [0, 1, 2], "A", representation="cartoon")
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="marker",
        skip_digestion=True,
    )
    region.set_layer("site", skip_digestion=True)
    shape.set_layer_tag("site", skip_digestion=True)
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # noqa: SLF001

    view.layers["site"].set_tag("pocket", skip_digestion=True)

    latest = {message["op"]: message for message in sent}
    region_record = next(item for item in latest["set_region_summaries"]["regions"] if item["tag"] == "A")
    shape_record = next(item for item in latest["set_shape_summaries"]["shapes"] if item["tag"] == "marker")
    assert region_record["layer"] == "pocket"
    assert shape_record["layer_tag"] == "pocket"
    assert latest["set_layer_summaries"]["layers"] == [
        {"tag": "pocket", "provenance": "user", "hidden": False},
    ]
