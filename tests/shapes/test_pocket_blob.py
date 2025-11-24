from molsysviewer.shapes import PocketBlobs


class DummyView:
    def __init__(self) -> None:
        self.messages = []

    def _send(self, message):
        self.messages.append(message)


def test_add_pocket_blob_message():
    view = DummyView()
    blobs = PocketBlobs(view)

    blobs.add_pocket_blob(
        centers=[(0, 0, 0), (1, 1, 1)],
        radii=[1.0, 1.5],
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
                "centers": [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
                "radii": [1.0, 1.5],
                "radius_scale": 1.1,
                "resolution": 0.5,
                "iso_level": 0.2,
                "smoothing": 1.2,
                "values": [0.1, 0.9],
                "color_map": "viridis",
                "alpha": 0.4,
                "tag": "blob",
                "name": "demo",
            },
        }
    ]


def test_add_pocket_blob_validates_lengths():
    view = DummyView()
    blobs = PocketBlobs(view)

    try:
        blobs.add_pocket_blob(centers=[(0, 0, 0)], radii=[1.0, 2.0])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for mismatched lengths")
