from molsysviewer.loaders import load_pdb_string


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


def test_load_pdb_string_sends_message(monkeypatch):
    view = DummyView()

    def fake_convert(item, *, to_form=None, **_kwargs):
        return f"converted:{to_form}"

    def fake_get(_item, *, element=None, n_atoms=False, **_kwargs):
        if element == "atom" and n_atoms:
            return 2
        return None

    import molsysviewer.loaders.load_pdb_string as pdb_mod

    monkeypatch.setattr(pdb_mod.msm, "convert", fake_convert)
    monkeypatch.setattr(pdb_mod.msm, "get", fake_get)

    load_pdb_string(view, pdb_string="PDBDATA", label="pdb")

    assert view.messages == [
        {
            "op": "load_structure_from_string",
            "format": "pdb",
            "data": "PDBDATA",
            "label": "pdb",
        }
    ]
