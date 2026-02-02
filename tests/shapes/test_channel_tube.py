from molsysviewer.shapes import ChannelTubes


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


def test_add_channel_tube_message():
    view = DummyView()
    tubes = ChannelTubes(view)

    tubes.add_channel_tube(
        centers=[(0, 0, 0), (1, 1, 1), (2, 1, 0)],
        radii=[1.0, 1.1, 1.2],
        color_mode="solvent",
        solvent_distances=[0.2, 0.4, 0.6],
        color_map="plasma",
        radial_segments=12,
        smoothing_subdivisions=2,
        alpha=0.8,
        tag="tube",
        name="demo",
    )

    assert view.messages == [
        {
            "op": "add_channel_tube",
            "options": {
                "centers": [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 1.0, 0.0]],
                "radii": [1.0, 1.1, 1.2],
                "color_mode": "solvent",
                "solvent_distances": [0.2, 0.4, 0.6],
                "color_map": "plasma",
                "radial_segments": 12,
                "smoothing_subdivisions": 2,
                "alpha": 0.8,
                "tag": "tube",
                "name": "demo",
            },
        }
    ]


def test_add_channel_tube_requires_two_points():
    view = DummyView()
    tubes = ChannelTubes(view)
    try:
        tubes.add_channel_tube(centers=[(0, 0, 0)], radii=[1.0])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for insufficient centers")
