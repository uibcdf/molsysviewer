import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer.shapes import AnisotropyEllipsoids


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


def test_add_anisotropy_ellipsoids_message():
    view = DummyView()
    ell = AnisotropyEllipsoids(view)

    ell.add_anisotropy_ellipsoids(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1)], "nm"),
        eigenvalues=[(1.0, 0.5, 0.2), (0.8, 0.4, 0.1)],
        eigenvectors=[
            [(1, 0, 0), (0, 1, 0), (0, 0, 1)],
            [(0, 1, 0), (1, 0, 0), (0, 0, 1)],
        ],
        scale=2.0,
        max_eccentricity=5.0,
        color_mode="anisotropy",
        color_map="magma",
        alpha=0.5,
        tag="ell",
        name="demo",
    )

    assert view.messages[0]["op"] == "add_anisotropy_ellipsoids"
    options = view.messages[0]["options"]
    assert options["centers"] == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
    assert options["eigenvalues"] == [[1.0, 0.5, 0.2], [0.8, 0.4, 0.1]]
    assert options["eigenvectors"] == [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    ]
    assert options["scale"] == 2.0
    assert options["max_eccentricity"] == 5.0
    assert options["color_mode"] == "anisotropy"
    assert options["color_by"] == "anisotropy"
    assert isinstance(options["palette"], list)
    assert options["palette"] == options["color_map"]
    assert len(options["palette"]) > 2
    assert options["alpha"] == 0.5
    assert options["tag"] == "ell"
    assert options["layer_tag"] == "ell"
    assert options["name"] == "demo"


def test_add_anisotropy_ellipsoids_accepts_color_by_and_palette():
    view = DummyView()
    ell = AnisotropyEllipsoids(view)

    ell.add_anisotropy_ellipsoids(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1)], "nm"),
        principal_directions=[(1, 0, 0), (0, 1, 0)],
        color_by="anisotropy",
        palette=["red", "#00ff00", (0, 0, 255)],
        tag="ell",
        skip_digestion=True,
    )

    options = view.messages[0]["options"]
    assert options["color_by"] == "anisotropy"
    assert options["color_mode"] == "anisotropy"
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["color_map"] == [0xFF0000, 0x00FF00, 0x0000FF]


def test_add_anisotropy_requires_centers():
    view = DummyView()
    ell = AnisotropyEllipsoids(view)
    try:
        ell.add_anisotropy_ellipsoids(centers=[])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty centers")
