from molsysviewer.shapes import PharmacophoreShapes


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


def test_add_pharmacophore_features():
    view = DummyView()
    ph4 = PharmacophoreShapes(view)

    ph4.add_pharmacophore_features(
        centers=[(0, 0, 0), (1, 1, 1)],
        kinds=["donor", "acceptor"],
        radii=[0.5, 0.6],
        alphas=[0.4, 0.5],
        directions=[(1, 0, 0), (0, 1, 0)],
        tag="ph4",
        name="demo",
    )

    assert view.messages == [
        {
            "op": "add_pharmacophore_features",
            "options": {
                "centers": [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
                "kinds": ["donor", "acceptor"],
                "radii": [0.5, 0.6],
                "alphas": [0.4, 0.5],
                "colors": [0x3b82f6, 0xef4444],
                "directions": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                "tag": "ph4",
                "name": "demo",
            },
        }
    ]
