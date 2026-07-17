"""Unit tests for the color-operation argument digesters.

These cover the ArgDigest contract for ``value_range`` and ``replace``, the two
arguments the public scalar-color methods declare and use but previously had no
digester for (see ``devguide/pending_bugs/missing_argdigest_color_digesters.md``).
"""

from __future__ import annotations

import numpy as np
import pytest

from molsysviewer._private.arg_digestion.argument.replace import digest_replace
from molsysviewer._private.arg_digestion.argument.value_range import digest_value_range
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
