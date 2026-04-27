import warnings
import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer.shapes import PharmacophoreShapes, ShapesManager


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


def test_add_interaction_sites():
    view = DummyView()
    ph4 = PharmacophoreShapes(view)

    ph4.add_interaction_sites(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1)], "nm"),
        kinds=["donor", "acceptor"],
        radii=puw.quantity([0.5, 0.6], "nm"),
        alphas=[0.4, 0.5],
        directions=[(1, 0, 0), (0, 1, 0)],
        tag="ph4",
        name="demo",
        skip_digestion=True,
    )

    assert view.messages == [
        {
            "op": "add_pharmacophore_features",
            "options": {
                "centers": [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]],
                "kinds": ["donor", "acceptor"],
                "radii": [5.0, 6.0],
                "alphas": [0.4, 0.5],
                "colors": [0x3b82f6, 0xef4444],
                "directions": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                "tag": "ph4",
                "layer_tag": "ph4",
                "name": "demo",
            },
        }
    ]


def test_add_interaction_sites_accepts_color_scheme_and_color_table():
    view = DummyView()
    ph4 = PharmacophoreShapes(view)

    ph4.add_interaction_sites(
        centers=puw.quantity([(0, 0, 0), (1, 1, 1)], "nm"),
        kinds=["donor", "acceptor"],
        color_scheme="pharmacophore_default",
        color_table={"donor": "white", "acceptor": "#112233"},
        tag="ph4",
        skip_digestion=True,
    )

    options = view.messages[0]["options"]
    assert options["color_scheme"] == "pharmacophore_default"
    assert options["color_table"] == {"donor": 0xFFFFFF, "acceptor": 0x112233}
    assert options["colors"] == [0xFFFFFF, 0x112233]


def test_add_pharmacophore_features_warns_and_uses_same_payload():
    view = DummyView()
    ph4 = PharmacophoreShapes(view)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ph4.add_pharmacophore_features(
            centers=puw.quantity([(0, 0, 0)], "nm"),
            kinds=["donor"],
            tag="ph4",
            skip_digestion=True,
        )

    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "add_interaction_sites" in str(caught[0].message)
    assert view.messages == [
        {
            "op": "add_pharmacophore_features",
            "options": {
                "centers": [[0.0, 0.0, 0.0]],
                "kinds": ["donor"],
                "radii": [0.6],
                "alphas": [0.6],
                "colors": [0x3b82f6],
                "tag": "ph4",
                "layer_tag": "ph4",
            },
        }
    ]


def test_shapes_manager_exposes_interaction_sites():
    view = DummyView()
    shapes = ShapesManager(view)

    assert isinstance(shapes.interaction_sites, PharmacophoreShapes)
    assert not hasattr(shapes, "ph4")
