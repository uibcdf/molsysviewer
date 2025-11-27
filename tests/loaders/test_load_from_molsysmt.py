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

        def to_form(self, target):
            if target == "molsysmt.ViewerJSON":
                return self.payload
            raise AssertionError("Unexpected to_form target")

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


def test_load_from_molsysmt_creates_view_when_missing(monkeypatch):
    class DummyMolSys:
        def __init__(self, payload):
            self.payload = payload

        def get(self, *, element=None, n_atoms=False, **_kwargs):
            if element == "atom" and n_atoms:
                return 1
            raise AssertionError("Unexpected get request")

        def to_form(self, target):
            if target == "molsysmt.ViewerJSON":
                return self.payload
            raise AssertionError("Unexpected to_form target")

    viewer_json = {
        "atoms": {"atom_id": [1]},
        "frames": [
            {
                "positions": [[1.0, 2.0, 3.0]],
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
