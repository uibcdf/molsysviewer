import pytest

from molsysviewer.shapes import PocketSurfaces


class DummyView:
    def __init__(self) -> None:
        self.messages = []
        self._layers = {}
        self._layer_counter = 0

    def _send(self, message):
        self.messages.append(message)

    def _next_layer_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"


def test_add_pocket_surface_basic_message():
    view = DummyView()
    pockets = PocketSurfaces(view)

    pockets.add_pocket_surface(atom_indices=[1, 2, 3], scalars=[0.1, 0.2, 0.3], alpha=0.5)

    assert view.messages == [
        {
            "op": "add_pocket_surface",
            "options": {
                "atom_indices": [1, 2, 3],
                "scalars": [0.1, 0.2, 0.3],
                "alpha": 0.5,
                "tag": "shape-1",
                "layer_tag": "shape-1",
            },
        }
    ]


def test_mouth_indices_override_clip():
    view = DummyView()
    pockets = PocketSurfaces(view)

    pockets.add_pocket_surface(
        atom_indices=[1, 2],
        mouth_atom_indices=[[4, 5], [6]],
        clip_plane={"point": [0, 0, 0], "normal": [0, 0, 1]},
    )

    # clip_plane is ignored when mouths are provided
    options = view.messages[0]["options"]
    assert "clip_plane" not in options
    assert options["mouth_atom_indices"] == [[4, 5], [6]]


def test_requires_atom_indices():
    view = DummyView()
    pockets = PocketSurfaces(view)
    with pytest.raises(ValueError):
        pockets.add_pocket_surface(atom_indices=[])
