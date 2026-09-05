from molsysviewer.shapes import ShapesManager


class DummyLayer:
    def __init__(self, tag, layer_tag):
        self.tag = tag
        self.layer_tag = layer_tag


class DummyView:
    def __init__(self) -> None:
        self.messages = []
        self._layers = {}
        self._scene_objects = {}
        self._layer_counter = 0

    def _send(self, message):
        self.messages.append(message)

    def _next_layer_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"

    def _next_shape_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"


class MockFeature:
    def __init__(self, feature_type, **kwargs):
        self.feature_type = feature_type
        self._topography = None
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockTopography:
    def __init__(self):
        self.features = {}


def test_add_topomt_feature_pocket():
    view = DummyView()
    mgr = ShapesManager(view)

    # 1. Test Pocket without boundaries
    pocket = MockFeature("pocket", atom_indices=[10, 11, 12])
    mgr.add_topomt_feature(pocket)

    assert len(view.messages) == 1
    assert view.messages[0]["op"] == "add_pocket_surface"
    assert view.messages[0]["options"]["atom_indices"] == [10, 11, 12]
    assert "mouth_atom_indices" not in view.messages[0]["options"]

    # 2. Test Pocket with boundaries and topography
    topo = MockTopography()
    mouth = MockFeature("mouth", atom_indices=[5, 6])
    topo.features["MOU-1"] = mouth

    pocket_with_mouth = MockFeature("pocket", atom_indices=[10, 11, 12], boundaries=["MOU-1"])
    pocket_with_mouth._topography = topo

    mgr.add_topomt_feature(pocket_with_mouth)
    assert len(view.messages) == 2
    assert view.messages[1]["op"] == "add_pocket_surface"
    assert view.messages[1]["options"]["atom_indices"] == [10, 11, 12]
    assert view.messages[1]["options"]["mouth_atom_indices"] == [[5, 6]]


def test_add_topomt_feature_channel():
    view = DummyView()
    mgr = ShapesManager(view)

    # Test Channel with centers and radii
    channel = MockFeature(
        "channel",
        centers=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
        radii=[1.5, 2.5]
    )
    mgr.add_topomt_feature(channel)

    assert len(view.messages) == 1
    assert view.messages[0]["op"] == "add_channel_tube"
    assert view.messages[0]["options"]["centers"] == [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]]  # angstrom conversion!
    assert view.messages[0]["options"]["radii"] == [15.0, 25.0]  # angstrom conversion!


def test_add_topomt_feature_mouth_boundary():
    view = DummyView()
    mgr = ShapesManager(view)

    # Test Mouth as a boundary (with atom_indices but no points)
    mouth = MockFeature("mouth", atom_indices=[20, 21])
    mgr.add_topomt_feature(mouth)

    assert len(view.messages) == 1
    assert view.messages[0]["op"] == "add_pocket_surface"
    assert view.messages[0]["options"]["atom_indices"] == [20, 21]
