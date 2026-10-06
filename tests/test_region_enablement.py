"""Region suspension preserves molecular identity and visual configuration."""

from copy import deepcopy

import pytest

import molsysviewer as msv


@pytest.fixture
def view():
    result = msv.demo["dialanine"]
    result.widget.send = lambda _message: None
    yield result
    result.close()


@pytest.mark.parametrize("representation", [None, "inherit", "ball-and-stick"])
def test_enablement_preserves_hidden_request_identity_and_style(view, representation):
    region = view.regions.add(atom_indices=[0, 1], tag="source", representation=representation)
    region.hide()
    uid, order, params = region.uid, region.order, dict(region.repr_params)
    region.disable()
    assert not region.enabled and not region.visible
    assert region._hidden
    assert view.regions["source"] is region
    assert region.select() == [0, 1]
    derived = region.union([2], tag="derived")
    assert derived.atom_indices == (0, 1, 2)
    assert derived.dependencies == (uid,)
    region.enable()
    assert region.enabled and not region.visible
    assert (region.uid, region.order, region.repr_params) == (uid, order, params)
    assert region.representation == representation
    region.show()
    assert region.visible


def test_disabled_region_visibility_and_layers_do_not_enable_it(view):
    region = view.regions.add(atom_indices=[0, 1], tag="source")
    region.set_layer("sources")
    region.disable()
    view.whole.hide()
    region.hide()
    region.show()
    view.layers["sources"].hide()
    assert not region.enabled and region._hidden
    view.layers["sources"].show()
    assert not region.enabled and not region._hidden
    view.regions.hide_all()
    assert not region.enabled and region._hidden
    view.regions.show_all()
    assert not region.enabled and not region._hidden
    assert not view.whole.visible
    region.enable()
    assert region.visible and not view.whole.visible


def test_disable_suspends_owned_colors_and_restores_precedence(view):
    view.whole.set_color("blue")
    low = view.regions.add(atom_indices=[0, 1], tag="low")
    low.set_color("red")
    high = view.regions.add(atom_indices=[1, 2], tag="high")
    high.set_color("green")
    configured = deepcopy(view._atom_color_layers)
    before = dict(view._atom_color_map)
    high.disable()
    assert view._atom_color_map[1] == 0xFF0000
    assert view._atom_color_map[2] == 0x0000FF
    assert view._atom_color_layers == configured
    high.set_color("orange")
    assert view._atom_color_map[1] == 0xFF0000
    high.enable()
    assert view._atom_color_map[1] == 0xFFA500
    high.set_color("green")
    assert view._atom_color_map == before
    low.disable()
    assert view._atom_color_map[0] == 0x0000FF


def test_disabled_region_survives_state_session_copy_extract_rebuild_and_popup(view, tmp_path):
    region = view.regions.add(atom_indices=[0, 1], tag="source", representation="inherit")
    region.set_color("orange")
    region.hide()
    region.disable()
    expected = next(r for r in view.export_state()["regions"] if r["tag"] == "source")
    assert expected["enabled"] is False and expected["hidden"] is True
    path = tmp_path / "disabled.msv"
    view.save_session(path)
    targets = [
        msv.demo["dialanine"],
        msv.load_session(path),
        msv.tools.basic.copy(view),
        view.extract(selection=[0, 1]),
    ]
    targets[0].import_state(view.export_state())
    try:
        for target in targets:
            restored = target.regions["source"]
            assert not restored.enabled and restored._hidden
            assert restored.uid == region.uid and restored.representation == "inherit"
            assert restored.atom_indices == (0, 1)
            assert target._atom_color_layers["source"] == {0: 0xFFA500, 1: 0xFFA500}
            assert target._atom_color_map == {}
            messages = target._build_embedded_runtime_snapshot()
            creation = next(m for m in messages if m.get("op") == "create_region" and m["tag"] == "source")
            assert creation["enabled"] is False
            restored.enable()
            assert restored._hidden and target._atom_color_map == {0: 0xFFA500, 1: 0xFFA500}
        view.apply_system_edit(view.molsys, atom_index_map={i: i for i in range(view.molsys.get_n_atoms())})
        assert not view.regions["source"].enabled and view.regions["source"]._hidden
        assert next(m for m in reversed(view._test_message_log) if m.get("op") == "create_region")["enabled"] is False
    finally:
        for target in targets:
            target.close()


def test_enablement_round_trips_through_history_and_studio(view):
    region = view.regions.add(atom_indices=[0, 1], tag="source")
    region.hide()
    view._handle_frontend_event(
        {"event": "interaction_context_action", "action": "toggle_region_enabled", "tag": "source"}
    )
    assert not region.enabled and region._hidden
    assert view.history.undo()
    assert view.regions["source"].enabled and view.regions["source"]._hidden
    assert view.history.redo()
    assert not view.regions["source"].enabled and view.regions["source"]._hidden
    view._handle_frontend_event(
        {"event": "interaction_context_action", "action": "toggle_region_visibility", "tag": "source"}
    )
    assert not view.regions["source"].enabled and not view.regions["source"]._hidden
    view._handle_frontend_event(
        {"event": "interaction_context_action", "action": "toggle_region_enabled", "tag": "source"}
    )
    assert view.regions["source"].visible
    assert view.regions.info("source")["enabled"] is True
    assert next(r for r in view._region_summary_records() if r["tag"] == "source")["enabled"] is True


@pytest.mark.parametrize("invalid", ["yes", 0, None])
def test_invalid_enabled_state_rejects_before_mutation(view, invalid):
    view.regions.add(atom_indices=[0, 1], tag="source")
    before = view.export_state()
    incoming = deepcopy(before)
    incoming["regions"][0]["enabled"] = invalid
    with pytest.raises(ValueError, match="enabled"):
        view.import_state(incoming)
    assert view.export_state() == before


def test_legacy_state_defaults_enabled_and_disabled_isolation_is_rejected(view):
    region = view.regions.add(atom_indices=[0, 1], tag="source")
    legacy = view.export_state()
    legacy["regions"][0].pop("enabled")
    view.import_state(legacy)
    region = view.regions["source"]
    assert region.enabled
    region.show_only()
    region.disable()
    assert not region._show_only
    before = view.export_state()
    with pytest.raises(ValueError, match="Enable"):
        region.show_only()
    assert view.export_state() == before
    invalid = deepcopy(before)
    invalid["regions"][0]["show_only"] = True
    with pytest.raises(ValueError, match="show_only"):
        view.import_state(invalid)
    assert view.export_state() == before


def test_disabled_dynamic_recipe_remains_available_to_dependents():
    with msv.demo["pentalanine"] as view:
        view._dynamic_region_evaluation_budget_ms = float("inf")
        source = view._new_region_impl(selection="atom_index < 3", tag="dynamic", frame_dependent=True)
        source.mode = "dynamic"
        source.disable()
        derived = source.union([4], tag="derived")
        assert source in view._dynamic_regions_requiring_frame_evaluation()
        view._evaluate_dynamic_regions_for_frame(3)
        assert source.select() == [0, 1, 2]
        assert derived.select() == [0, 1, 2, 4]
        assert not source.enabled
