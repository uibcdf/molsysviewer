import pytest
from molsysviewer import demo
import molsysmt as msm
import numpy as np
from molsysviewer.viewer.index_mapper import IndexMapper
from molsysviewer.loaders.load_molsysmt import load_from_molsysmt

def test_index_mapper_direct():
    molsys = msm.convert(demo["dialanine"]._molsys, to_form="molsysmt.MolSys")
    # Say we select a subset of atoms (atom index >= 10)
    selection = "atom_index >= 10"
    mapper = IndexMapper(molsys, selection=selection)
    
    # 22 atoms in dialanine. The subset has 12 atoms (indices 10 to 21).
    assert len(mapper.original_atoms) == 12
    assert mapper.original_atoms[0] == 10
    
    assert mapper.to_local_atom(10) == 0
    assert mapper.to_original_atom(0) == 10
    assert mapper.to_local_atoms([10, 15]) == [0, 5]
    assert mapper.to_original_atoms([0, 5]) == [10, 15]

def test_molsysmt_loaded_subselection():
    # Load dialanine with a subselection
    orig_view = demo["dialanine"]
    orig_molsys = orig_view.molecular_system
    
    # Load with subset of atoms (group 1) and all structures
    group1_atoms = list(orig_view.select("group_index==1"))
    view = load_from_molsysmt(orig_molsys, selection="group_index==1")
    
    assert view._index_mapper is not None
    # Let's select in view
    # view.select should return original coordinates
    selected = view.select("group_index==1")
    assert list(selected) == group1_atoms
    
    # Active selection picking event emulation
    # Frontend reports local atom index 0 is active selection
    local_event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": [0],
        "group_indices": [0],
        "component_indices": [0],
        "chain_indices": [0],
        "molecule_indices": [0],
        "entity_indices": [0],
        "count_atoms": 1,
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(local_event)
    
    # Active selection atom indices should be the original indices
    assert view.active_selection.atom_indices == [group1_atoms[0]]
    # active selection info group indices should be the original ones (group 1)
    assert view.active_selection.group_indices == [1]
    
    # Let's save selection and check it
    selection = view.active_selection.save("saved_active")
    assert selection.atom_indices == [group1_atoms[0]]
    assert selection.group_indices == [1]
    
    # Activating persistent selection should send local index 0 to frontend
    selection.activate()
    assert view._message_history[-1]["op"] == "set_active_selection"
    assert view._message_history[-1]["atom_indices"] == [0]

def test_molsysmt_loaded_structures_subselection():
    # Load pentalanine (has structures)
    orig_view = demo["pentalanine"]
    orig_molsys = orig_view.molecular_system
    
    # Load with structure_indices [2, 4]
    view = load_from_molsysmt(orig_molsys, structure_indices=[2, 4])
    assert view._index_mapper is not None
    
    # Player current index is initially original frame index 2 (local index 0)
    assert view.player.index == 2
    
    # Moving player forward advances local frame by 1, wrapping correctly
    view.player.step_forward()
    assert view.player.index == 4
    
    # Check that set_trajectory_frame with local index 1 was sent to frontend
    assert view._message_history[-1]["op"] == "set_trajectory_frame"
    assert view._message_history[-1]["index"] == 1
    
    # Front-end updates active structure index to 0
    event = {
        "event": "trajectory_frame_changed",
        "frame": 0,
    }
    view._handle_frontend_event(event)
    assert view.player.index == 2
