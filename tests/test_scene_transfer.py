"""Scene copies and explicit extraction correspondences retain canonical state."""

import molsysmt as msm
import pytest

import molsysviewer as msv


@pytest.fixture
def populated():
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
    analysis = msm.Interactions.from_records(
        [
            {
                "structure_index": i,
                "interaction_type": "disulfide_candidate",
                "participants": [{"role": "donor", "atom_indices": [0]}, {"role": "acceptor", "atom_indices": [2]}],
            }
            for i in range(3)
        ],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 1, 2],
        method="scene_transfer_fixture",
    )
    view.interactions.attach(analysis, name="contacts", assume_aligned=True)
    view.interactions.add("contacts", tag="hb", selection=[0, 2], structure_indices=[2, 0])
    view.regions.add(selection="atom_index == [0, 1, 2]", tag="r")
    view.regions["r"].set_color("red")
    view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="s").hide()
    view.annotations.add(
        text="note", atom_indices=[0], tag="a", offset_mode="camera", offset=(1.0, 2.0, 3.0), leader_line=True
    )
    view.measurements.add_distance(selection_a=[0], selection_b=[2], tag="d")
    view.selections.add("sel", atom_indices=[0, 2])
    return view


def test_copy_preserves_canonical_objects_colors_recipes_and_analyses(populated):
    result = msv.tools.basic.copy(populated)
    assert result.export_state() == populated.export_state()
    for domain, tag in (("shapes", "s"), ("annotations", "a"), ("measurements", "d"), ("interactions", "hb")):
        assert getattr(result, domain).get(tag) is not getattr(populated, domain).get(tag)
        assert getattr(result, domain).get(tag) is not None
    result.shapes["s"].set_color("blue")
    assert result.shapes.records() != populated.shapes.records()


def test_extract_remaps_frames_atoms_colors_and_scientific_references(populated):
    result = populated.extract(selection=[0, 2], structure_indices=[2, 0])
    record = result.interactions.records()[0]
    assert record["filter"]["selection"] == [0, 1]
    assert record["filter"]["structure_indices"] == [0, 1]
    assert not record["broken"]
    assert result.interactions._frame(result.interactions["hb"], 1)["links"]
    state = result.export_state()
    assert state["regions"][0]["color_layer"] == {"0": 16711680, "1": 16711680}
    assert state["regions"][0]["provenance"]["source_recipe"]["kind"] == "query"
    assert result.shapes["s"]._hidden
    assert state["measurements"][0]["options"]["picks_atom_indices"] == [[0], [1]]
    assert result.selections["sel"].atom_indices == [0, 1]


def test_extraction_marks_incomplete_interaction_filters_broken(populated):
    result = populated.extract(selection=[0], structure_indices=[2, 0])
    assert result.interactions["hb"].broken
    assert result.interactions._frame(result.interactions["hb"], 0)["links"] == []


def test_extraction_retains_interaction_filter_for_every_repeated_structure(populated, tmp_path):
    populated.interactions["hb"].set_filter(selection=[0, 2], structure_indices=[2])
    populated.player.go_to_structure(2)
    with populated.extract(selection=[0, 2], structure_indices=[2, 0, 2]) as result:
        obj = result.interactions["hb"]
        assert obj.filter["structure_indices"] == [0, 2]
        assert result.player.index == 0
        assert result.interactions.get_analysis("contacts").n_interactions == 3
        assert result.interactions.query("contacts", structure_indices=[0, 2]).n_interactions == 2
        first = result.interactions._frame(obj, 0)
        last = result.interactions._frame(obj, 2)
        assert first["status"] == last["status"] == "evaluated"
        assert first["n_supported"] == last["n_supported"] == 1
        assert first["links"][0]["start"] == last["links"][0]["start"]
        assert first["links"][0]["end"] == last["links"][0]["end"]
        assert result.interactions._frame(obj, 1)["status"] == "excluded"
        assert result.load_blocks[0]["structure_map"]["runs"] == [[3, 0, 1], [0, 1, 1], [3, 2, 1]]
        path = tmp_path / "repeated.msv"
        result.save_session(path)
        with msv.load_session(path) as restored:
            restored_obj = restored.interactions["hb"]
            assert restored_obj.filter["structure_indices"] == [0, 2]
            assert restored.player.index == 0
            assert [restored.interactions._frame(restored_obj, index)["status"] for index in range(3)] == [
                "evaluated",
                "excluded",
                "evaluated",
            ]


def test_merge_registers_every_overlay_and_preserves_colors():
    left, right = msv.demo["dialanine"], msv.demo["dialanine"]
    for view in (left, right):
        view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="s")
        view.annotations.add("note", atom_indices=[0], tag="a")
        view.regions.add(atom_indices=[0], tag="r").set_color("red")
    result = msv.tools.basic.merge([left, right])
    assert result.shapes["s"] is not None and result.shapes["s__2"] is not None
    assert result.annotations["a__2"] is not None
    state = result.export_state()
    assert len(state["shapes"]) == 2
    assert state["regions"][1]["color_layer"] == {"22": 16711680}


def test_identity_extraction_preserves_region_recipes(populated):
    result = populated.extract(selection="all")
    assert result.regions["r"].provenance == populated.regions["r"].provenance
    assert result.annotations.records()[0]["options"] == populated.annotations.records()[0]["options"]


def test_extraction_remaps_focus_style_atoms(populated):
    populated.focus_with_fade(selection=[0, 2])
    result = populated.extract(selection=[0, 2], structure_indices=[2, 0])
    assert result._scene_look["focus_fade"]["options"]["focus_atom_indices"] == [0, 1]
    assert populated._scene_look["focus_fade"]["options"]["focus_atom_indices"] == [0, 2]
