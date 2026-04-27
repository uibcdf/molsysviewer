import math

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

    class DummyMolSys:
        def __init__(self, payload):
            self.payload = payload

        def get(self, *, element=None, n_atoms=False, **_kwargs):
            if element == "atom" and n_atoms:
                return 1
            raise AssertionError("Unexpected get request")

        def get_n_atoms(self):
            return 1

        def to_form(self, target):
            if target == "molsysmt.ViewerJSON":
                return self.payload
            raise AssertionError("Unexpected to_form target")

    viewer_json = {
        "atoms": {
            "atom_id": [1],
            "atom_name": ["CA"],
            "group_id": [10],
            "group_name": ["MET"],
            "chain_id": ["A"],
            "entity_id": ["1"],
            "element_symbol": ["C"],
            "formal_charge": [0],
        },
        "bonds": {"atom_pairs": [[0, 0]], "order": [1]},
        "structures": [
            {
                "coordinates": [[1.0, 2.0, 3.0]],
                "time": 5,
                "box": {
                    "v0": [1.0, 0.0, 0.0],
                    "v1": [0.0, 2.0, 0.0],
                    "v2": [0.0, 0.0, 3.0],
                },
            }
        ],
    }

    def fake_convert(item, *, to_form=None, **_kwargs):
        if to_form == "molsysmt.MolSys":
            return DummyMolSys(viewer_json)
        raise AssertionError("Unexpected conversion request")

    import molsysviewer.loaders.load_molsysmt as loader_mod

    monkeypatch.setattr(loader_mod.msm, "convert", fake_convert)

    result = load_from_molsysmt(molecular_system="dummy", view=view)

    assert result is view
    assert view.messages, "No message was sent to the frontend"
    message = view.messages[0]
    assert message["op"] == "load_molsys_payload"
    payload = message["payload"]
    assert payload["atoms"]["atom_id"] == [1]
    assert payload["atoms"]["atom_name"] == ["CA"]
    assert payload["atoms"]["residue_id"] == [10]
    assert payload["atoms"]["residue_name"] == ["MET"]
    assert payload["atoms"]["chain_id"] == ["A"]
    assert payload["atoms"]["entity_id"] == ["1"]
    assert payload["atoms"]["element_symbol"] == ["C"]
    # Coordinates arrive in angstroms (ViewerJSON provides nm)
    assert payload["structures"][0]["coordinates"] == [[10.0, 20.0, 30.0]]
    assert payload["structures"][0]["box"] == [
        [10.0, 0.0, 0.0],
        [0.0, 20.0, 0.0],
        [0.0, 0.0, 30.0],
    ]
    assert payload["bonds"] == {"indexA": [0], "indexB": [0], "order": [1]}


def test_load_from_molsysmt_creates_view_when_missing(monkeypatch):
    class DummyMolSys:
        def __init__(self, payload):
            self.payload = payload

        def get(self, *, element=None, n_atoms=False, **_kwargs):
            if element == "atom" and n_atoms:
                return 1
            raise AssertionError("Unexpected get request")

        def get_n_atoms(self):
            return 1

        def to_form(self, target):
            if target == "molsysmt.ViewerJSON":
                return self.payload
            raise AssertionError("Unexpected to_form target")

    viewer_json = {
        "atoms": {"atom_id": [1]},
        "structures": [
            {
                "coordinates": [[1.0, 2.0, 3.0]],
            }
        ],
    }

    def fake_convert(item, *, to_form=None, **_kwargs):
        if to_form == "molsysmt.MolSys":
            return DummyMolSys(viewer_json)
        raise AssertionError("Unexpected conversion request")

    import molsysviewer.loaders.load_molsysmt as loader_mod

    created_view = DummyView()
    monkeypatch.setattr(loader_mod, "ensure_view", lambda view=None: created_view if view is None else view)
    monkeypatch.setattr(loader_mod.msm, "convert", fake_convert)

    result = load_from_molsysmt(molecular_system="dummy")

    assert result is created_view
    assert created_view.messages
