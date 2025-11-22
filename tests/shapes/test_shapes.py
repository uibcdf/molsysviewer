import pytest

from molsysviewer.shapes import ShapesManager, SphereShapes


class DummyView:
    def __init__(self) -> None:
        self.messages = []

    def _send(self, message):
        self.messages.append(message)


def test_shapes_exports_and_delegation(monkeypatch):
    view = DummyView()
    manager = ShapesManager(view)

    called = {}

    def fake_add_sphere(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs

    monkeypatch.setattr(manager.spheres, "add_sphere", fake_add_sphere)

    manager.add_sphere(center=(1, 2, 3), radius=5)
    assert called["kwargs"]["center"] == (1, 2, 3)
    assert called["kwargs"]["radius"] == 5


def test_add_sphere_sends_message():
    view = DummyView()
    shapes = SphereShapes(view)
    shapes.add_sphere(center=(1, 2, 3), radius=2.5, color=0x123456, alpha=0.7, tag="foo")

    assert view.messages == [
        {
            "op": "add_sphere",
            "options": {
                "center": [1, 2, 3],
                "radius": 2.5,
                "color": 0x123456,
                "alpha": 0.7,
                "tag": "foo",
            },
        }
    ]


def test_add_spheres_broadcasts_and_validates():
    view = DummyView()
    shapes = SphereShapes(view)

    centers = [(0, 0, 0), (1, 1, 1)]
    shapes.add_spheres(centers, radii=[1.0, 2.0], colors=0x00FF00, alphas=[0.1, 0.2])

    assert len(view.messages) == 2
    assert view.messages[0]["options"]["radius"] == 1.0
    assert view.messages[1]["options"]["radius"] == 2.0

    with pytest.raises(ValueError):
        shapes.add_spheres(centers, radii=[1.0], colors=[0xFFFFFF, 0x000000], alphas=0.5)
