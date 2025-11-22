from molsysviewer.shapes import SphereShapes


class DummyView:
    def __init__(self) -> None:
        self.messages = []

    def _send(self, message):
        self.messages.append(message)


def test_add_set_alpha_spheres_message():
    view = DummyView()
    spheres = SphereShapes(view)

    centers = [(0, 0, 0), (1, 1, 1)]
    radii = [1.0, 1.5]
    atom_centers = [(2, 2, 2)]

    spheres.add_set_alpha_spheres(
        centers=centers,
        radii=radii,
        atom_centers=atom_centers,
        atom_radius=0.8,
        color_alpha_spheres=0x111111,
        color_atoms=0x222222,
        alpha_alpha_spheres=0.2,
        alpha_atoms=0.6,
        tag="group-1",
    )

    assert view.messages == [
        {
            "op": "add_alpha_sphere_set",
            "options": {
                "alpha_spheres": {
                    "centers": [[0, 0, 0], [1, 1, 1]],
                    "radii": [1.0, 1.5],
                    "color": 0x111111,
                    "alpha": 0.2,
                },
                "atom_spheres": {
                    "centers": [[2, 2, 2]],
                    "radius": 0.8,
                    "color": 0x222222,
                    "alpha": 0.6,
                },
                "tag": "group-1",
            },
        }
    ]


def test_add_set_alpha_spheres_requires_matching_lengths():
    view = DummyView()
    spheres = SphereShapes(view)
    try:
        spheres.add_set_alpha_spheres(centers=[(0, 0, 0)], radii=[1.0, 2.0])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for mismatched lengths")
