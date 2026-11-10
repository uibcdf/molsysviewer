"""Call-binding and stability review, separate from scientific behavior tests."""

from __future__ import annotations

import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))
from public_api_contract import (  # noqa: E402
    BASELINE,
    build_contract,
    call_shape,
    classification,
    compare_contracts,
    encode_default,
)
from public_api_inventory import build_inventory  # noqa: E402


@pytest.fixture(scope="module")
def current():
    return build_contract()


def test_reviewed_public_contract_has_no_unreviewed_drift(current):
    before = json.loads(BASELINE.read_text())
    assert compare_contracts(before, current) == [], (
        "Review route, call-shape or stability changes before regenerating the independent baseline."
    )


def test_same_reachable_callable_inventory_has_additional_properties_and_constructors(current):
    expected = {row["path"] for row in build_inventory()["callables"]}
    assert {route for route, row in current["declarations"].items() if row["kind"] == "callable"} == expected
    declarations = current["declarations"]
    assert declarations["view.molsys"]["kind"] == "property"
    assert declarations["view.molsys"]["writable"] is False
    assert declarations["molsysviewer.AddonSpec"]["kind"] == "class"
    assert declarations["molsysviewer.tools.embed.IframeMarkup"]["constructor"] == {
        "kind": "inherited_builtin",
        "base": "builtins.str",
    }


def test_snapshot_is_deterministic_and_does_not_depend_on_object_addresses(current):
    second = build_contract()
    assert compare_contracts(current, second) == []
    assert current == second
    assert json.dumps(current, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)


@pytest.mark.parametrize(
    "route",
    [
        "view.interactions.attach",
        "view.save_session",
        "view.save_session_async",
        "molsysviewer.load_session",
        "view.addons.manager.presentations.prepare",
    ],
)
def test_experimental_boundaries_are_explicit(current, route):
    assert current["declarations"][route]["stability"] == "experimental"
    assert current["declarations"][route]["reason"]


def document(function):
    return {
        "declarations": {
            "example.operation": {
                "kind": "callable",
                **call_shape(function),
                "stability": "stable",
                "reason": "Binding control",
            }
        }
    }


def test_removed_keyword_default_and_parameter_kind_changes_are_detected():
    def original(first, second=2, *, enabled=False):
        pass

    def keyword_only(first, *, second=2, enabled=False):
        pass

    def changed_default(first, second=2, *, enabled=True):
        pass

    def removed(first, second=2):
        pass

    inspect.signature(original).bind(1, 2, enabled=True)
    with pytest.raises(TypeError):
        inspect.signature(keyword_only).bind(1, 2, enabled=True)
    with pytest.raises(TypeError):
        inspect.signature(removed).bind(1, enabled=True)
    for changed in (keyword_only, changed_default, removed):
        assert compare_contracts(document(original), document(changed))[0]["compatibility"] == "breaking"


def test_optional_keyword_extension_is_visible_but_old_calls_still_bind():
    def original(first, *, enabled=False):
        pass

    def extended(first, *, enabled=False, label=None):
        pass

    inspect.signature(original).bind(1, enabled=True)
    inspect.signature(extended).bind(1, enabled=True)
    changes = compare_contracts(document(original), document(extended))
    assert changes == [{"route": "example.operation", "change": "changed", "compatibility": "compatible_extension"}]


def test_inserted_optional_keyword_preserves_existing_bindings():
    def original(value, *, skip_digestion=False):
        pass

    def extended(value, *, observations=None, skip_digestion=False):
        pass

    old = inspect.signature(original).bind(1, skip_digestion=True)
    new = inspect.signature(extended).bind(1, skip_digestion=True)
    assert old.arguments == new.arguments
    assert compare_contracts(document(original), document(extended))[0]["compatibility"] == "compatible_extension"


def test_optional_keyword_with_variadic_arguments_keeps_their_meaning():
    def original(value, *tail, skip_digestion=False):
        pass

    def extended(value, *tail, observations=None, skip_digestion=False):
        pass

    def consumes_tail(value, observations=None, *tail, skip_digestion=False):
        pass

    old = inspect.signature(original).bind(1, 2, 3, skip_digestion=True)
    assert old.arguments == inspect.signature(extended).bind(1, 2, 3, skip_digestion=True).arguments
    assert old.arguments != inspect.signature(consumes_tail).bind(1, 2, 3, skip_digestion=True).arguments
    assert compare_contracts(document(original), document(extended))[0]["compatibility"] == "compatible_extension"
    assert compare_contracts(document(original), document(consumes_tail))[0]["compatibility"] == "breaking"


def test_positional_insertion_and_required_keyword_are_not_compatible_extensions():
    def original(first, second=2):
        pass

    def shifted(first, added=None, second=2):
        pass

    def required(first, second=2, *, added):
        pass

    assert inspect.signature(original).bind(1, 3).arguments != inspect.signature(shifted).bind(1, 3).arguments
    with pytest.raises(TypeError):
        inspect.signature(required).bind(1, 3)
    for changed in (shifted, required):
        assert compare_contracts(document(original), document(changed))[0]["compatibility"] == "breaking"


def test_keyword_only_reordering_is_visible_without_inventing_a_binding_break():
    def original(value, *, first=1, second=2):
        pass

    def reordered(value, *, second=2, first=1):
        pass

    assert (
        inspect.signature(original).bind(0, first=4, second=3).arguments
        == inspect.signature(reordered).bind(0, first=4, second=3).arguments
    )
    assert compare_contracts(document(original), document(reordered))[0]["compatibility"] == "compatible_reordering"


def test_classification_change_cannot_hide_a_breaking_change():
    def original(first, *, enabled=False):
        pass

    before = document(original)
    after = deepcopy(before)
    entry = after["declarations"]["example.operation"]
    entry["stability"] = "experimental"
    assert compare_contracts(before, after)[0]["compatibility"] == "classification_review"
    entry["parameters"].pop()
    result = compare_contracts(before, after)[0]
    assert result["compatibility"] == "breaking" and result["classification_changed"]


def test_deleted_routes_property_kinds_and_setters_require_review(current):
    for mutation in ("removed", "kind", "setter"):
        before = {"declarations": {"view.molsys": deepcopy(current["declarations"]["view.molsys"])}}
        after = deepcopy(before)
        if mutation == "removed":
            del after["declarations"]["view.molsys"]
        elif mutation == "kind":
            after["declarations"]["view.molsys"]["kind"] = "callable"
        else:
            after["declarations"]["view.molsys"]["writable"] = True
        assert compare_contracts(before, after)[0]["compatibility"] == "breaking"


def test_default_encoding_preserves_types_signed_zero_and_array_dtype():
    assert encode_default(True) != encode_default(1)
    assert encode_default(0) != encode_default(0.0)
    assert encode_default(-0.0) != encode_default(0.0)
    assert encode_default(np.float64(1)) != encode_default(1.0)
    assert encode_default(np.array([1], dtype=np.int32)) != encode_default(np.array([1], dtype=np.int64))
    with pytest.raises(TypeError, match="deterministic default encoding"):
        encode_default(object())


def test_unknown_or_conflicting_classification_fails_explicitly():
    with pytest.raises(ValueError, match="No reviewed stability rule"):
        classification("view.operation", "molsysviewer.example", [])
    rules = [
        {"route": "view", "priority": 1, "stability": "stable", "reason": "a"},
        {"route": "view", "priority": 1, "stability": "experimental", "reason": "b"},
    ]
    with pytest.raises(ValueError, match="Ambiguous"):
        classification("view.operation", "molsysviewer.example", rules)
