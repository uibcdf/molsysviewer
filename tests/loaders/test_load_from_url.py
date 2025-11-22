from molsysviewer.loaders import load_from_url


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


def test_load_from_url_sends_minimal_message():
    view = DummyView()
    load_from_url(view, url="http://example.com/structure.pdb", format="pdb", label="demo")

    assert view.molecular_system == "http://example.com/structure.pdb"
    assert view.selection == "all"
    assert view._molsys is None
    assert view.messages == [
        {
            "op": "load_structure_from_url",
            "url": "http://example.com/structure.pdb",
            "format": "pdb",
            "label": "demo",
        }
    ]
