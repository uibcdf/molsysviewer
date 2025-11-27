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
        load_pdb_id(pdb_id="   ", view=view)


def test_load_pdb_id_creates_view_when_missing(monkeypatch):
    def fake_convert(item, *, to_form=None, **_kwargs):
        return f"converted:{to_form}"

    def fake_get(_item, *, element=None, n_atoms=False, **_kwargs):
        if element == "atom" and n_atoms:
            return 2
        return None

    import molsysviewer.loaders.load_pdb_id as pdb_mod

    created_view = DummyView()

    monkeypatch.setattr(pdb_mod, "ensure_view", lambda view=None: created_view if view is None else view)
    monkeypatch.setattr(pdb_mod.msm, "convert", fake_convert)
    monkeypatch.setattr(pdb_mod.msm, "get", fake_get)

    result = load_pdb_id(pdb_id="1crn", label="demo")

    assert result is created_view
    assert created_view.messages
