import types

from molsysviewer.loaders import load_from_molsysmt


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


def test_load_from_molsysmt_uses_viewer_json(monkeypatch):
    """Ensure ViewerJSON conversion path yields a MolSys payload message."""
    view = DummyView()

    viewer_json = {
        "atoms": {"atom_id": [1]},
        "frames": [
            {
                "positions": [[1.0, 2.0, 3.0]],
                "time": 5,
                "cell": {"a": 1, "b": 2, "c": 3, "alpha": 90, "beta": 90, "gamma": 90},
            }
        ],
    }

    def fake_convert(item, *, to_form=None, **_kwargs):
        if to_form == "molsysmt.MolSys":
            return types.SimpleNamespace()
        if to_form == "molsysmt.ViewerJSON":
            return types.SimpleNamespace(to_dict=lambda: viewer_json)
        raise AssertionError("Unexpected conversion request")

    def fake_get(_item, *, element=None, n_atoms=False, **_kwargs):
        if element == "atom" and n_atoms:
            return 1
        raise AssertionError("Unexpected get request")

    import molsysviewer.loaders.load_molsysmt as loader_mod

    monkeypatch.setattr(loader_mod.msm, "convert", fake_convert)
    monkeypatch.setattr(loader_mod.msm, "get", fake_get)

    load_from_molsysmt(view, molecular_system="dummy")

    assert view.messages, "No message was sent to the frontend"
    message = view.messages[0]
    assert message["op"] == "load_molsys_payload"
    payload = message["payload"]
    assert payload["atoms"]["atom_id"] == [1]
    # Coordinates arrive in angstroms (ViewerJSON provides nm)
    assert payload["coordinates"][0]["positions"] == [[10.0, 20.0, 30.0]]
    assert payload["coordinates"][0]["cell"] == {
        "a": 10.0,
        "b": 20.0,
        "c": 30.0,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
    }
