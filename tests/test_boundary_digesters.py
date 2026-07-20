"""Digesters for public arguments that previously had none.

Found by the Python↔JS boundary audit (`devguide/python_js_boundary_audit_2026_07.md`):
these arguments are declared on `@digest()`-decorated public methods, so every
ordinary call emitted `DigestNotDigestedWarning` and the contract went
unvalidated.
"""

from __future__ import annotations

import pytest

from molsysviewer._private.arg_digestion.argument.fade import digest_fade
from molsysviewer._private.arg_digestion.argument.layer import digest_layer
from molsysviewer._private.arg_digestion.argument.meta import digest_meta
from molsysviewer._private.arg_digestion.argument.region import digest_region
from molsysviewer._private.arg_digestion.argument.target import digest_target
from molsysviewer._private.arg_digestion.argument.transaction_id import digest_transaction_id
from molsysviewer._private.exceptions import ArgumentError


class _Tagged:
    """Stands in for a Region/Layer object, which are identified by their tag."""

    def __init__(self, tag: str) -> None:
        self.tag = tag


# --- region ----------------------------------------------------------------

def test_region_accepts_a_tag_or_a_region_object():
    assert digest_region("pocket") == "pocket"
    assert digest_region("  pocket  ") == "pocket"
    obj = _Tagged("pocket")
    assert digest_region(obj) is obj


@pytest.mark.parametrize("given", [None, "", "   ", 5, object()])
def test_region_rejects_empty_or_unrelated_values(given):
    with pytest.raises(ArgumentError):
        digest_region(given)


# --- fade ------------------------------------------------------------------

@pytest.mark.parametrize("given, expected", [(0, 0.0), (0.85, 0.85), (1, 1.0)])
def test_fade_accepts_transparencies_in_range(given, expected):
    assert digest_fade(given) == expected


@pytest.mark.parametrize("given", [-0.1, 1.5, True, False, "0.5", None])
def test_fade_rejects_values_outside_a_transparency(given):
    # booleans are ints in Python but are not meaningful transparencies
    with pytest.raises(ArgumentError):
        digest_fade(given)


# --- meta ------------------------------------------------------------------

def test_meta_accepts_none_and_copies_mappings():
    assert digest_meta(None) is None
    source = {"author": "lab"}
    result = digest_meta(source)
    assert result == source
    # a copy, so later mutation of the caller's dict cannot alter stored state
    source["author"] = "someone else"
    assert result == {"author": "lab"}


@pytest.mark.parametrize("given", ["meta", 5, ["a", "b"]])
def test_meta_rejects_non_mappings(given):
    with pytest.raises(ArgumentError):
        digest_meta(given)


# --- layer -----------------------------------------------------------------

def test_layer_accepts_none_a_tag_or_a_layer_object():
    assert digest_layer(None) is None      # detaches from the current layer
    assert digest_layer("  surface  ") == "surface"
    obj = _Tagged("surface")
    assert digest_layer(obj) is obj


@pytest.mark.parametrize("given", ["", "   ", 5, object()])
def test_layer_rejects_empty_or_unrelated_values(given):
    with pytest.raises(ArgumentError):
        digest_layer(given)


# --- target ----------------------------------------------------------------

def test_target_is_normalized_for_lookup():
    assert digest_target("  Group  ") == "group"
    assert digest_target("MOLECULE") == "molecule"


@pytest.mark.parametrize("given", [None, "", "   ", 5])
def test_target_rejects_empty_or_non_string(given):
    with pytest.raises(ArgumentError):
        digest_target(given)


# --- transaction_id --------------------------------------------------------

def test_transaction_id_accepts_none_ints_and_strings():
    assert digest_transaction_id(None) is None
    assert digest_transaction_id(42) == 42
    assert digest_transaction_id("  tx-1  ") == "tx-1"


@pytest.mark.parametrize("given", ["", "   ", True, False, 1.5, []])
def test_transaction_id_rejects_empty_or_unusable_values(given):
    with pytest.raises(ArgumentError):
        digest_transaction_id(given)
