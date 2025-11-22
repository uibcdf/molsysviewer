from molsysviewer.loaders import load_mmcif_string


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


def test_load_mmcif_string_sends_message(monkeypatch):
    view = DummyView()

    def fake_convert(item, *, to_form=None, **_kwargs):
        return f"converted:{to_form}"

    def fake_get(_item, *, element=None, n_atoms=False, **_kwargs):
        if element == "atom" and n_atoms:
            return 2
        return None

    import molsysviewer.loaders.load_mmcif_string as mmcif_mod

    monkeypatch.setattr(mmcif_mod.msm, "convert", fake_convert)
    monkeypatch.setattr(mmcif_mod.msm, "get", fake_get)

    load_mmcif_string(view, mmcif_string="MMCIFDATA", label="cif")

    assert view.messages == [
        {
            "op": "load_structure_from_string",
            "format": "mmcif",
            "data": "MMCIFDATA",
            "label": "cif",
        }
    ]
