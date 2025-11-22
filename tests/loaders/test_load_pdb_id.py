import pytest

from molsysviewer.loaders import load_pdb_id


class DummyView:
    def __init__(self) -> None:
        self.messages = []
        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None

    def _send(self, message):
        self.messages.append(message)


def test_load_pdb_id_validates_input():
    view = DummyView()
    with pytest.raises(ValueError):
        load_pdb_id(view, pdb_id="   ")
