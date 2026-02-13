import numpy as np

from molsysviewer._private.arg_digestion import (
    digest_selection_and_syntax,
    digest_selection_inputs,
)


def test_digest_selection_and_syntax_normalizes_syntax():
    selection, syntax = digest_selection_and_syntax("all", syntax="mdtraj", caller="test")

    assert selection == "all"
    assert syntax == "MDTraj"


def test_digest_selection_inputs_handles_indices():
    selection, structure_indices, syntax = digest_selection_inputs(
        selection=[1, 2, 3],
        structure_indices=0,
        syntax="MolSysMT",
        caller="test",
    )

    assert selection == [1, 2, 3]
    assert isinstance(structure_indices, np.ndarray)
    assert structure_indices.tolist() == [0]
    assert syntax == "MolSysMT"
