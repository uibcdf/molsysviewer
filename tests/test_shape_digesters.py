"""Digesters for the shape arguments found by the boundary audit.

All of these are declared on `@digest()`-decorated public shape methods and had
no digester, so every call emitted `DigestNotDigestedWarning`.
"""

from __future__ import annotations

import numpy as np
import pytest

from molsysviewer._private.arg_digestion.argument.alpha_atoms import digest_alpha_atoms
from molsysviewer._private.arg_digestion.argument.atom_quads import digest_atom_quads
from molsysviewer._private.arg_digestion.argument.atom_triplets import digest_atom_triplets
from molsysviewer._private.arg_digestion.argument.color_component import digest_color_component
from molsysviewer._private.arg_digestion.argument.directions import digest_directions
from molsysviewer._private.arg_digestion.argument.draw_edges import digest_draw_edges
from molsysviewer._private.arg_digestion.argument.edge_color import digest_edge_color
from molsysviewer._private.arg_digestion.argument.exterior_only import digest_exterior_only
from molsysviewer._private.arg_digestion.argument.kinds import digest_kinds
from molsysviewer._private.arg_digestion.argument.length_scale import digest_length_scale
from molsysviewer._private.arg_digestion.argument.normals import digest_normals
from molsysviewer._private.arg_digestion.argument.segments import digest_segments
from molsysviewer._private.arg_digestion.argument.structures_atom_indices import (
    digest_structures_atom_indices,
)
from molsysviewer._private.exceptions import ArgumentError


# --- optional boolean flags -------------------------------------------------

def test_optional_flag_passes_none_through_to_the_shape_default():
    assert digest_draw_edges(None) is None
    assert digest_draw_edges(True) is True
    assert digest_draw_edges(False) is False


@pytest.mark.parametrize("given", [1, 0, "yes", ""])
def test_optional_flag_rejects_truthy_non_booleans(given):
    # numbers and strings would silently read as truthy
    with pytest.raises(ArgumentError):
        digest_draw_edges(given)


def test_required_flag_rejects_none():
    assert digest_exterior_only(True) is True
    with pytest.raises(ArgumentError):
        digest_exterior_only(None)


# --- colors -----------------------------------------------------------------

def test_edge_color_normalizes_colour_forms():
    assert digest_edge_color(None) is None
    assert digest_edge_color(0xFF0000) == 0xFF0000
    assert digest_edge_color("red") == digest_edge_color("#ff0000")


def test_edge_color_rejects_nonsense():
    with pytest.raises(ArgumentError):
        digest_edge_color("not a colour")


# --- opacities --------------------------------------------------------------

@pytest.mark.parametrize("given, expected", [(0, 0.0), (0.3, 0.3), (1, 1.0)])
def test_opacity_accepts_range(given, expected):
    assert digest_alpha_atoms(given) == expected


@pytest.mark.parametrize("given", [-0.1, 1.2, True, "0.5"])
def test_opacity_rejects_out_of_range_and_booleans(given):
    with pytest.raises(ArgumentError):
        digest_alpha_atoms(given)


# --- fixed-size index groups ------------------------------------------------

def test_index_groups_accept_lists_and_numpy():
    assert digest_atom_quads([[0, 1, 2, 3]]) == [[0, 1, 2, 3]]
    assert digest_atom_quads(np.array([[0, 1, 2, 3]])) == [[0, 1, 2, 3]]
    assert digest_atom_triplets([[0, 1, 2], (3, 4, 5)]) == [[0, 1, 2], [3, 4, 5]]
    assert digest_atom_quads(None) is None


@pytest.mark.parametrize(
    "given",
    [
        [[0, 1, 2]],          # wrong group size for quads
        [[0, 1, 2, 3, 4]],    # wrong group size for quads
        [[0, 1, 2, -1]],      # negative index
        [[0, 1, 2, 1.5]],     # non-integer
        [[0, 1, 2, True]],    # boolean masquerading as an index
        [],                   # nothing to draw
        "0123",
    ],
)
def test_index_groups_reject_malformed_geometry(given):
    with pytest.raises(ArgumentError):
        digest_atom_quads(given)


def test_structures_atom_indices_allows_an_empty_structure():
    # an empty list hides the shape on that structure; None does the same
    assert digest_structures_atom_indices([[0, 1], [], None]) == [[0, 1], [], None]
    assert digest_structures_atom_indices(None) is None


# --- 3D vectors -------------------------------------------------------------

def test_vectors_accept_lists_and_numpy():
    assert digest_normals([[0.0, 0.0, 1.0]]) == [[0.0, 0.0, 1.0]]
    assert digest_directions(np.array([[1.0, 0.0, 0.0]])) == [[1.0, 0.0, 0.0]]
    assert digest_normals(None) is None


@pytest.mark.parametrize(
    "given",
    [
        [[0.0, 1.0]],                   # not 3D
        [[0.0, 0.0, 0.0, 0.0]],         # not 3D
        [[0.0, 0.0, float("nan")]],     # non-finite would be degenerate geometry
        [[0.0, 0.0, float("inf")]],
        [],
    ],
)
def test_vectors_reject_degenerate_input(given):
    with pytest.raises(ArgumentError):
        digest_normals(given)


# --- the remaining scalars --------------------------------------------------

def test_segments_needs_at_least_three():
    assert digest_segments(None) is None
    assert digest_segments(24) == 24
    for bad in (2, 0, -3, 24.0, True):
        with pytest.raises(ArgumentError):
            digest_segments(bad)


def test_kinds_is_a_non_empty_sequence_of_labels():
    assert digest_kinds(["donor", "  acceptor "]) == ["donor", "acceptor"]
    for bad in ([], ["donor", ""], ["donor", 5], "donor"):
        with pytest.raises(ArgumentError):
            digest_kinds(bad)


def test_length_scale_must_be_positive():
    assert digest_length_scale(2.0) == 2.0
    for bad in (0, -1.0, float("inf"), True, "2"):
        with pytest.raises(ArgumentError):
            digest_length_scale(bad)


def test_color_component_is_an_axis_index():
    for axis in (0, 1, 2):
        assert digest_color_component(axis) == axis
    for bad in (3, -1, 1.0, True, "z"):
        with pytest.raises(ArgumentError):
            digest_color_component(bad)
