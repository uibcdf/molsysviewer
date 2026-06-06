import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer.shapes import Rings


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


def test_add_rings_message():
    view = DummyView()
    rings = Rings(view)

    rings.add_rings(
        centers=puw.quantity([(0, 0, 0), (0, 0, 1)], "nm"),
        normals=[(0, 0, 1), (0, 0, 1)],
        radii=puw.quantity([1.0, 0.8], "nm"),
        thickness=puw.quantity(0.05, "nm"),
        colors=[0xE69F00, 0xE69F00],
        segments=24,
        alpha=0.7,
        tag="rings",
        name="profile",
    )

    assert view.messages[0]["op"] == "add_rings"
    options = view.messages[0]["options"]
    assert options["centers"] == [[0.0, 0.0, 0.0], [0.0, 0.0, 10.0]]
    assert options["normals"] == [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]
    assert options["radii"] == [10.0, 8.0]
    assert options["thickness"] == [0.5, 0.5]
    assert options["colors"] == [0xE69F00, 0xE69F00]
    assert options["segments"] == 24
    assert options["alpha"] == 0.7
    assert options["tag"] == "rings"
    assert options["layer_tag"] == "rings"
    assert options["name"] == "profile"


def test_add_rings_scalar_coloring():
    view = DummyView()
    rings = Rings(view)

    rings.add_rings(
        centers=puw.quantity([(0, 0, 0), (0, 0, 1), (0, 0, 2)], "nm"),
        normals=[(0, 0, 1)] * 3,
        radii=puw.quantity([1.0, 0.5, 1.2], "nm"),
        color_by="clearance",
        values=[1.0, 0.5, 1.2],
        palette=["red", "#00ff00", (0, 0, 255)],
        skip_digestion=True,
    )

    options = view.messages[0]["options"]
    assert options["color_by"] == "clearance"
    assert options["color_mode"] == "clearance"
    assert options["values"] == [1.0, 0.5, 1.2]
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["palette"] == options["color_map"]


def test_add_rings_length_mismatch_raises():
    view = DummyView()
    rings = Rings(view)
    try:
        rings.add_rings(
            centers=puw.quantity([(0, 0, 0), (0, 0, 1)], "nm"),
            normals=[(0, 0, 1)],
            radii=puw.quantity([1.0, 0.8], "nm"),
            skip_digestion=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for mismatched lengths")


def test_add_rings_requires_at_least_one():
    view = DummyView()
    rings = Rings(view)
    try:
        rings.add_rings(
            centers=puw.quantity([], "nm"),
            normals=[],
            radii=puw.quantity([], "nm"),
            skip_digestion=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty rings")
