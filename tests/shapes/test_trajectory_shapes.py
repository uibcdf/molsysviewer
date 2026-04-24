"""Tests for structure-aware shape coordinates (structures_coords) and add_hbonds.

Verifies that add_sphere, add_triangle_faces, add_links, and add_channel_tube
accept per-structure coordinate arrays and include structures_coords in the sent message.
Also tests add_hbonds with per-structure atom-index pairs.
"""

import numpy as np
import pyunitwizard as puw

from molsysviewer.shapes.spheres import SphereShapes
from molsysviewer.shapes.triangle_faces import TriangleFaces
from molsysviewer.shapes.links import LinkShapes
from molsysviewer.shapes.channel_tubes import ChannelTubes


class DummyView:
    def __init__(self):
        self.messages = []
        self._shape_counter = 0
        self._layer_counter = 0
        self._scene_objects = {}

    def _send(self, msg):
        self.messages.append(msg)

    def _next_shape_tag(self):
        self._shape_counter += 1
        return f"shape{self._shape_counter}"

    def _next_layer_tag(self):
        self._layer_counter += 1
        return f"layer{self._layer_counter}"

    def _ensure_layer_group(self, *args, **kwargs):
        pass


def test_add_sphere_includes_structures_coords_in_message():
    view = DummyView()
    shapes = SphereShapes(view)

    centers = puw.quantity([[0, 0, 0], [1, 1, 1], [2, 2, 2]], "angstroms")
    shapes.add_sphere(
        center=puw.quantity([0, 0, 0], "angstroms"),
        radius=puw.quantity(5.0, "angstroms"),
        structure_centers=centers,
        tag="s1",
    )

    assert len(view.messages) == 1
    opts = view.messages[0]["options"]
    assert "structures_coords" in opts
    assert len(opts["structures_coords"]) == 3
    assert opts["structures_coords"][0] == [0.0, 0.0, 0.0]
    assert opts["structures_coords"][1] == [1.0, 1.0, 1.0]
    assert opts["structures_coords"][2] == [2.0, 2.0, 2.0]


def test_add_sphere_without_structure_centers_has_no_structures_coords():
    view = DummyView()
    shapes = SphereShapes(view)

    shapes.add_sphere(
        center=puw.quantity([0, 0, 0], "angstroms"),
        radius=puw.quantity(5.0, "angstroms"),
        tag="s1",
    )

    opts = view.messages[0]["options"]
    assert "structures_coords" not in opts


def test_add_triangle_faces_includes_structures_coords():
    view = DummyView()
    tris = TriangleFaces(view)

    frame0 = [[[0, 0, 0], [1, 0, 0], [0, 1, 0]]]
    frame1 = [[[0, 0, 1], [1, 0, 1], [0, 1, 1]]]
    structures = [frame0, frame1]

    tris.add_triangle_faces(structure_vertices=structures, tag="t1")

    opts = view.messages[0]["options"]
    assert "structures_coords" in opts
    assert len(opts["structures_coords"]) == 2
    # Structure 0 vertices should be set as the initial vertices too
    assert "vertices" in opts


def test_add_links_includes_structures_coords():
    view = DummyView()
    links = LinkShapes(view)

    frame0_pairs = [[[0, 0, 0], [1, 0, 0]]]
    frame1_pairs = [[[0, 0, 1], [1, 0, 1]]]

    links.add_links(
        structure_coordinate_pairs=[frame0_pairs, frame1_pairs],
        tag="l1",
    )

    opts = view.messages[0]["options"]
    assert "structures_coords" in opts
    assert len(opts["structures_coords"]) == 2
    # Structure 0 coordinate_pairs should be set as the initial coords
    assert "coordinate_pairs" in opts


def test_add_links_structure_none_passes_null_to_message():
    view = DummyView()
    links = LinkShapes(view)

    frame0_pairs = [[[0, 0, 0], [1, 0, 0]]]

    links.add_links(
        structure_coordinate_pairs=[frame0_pairs, None],
        tag="l2",
    )

    opts = view.messages[0]["options"]
    assert opts["structures_coords"][1] is None
    assert opts["structures_coords"][0] is not None


def test_add_channel_tube_includes_structures_coords():
    view = DummyView()
    tubes = ChannelTubes(view)

    centers_struct0 = [[0, 0, 0], [1, 1, 1], [2, 2, 2]]
    centers_struct1 = [[0, 0, 1], [1, 1, 2], [2, 2, 3]]

    tubes.add_channel_tube(
        centers=puw.quantity(centers_struct0, "angstroms"),
        radii=puw.quantity([1.0, 1.0, 1.0], "angstroms"),
        structure_centers=[centers_struct0, centers_struct1],
        tag="tube1",
    )

    opts = view.messages[0]["options"]
    assert "structures_coords" in opts
    assert len(opts["structures_coords"]) == 2
    assert len(opts["structures_coords"][0]) == 3  # 3 centers per structure


def test_add_hbonds_includes_structures_atom_pairs():
    view = DummyView()
    links = LinkShapes(view)

    links.add_hbonds(
        structures=[
            None,
            [[3, 7], [8, 35]],
            None,
            [[1, 9], [24, 27]],
        ],
        tag="hb1",
    )

    assert len(view.messages) == 1
    msg = view.messages[0]
    assert msg["op"] == "add_hbonds"
    opts = msg["options"]
    assert "structures_atom_pairs" in opts
    assert len(opts["structures_atom_pairs"]) == 4
    assert opts["structures_atom_pairs"][0] is None
    assert opts["structures_atom_pairs"][1] == [[3, 7], [8, 35]]
    assert opts["structures_atom_pairs"][2] is None
    assert opts["structures_atom_pairs"][3] == [[1, 9], [24, 27]]


def test_add_hbonds_empty_structure_is_none():
    view = DummyView()
    links = LinkShapes(view)

    links.add_hbonds(structures=[[[0, 1]], None], tag="hb2")

    opts = view.messages[0]["options"]
    assert opts["structures_atom_pairs"][1] is None
    assert opts["structures_atom_pairs"][0] == [[0, 1]]
