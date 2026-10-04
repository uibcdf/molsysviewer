"""Public scene guarantees: lifetimes, detached reads, registry writes and history."""

from copy import deepcopy

import pytest

import molsysviewer as msv


@pytest.fixture
def view():
    view = msv.demo["dialanine"]
    view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="s")
    view.annotations.add("note", atom_indices=[0], tag="a")
    view.measurements.add_distance(selection_a=[0], selection_b=[2], tag="d")
    view.regions.add(atom_indices=[0, 1], tag="r")
    view.layers.add("group", meta={"nested": {"value": 1}})
    view.selections.add("sel", atom_indices=[0, 1])
    return view


class TestHandleLifetime:
    @pytest.mark.parametrize(
        "domain,tag,mutate",
        [
            ("shapes", "s", lambda obj: obj.set_color("blue")),
            ("annotations", "a", lambda obj: obj.hide()),
            ("measurements", "d", lambda obj: obj.hide()),
            ("measurements", "d", lambda obj: obj.focus()),
            ("regions", "r", lambda obj: obj.hide()),
            ("layers", "group", lambda obj: obj.hide()),
            ("selections", "sel", lambda obj: obj.delete()),
        ],
    )
    def test_replaced_handles_cannot_mutate_restored_objects(self, view, domain, tag, mutate):
        old = getattr(view, domain).get(tag)
        view.regions["r"].set_color("red")
        assert view.history.undo()
        assert getattr(view, domain).get(tag) is not old
        before = deepcopy(view.export_state())
        redo = list(view.history._redo)
        with pytest.raises(ValueError, match="retired"):
            mutate(old)
        assert view.export_state() == before
        assert view.history._redo == redo

    def test_retired_section_cannot_toggle_replacement_drag_handles(self, view):
        section = view.scene.add_section(point=[0, 0, 0], normal=[1, 0, 0], tag="cut")
        view.import_state(view.export_state())
        before = deepcopy(view.export_state())
        messages = len(view._test_message_log)
        for operation in (section.enable_drag, section.disable_drag):
            with pytest.raises(ValueError, match="retired"):
                operation()
        assert view.export_state() == before
        assert len(view._test_message_log) == messages


class TestDetachedReads:
    @pytest.mark.parametrize(
        "domain,key", [("shapes", "center"), ("annotations", "atom_indices"), ("measurements", "picks_atom_indices")]
    )
    def test_nested_records_are_detached(self, view, domain, key):
        state = view.export_state()
        records = getattr(view, domain).records()
        records[0]["options"][key].clear()
        assert view.export_state() == state

    def test_layer_metadata_and_selection_recipe_are_detached(self, view):
        state = view.export_state()
        view.layers.info("group")["meta"]["nested"]["value"] = 7
        view.selections.records()[0]["atom_indices"].clear()
        assert view.export_state() == state

    def test_representation_params_and_style_queries_are_detached(self, view):
        view.whole.set_representation("ball-and-stick", color="red")
        view.regions["r"].set_representation("ball-and-stick", color="red")
        state = view.export_state()
        view.whole.params["molstar_color_theme"]["params"]["value"] = 0
        view.regions["r"].repr_params["molstar_color_theme"]["params"]["value"] = 0
        assert view.export_state() == state
        style = msv.Style(representation="cartoon", params={"nested": {"value": 1}})
        view.styles.add("owned", style)
        view.styles.records()[0]["style"]["params"]["nested"]["value"] = 0
        assert style.info()["params"]["nested"]["value"] == 1


class TestRegistryLifecycle:
    @pytest.mark.parametrize("domain,tag", [("regions", "r"), ("layers", "group")])
    @pytest.mark.parametrize(
        "operation",
        [
            lambda m, t: m.pop(t),
            lambda m, t: m.__delitem__(t),
            lambda m, t: m.__setitem__(t, None),
            lambda m, t: m.update({t: None}),
            lambda m, t: m.popitem(),
            lambda m, t: m.setdefault("bad", None),
            lambda m, t: m.__ior__({t: None}),
        ],
    )
    def test_raw_mutations_are_rejected_without_scene_changes(self, view, domain, tag, operation):
        state = view.export_state()
        with pytest.raises(TypeError, match="scene manager"):
            operation(getattr(view, domain), tag)
        assert view.export_state() == state

    def test_regions_clear_uses_lifecycle_and_undo(self, view):
        view.regions["r"].set_color("red")
        view.regions.clear()
        assert not view.regions
        assert not view._atom_color_layers.get("r")
        assert view.history.undo()
        assert view.regions["r"].atom_indices == (0, 1)
        assert view._atom_color_layers["r"]


class TestHistoryCommit:
    def test_rejected_operations_and_noops_preserve_redo(self, view):
        view.shapes["s"].set_color("red")
        assert view.history.undo()
        redo = list(view.history._redo)
        undo = list(view.history._undo)
        with pytest.raises(Exception):
            view.regions.add(atom_indices=[0], tag="r")
        assert view.history._redo == redo
        assert view.history._undo == undo
        view.shapes["s"].show()
        assert view.history._redo == redo
        assert view.history._undo == undo
        assert view.history.redo()
        assert view.shapes.records()[0]["options"]["color"] == 16711680


def test_scene_inventory_includes_interactions_and_layer_counts():
    import molsysmt as msm

    view = msv.demo["dialanine"]
    result = msm.Interactions.from_records(
        [
            {
                "structure_index": 0,
                "interaction_type": "hbond",
                "participants": [{"role": "donor", "atom_indices": [0]}, {"role": "acceptor", "atom_indices": [2]}],
            }
        ],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=view.molsys.structures.n_structures,
        evaluated_structure_indices=[0],
        method="inspection_fixture",
    )
    view.interactions.attach(result, name="contacts", assume_aligned=True)
    view.interactions.add("contacts", tag="hb", layer_tag="contacts")
    summary = view._viewer_info_summary()
    assert summary["interactions"]["tags"] == ["hb"]
    assert summary["interactions"]["analysis_names"] == ["contacts"]
    records = view.info(output_type="dictionary")
    assert any(r["section"] == "interactions" and r["tag"] == "hb" for r in records)
    frame = view.info(output_type="dataframe")
    assert view.info(output_type="styler").data.equals(frame)
    row = frame[(frame["section"] == "interactions") & (frame["tag"] == "hb")].iloc[0]
    assert row["kind"] == "interaction" and row["visible"]
    assert "analysis=contacts" in row["details"]
    layer = frame[(frame["section"] == "layers") & (frame["tag"] == "contacts")].iloc[0]
    assert "interactions=1" in layer["details"]
    view.layers["contacts"].hide()
    assert not view.info(output_type="dataframe").query("section == 'interactions'").iloc[0]["visible"]
