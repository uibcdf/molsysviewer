import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

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

    def _next_shape_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"


def test_add_channel_tube_message():
    view = DummyView()
    tubes = ChannelTubes(view)

    tubes.add_channel_tube(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1), (2, 1, 0)], "nm"),
        radii=puw.quantity([1.0, 1.1, 1.2], "nm"),
        color_mode="solvent",
        solvent_distances=[0.2, 0.4, 0.6],
        color_map="plasma",
        radial_segments=12,
        smoothing_subdivisions=2,
        alpha=0.8,
        tag="tube",
        name="demo",
    )

    assert view.messages[0]["op"] == "add_channel_tube"
    options = view.messages[0]["options"]
    assert options["centers"] == [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0], [20.0, 10.0, 0.0]]
    assert options["radii"] == [10.0, 11.0, 12.0]
    assert options["color_mode"] == "solvent"
    assert options["color_by"] == "solvent"
    assert options["solvent_distances"] == [0.2, 0.4, 0.6]
    assert isinstance(options["palette"], list)
    assert options["palette"] == options["color_map"]
    assert len(options["palette"]) > 2
    assert options["radial_segments"] == 12
    assert options["smoothing_subdivisions"] == 2
    assert options["alpha"] == 0.8
    assert options["tag"] == "tube"
    assert options["layer_tag"] == "tube"
    assert options["name"] == "demo"


def test_add_channel_tube_accepts_color_by_and_palette():
    view = DummyView()
    tubes = ChannelTubes(view)

    tubes.add_channel_tube(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1), (2, 1, 0)], "nm"),
        radii=puw.quantity([1.0, 1.1, 1.2], "nm"),
        color_by="solvent",
        solvent_distances=[0.2, 0.4, 0.6],
        palette=["red", "#00ff00", (0, 0, 255)],
        tag="tube",
        skip_digestion=True,
    )

    options = view.messages[0]["options"]
    assert options["color_by"] == "solvent"
    assert options["color_mode"] == "solvent"
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["color_map"] == [0xFF0000, 0x00FF00, 0x0000FF]


def test_add_channel_tube_requires_two_points():
    view = DummyView()
    tubes = ChannelTubes(view)
    try:
        tubes.add_channel_tube(centers=puw.quantity([(0, 0, 0)], "nm"), radii=puw.quantity([1.0], "nm"))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for insufficient centers")
