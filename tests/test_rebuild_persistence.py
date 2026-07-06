from __future__ import annotations
import pytest
import numpy as np

pytest.importorskip("molsysmt")
import molsysmt as msm
from molsysviewer.demo import demo
from _edit_helpers import apply_remove

def test_rebuild_persistence_and_hierarchy():
    """Stress test for persistence of annotations, measurements, and selections after rebuild."""

    # 1. Load a system (pentalanine)
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None # Mock send
    mol = view._molsys

    initial_n_atoms = int(msm.get(mol, element='atom', n_atoms=True))

    # 2. Setup artifacts
    # Label on residue 2
    view.annotations.add_annotation(text="LabelRes2", selection="group_index==2", tag="L2", skip_digestion=True)
    # Distance between atoms 10 and 11
    view.measurements.add_distance(selection_a=[10], selection_b=[11], tag="D10-11", skip_digestion=True)
    # Save selection for atoms 10, 11
    view.selections.add(tag="S10-11", atom_indices=[10, 11], skip_digestion=True)
    
    # Get the actual atom indices for residue 2 before removal
    res2_atoms_before = list(msm.select(mol, selection='group_index==2', syntax='MolSysMT'))

    # 3. Perform a structural modification: Remove the first 5 atoms
    # This triggers rebuild_view_from_current_molsys
    apply_remove(view, selection='atom_index < 5')
    
    new_n_atoms = int(msm.get(view._molsys, element='atom', n_atoms=True))
    assert new_n_atoms == initial_n_atoms - 5

    # 4. Verify hierarchy in the new payload
    load_msg = next(m for m in view._message_history if m.get('op') == 'load_molsys_payload')
    payload_atoms = load_msg.get('payload', {}).get('atoms', {})
    
    assert 'molecule_id' in payload_atoms
    assert 'component_id' in payload_atoms
    assert len(payload_atoms['molecule_id']) == new_n_atoms

    # 5. Verify persistence and remapping
    # Original res2_atoms_before shifted by -5
    expected_label_indices = [idx - 5 for idx in res2_atoms_before]
    # Original 10, 11 shifted by -5 -> 5, 6
    expected_dist_indices = [[5], [6]]
    expected_sel_indices = [5, 6]
    
    def get_history_msg(op, tag):
        msgs = []
        for msg in view._message_history:
            msg_op = msg.get('op')
            msg_tag = msg.get('tag') or msg.get('options', {}).get('tag')
            if msg_op == op and msg_tag == tag:
                msgs.append(msg)
        return msgs

    # Check Label
    l2_msgs = get_history_msg('add_label', 'L2')
    assert len(l2_msgs) == 1, "Label should not be duplicated in history"
    assert l2_msgs[0]['options']['atom_indices'] == expected_label_indices

    # Check Distance
    d10_msgs = get_history_msg('add_distance_measurement', 'D10-11')
    assert len(d10_msgs) == 1, "Measurement should not be duplicated in history"
    assert d10_msgs[0]['options']['picks_atom_indices'] == expected_dist_indices

    # Check Selection
    s10_msgs = get_history_msg('save_selection', 'S10-11')
    assert len(s10_msgs) == 1, "Selection should not be duplicated in history"
    assert s10_msgs[0]['atom_indices'] == expected_sel_indices
