from __future__ import annotations

import warnings

import pytest

from molsysviewer.demo import demo


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
    assert "A" in layer.members


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


def test_moving_a_region_cleans_up_the_emptied_layer():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("first", skip_digestion=True)
    assert "first" in view.layers

    r.set_layer("second", skip_digestion=True)
    assert r.layer == "second"
    # "first" is now empty and must not linger.
    assert "first" not in view.layers
    assert "second" in view.layers


def test_deleting_a_region_cleans_up_its_empty_layer():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    r.delete(skip_digestion=True)
    assert "site" not in view.layers


def test_remove_from_layer_detaches_and_cleans_up():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    r.remove_from_layer(skip_digestion=True)
    assert r.layer is None
    assert "site" not in view.layers


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
    layer = view.new_layer(tag="site")
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
    _action(view, "set_region_layer", tag="A", layer="site")
    assert view.regions["A"].layer == "site"
    # An empty/null layer detaches.
    _action(view, "set_region_layer", tag="A", layer="")
    assert view.regions["A"].layer is None
    assert "site" not in view.layers


def test_context_action_set_layer_visibility_and_delete():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "A", representation="cartoon")
    _action(view, "set_region_layer", tag="A", layer="site")

    _action(view, "set_layer_visibility", tag="site", hidden=True)
    assert view.regions["A"].visible is False
    _action(view, "set_layer_visibility", tag="site")  # toggle back
    assert view.regions["A"].visible is True

    _action(view, "delete_layer_group", tag="site")
    assert "A" not in view.regions
    assert "site" not in view.layers


def test_context_action_remove_region_from_layer():
    view = _mute(demo["dialanine"])
    _region(view, [0, 1, 2], "A", representation="cartoon")
    _action(view, "set_region_layer", tag="A", layer="site")
    _action(view, "remove_region_from_layer", tag="A")
    assert view.regions["A"].layer is None


def test_renaming_a_layer_keeps_its_regions():
    view = _mute(demo["dialanine"])
    r = _region(view, [0, 1, 2], "A", representation="cartoon")
    r.set_layer("site", skip_digestion=True)
    view.layers["site"].set_tag("pocket", skip_digestion=True)
    assert r.layer == "pocket"
    assert "pocket" in view.layers
    assert "A" in view.layers["pocket"].regions
