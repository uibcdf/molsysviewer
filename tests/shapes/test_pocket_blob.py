import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer.shapes import PocketBlobs


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


def test_add_pocket_blob_message():
    view = DummyView()
    blobs = PocketBlobs(view)

    blobs.add_pocket_blob(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1)], "nm"),
        radii=puw.quantity([1.0, 1.5], "nm"),
        radius_scale=1.1,
        resolution=0.5,
        iso_level=0.2,
        smoothing=1.2,
        values=[0.1, 0.9],
        color_map="viridis",
        alpha=0.4,
        tag="blob",
        name="demo",
    )

    assert view.messages == [
        {
            "op": "add_pocket_blob",
            "options": {
                "centers": [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]],
                "radii": [10.0, 15.0],
                "radius_scale": 1.1,
                "resolution": 0.5,
                "iso_level": 0.2,
                "smoothing": 1.2,
                "values": [0.1, 0.9],
                "color_map": "viridis",
                "alpha": 0.4,
                "tag": "blob",
                "layer_tag": "blob",
                "name": "demo",
            },
        }
    ]


def test_add_pocket_blob_validates_lengths():
    view = DummyView()
    blobs = PocketBlobs(view)

    try:
        blobs.add_pocket_blob(centers=puw.quantity([(0, 0, 0)], "nm"), radii=puw.quantity([1.0, 2.0], "nm"))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for mismatched lengths")
