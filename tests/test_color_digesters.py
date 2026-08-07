"""Unit tests for the color-operation argument digesters.

These cover the ArgDigest contract for ``value_range`` and ``replace``, the two
arguments the public scalar-color methods declare and use but previously had no
digester for (see ``devguide/pending_bugs/missing_argdigest_color_digesters.md``).
"""

from __future__ import annotations

import numpy as np
import pytest

from molsysviewer._private.argdigest.argument.color_scheme import digest_color_scheme
from molsysviewer._private.argdigest.argument.replace import digest_replace
from molsysviewer._private.argdigest.argument.scheme import digest_scheme
from molsysviewer._private.argdigest.argument.value_range import digest_value_range
from molsysviewer._private.exceptions import ArgumentError


# --- value_range -----------------------------------------------------------

def test_value_range_none_is_inferred():
    assert digest_value_range(None) is None


@pytest.mark.parametrize(
    "given, expected",
    [
        ([0, 1], [0.0, 1.0]),
        ((0.0, 2.5), [0.0, 2.5]),
        ([-3, 7], [-3.0, 7.0]),
        ([3, 3], [3.0, 3.0]),  # equal bounds are valid: the mapper handles zero span
        (np.array([1.0, 4.0]), [1.0, 4.0]),  # 1-D numpy arrays are accepted
    ],
)
def test_value_range_valid_is_normalized_to_float_pair(given, expected):
    result = digest_value_range(given)
    assert result == expected
    assert all(isinstance(v, float) for v in result)


@pytest.mark.parametrize(
    "given",
    [
        [1],  # too short
        [1, 2, 3],  # too long
        [2, 1],  # reversed bounds
        [float("nan"), 1.0],  # non-finite
        [float("inf"), 1.0],  # non-finite
        [True, 1],  # booleans are not numbers here
        ["a", "b"],  # non-numeric
        np.array([[1, 2], [3, 4]]),  # multidimensional
        5,  # scalar, not a pair
        "01",  # string of length 2 is not a numeric pair
    ],
)
def test_value_range_invalid_raises_argument_error(given):
    with pytest.raises(ArgumentError):
        digest_value_range(given)


# --- replace ---------------------------------------------------------------

@pytest.mark.parametrize("given", [True, False])
def test_replace_accepts_bool_unchanged(given):
    assert digest_replace(given) is given


@pytest.mark.parametrize("given", [1, 0, "true", "", None, 1.0])
def test_replace_rejects_non_bool(given):
    with pytest.raises(ArgumentError):
        digest_replace(given)


# --- scheme / color_scheme -------------------------------------------------

@pytest.mark.parametrize(
    "given, expected",
    [
        # canonical tags resolve to themselves
        ("chain_default", "chain_default"),
        ("element_cpk", "element_cpk"),
        ("molecule_type", "molecule_type"),
        ("group_name", "group_name"),  # MolSysSuite term, canonical
        # Mol* theme names (derived from the registry's molstar_theme field)
        ("chain-id", "chain_default"),
        ("element-symbol", "element_cpk"),
        ("residue-name", "group_name"),
        ("secondary-structure", "secondary_structure_default"),
        ("entity-id", "entity_default"),
        # MolSysMT attribute vocabulary
        ("chain_id", "chain_default"),
        ("residue_name", "group_name"),  # tolerated spelling
        ("entity_id", "entity_default"),
        ("element", "element_cpk"),
        # whitespace tolerated
        ("  chain-id  ", "chain_default"),
    ],
)
def test_scheme_resolves_synonyms_to_canonical_tag(given, expected):
    assert digest_scheme(given) == expected


@pytest.mark.parametrize("given", [None, "", "   ", 5, ["chain-id"], "nope", "chainid"])
def test_scheme_rejects_unknown_or_non_string(given):
    # Previously any non-empty string was accepted and then silently ignored by
    # the frontend, so an unrecognized scheme did nothing at all.
    with pytest.raises(ArgumentError):
        digest_scheme(given)


def test_scheme_error_lists_valid_options():
    with pytest.raises(ArgumentError, match="Valid color schemes"):
        digest_scheme("definitely-not-a-scheme")


def test_color_scheme_param_resolves_structural_synonyms():
    assert digest_color_scheme(None) is None
    assert digest_color_scheme("chain-id") == "chain_default"
    assert digest_color_scheme("residue_name") == "group_name"


def test_color_scheme_param_passes_through_non_structural_schemes():
    # `color_scheme` is shared with shape/pharmacophore visuals, which use their
    # own vocabulary, so unknown names must not be rejected here (only `scheme`,
    # which is structural-only, validates strictly).
    assert digest_color_scheme("pharmacophore_default") == "pharmacophore_default"
    assert digest_color_scheme("pocket_default") == "pocket_default"


def test_color_scheme_rejects_non_string():
    with pytest.raises(ArgumentError):
        digest_color_scheme(5)
