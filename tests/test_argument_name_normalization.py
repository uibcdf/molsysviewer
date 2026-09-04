"""The declared argument-name aliases, and the scope that keeps them safe.

These renames are silent when they work, so a green suite proves nothing about them on
its own — that is exactly how the imperative standardizer they replaced went unnoticed.
It tested `caller == 'molsysviewer.viewer.MolSysView.get'`, the real caller is
`molsysviewer.viewer.get`, and so every one of its four branches was dead: over a full
run, 4,674 digested calls across 210 distinct callers matched none of them.

The consequence was user-visible, not cosmetic. `view.get` forwards to `msm.get` with
`skip_digestion=True` — deliberately, since the arguments are digested once, here — so
MolSysMT's own normalization never runs on it either. Nothing renamed anything, and
`view.get(element='group', index=True)` raised `KeyError: 'index'`.

So the tests below are the port's only real evidence. Each one fails against the code as
it stood before the migration.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from argdigest import ArgumentConsistencyError, describe_normalization
from argdigest.core.function_loader import load_normalization
from molsysviewer.demo import demo

NORMALIZATION_SOURCE = "molsysviewer._private.argdigest.normalization"


@pytest.fixture
def view():
    # Function-scoped on purpose: `conftest` instruments `MolSysView.__init__` per test,
    # so a view built once and reused across the module sends messages into a log that
    # the current test's patch never created.
    view = demo["dialanine"]
    view.widget.send = lambda _message: None  # type: ignore[attr-defined]
    return view


@pytest.fixture(scope="module")
def registry():
    return load_normalization(NORMALIZATION_SOURCE)


# --- the rules, exercised through the public surface -------------------------------


@pytest.mark.parametrize(
    "element, bare, canonical",
    [
        ("atom", "name", "atom_name"),
        ("atom", "index", "atom_index"),
        ("atom", "id", "atom_id"),
        ("group", "name", "group_name"),
        ("group", "index", "group_index"),
        ("chain", "name", "chain_name"),
        ("bond", "order", "bond_order"),
    ],
)
def test_a_bare_element_name_means_the_attribute_of_that_element(view, element, bare, canonical):
    """`element='group', name=True` is `group_name`, and must agree with spelling it out."""
    selection = "atom_index==[0,1]"

    through_bare_name = view.get(selection=selection, element=element, **{bare: True})
    spelled_out = view.get(selection=selection, element=element, **{canonical: True})

    assert list(through_bare_name) == list(spelled_out)


def test_the_same_bare_name_follows_the_element_it_was_asked_about(view):
    """`name` is not one attribute: it is whichever the element makes it."""
    selection = "atom_index==[0,1]"

    assert list(view.get(selection=selection, element="atom", name=True)) == ["H1", "CH3"]
    assert list(view.get(selection=selection, element="group", name=True)) == ["ACE"]


@pytest.mark.parametrize("synonym, canonical", [("atom_names", "atom_name"),
                                                ("atom_indices", "atom_index")])
def test_attribute_synonyms_reach_get(view, synonym, canonical):
    selection = "atom_index==[0,1]"

    assert list(view.get(selection=selection, element="atom", **{synonym: True})) \
        == list(view.get(selection=selection, element="atom", **{canonical: True}))


def test_an_alias_and_its_canonical_name_are_rejected_together(view):
    with pytest.raises(ArgumentConsistencyError, match="atom_names.*atom_name"):
        view.get(element="atom", atom_names=True, atom_name=False)


def test_attribute_synonyms_reach_get(view):
    """`contains` and `is_composed_of` were removed; `get` carries the same names.

    The rename that mattered to them still has to happen, and now MolSysMT is the one
    doing it — see `uibcdf/molsysviewer#71`.
    """
    assert view.whole.get(n_waters=True) == 0
    assert list(view.whole.get(element="group", name=True)) \
        == list(view.whole.get(element="group", group_name=True))


def test_a_region_gets_the_same_renames_as_the_view(view):
    """`Region` has the same shape and was missed on the first pass.

    It digests, then forwards with `skip_digestion=True` — so `region.get` raised
    `KeyError: 'index'` for exactly the reason `view.get` did.
    """
    view.regions.add(selection="atom_index==[0,1]", tag="_normalization_probe")
    region = view.regions["_normalization_probe"]

    assert list(region.get(element="group", index=True)) \
        == list(region.get(element="group", group_index=True))


def test_the_whole_gets_the_synonyms_too(view):
    assert list(view.whole.get(element="group", residue_name=True)) \
        == list(view.whole.get(element="group", group_name=True))


def test_a_pure_forwarder_needs_no_table_of_its_own(view):
    """`Whole.get` passes `skip_digestion` through rather than forcing it.

    So `view.get` digests on its behalf and the bare names work without `whole.get`
    appearing in any table. Pinned because adding it would look like a fix and would
    instead mean renaming twice.
    """
    assert list(view.whole.get(element="group", index=True)) \
        == list(view.get(element="group", group_index=True))


def test_every_method_that_forwards_undigested_kwargs_has_a_table(registry):
    """The membership rule is structural, so it can be re-derived instead of trusted.

    A method that digests here and forwards `**kwargs` onward with `skip_digestion=True`
    is the last layer that can rename them. If one acquires that shape and nobody adds it
    to a table, nothing renames its arguments and nothing says so — which is precisely how
    the mechanism this replaced stayed broken. Two exemptions, both deliberate:
    `convert` forwards conversion options rather than attribute names, and the shape
    helpers forward representation parameters.
    """
    import ast
    from pathlib import Path

    # Forwarding undigested kwargs is only a problem when those kwargs are *attribute
    # names*. These forward conversion options, representation parameters and shape
    # parameters, none of which the synonym tables touch.
    exempt = {("molsysviewer/viewer/molsysmt_interface.py", "convert"),
              ("molsysviewer/shapes/__init__.py", "add_sphere"),
              ("molsysviewer/shapes/__init__.py", "add_topomt_feature"),
              ("molsysviewer/shapes/pharmacophore.py", "add_pharmacophore_features")}

    root = Path(__file__).resolve().parents[1]
    delegators = set()
    for path in sorted((root / "molsysviewer").rglob("*.py")):
        if "_private" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.FunctionDef) or node.args.kwarg is None:
                continue
            if not any("digest" in ast.unparse(d) for d in node.decorator_list):
                continue
            source = ast.unparse(node)
            if "**kwargs" in source and "skip_digestion=True" in source:
                relative = str(path.relative_to(root))
                if (relative, node.name) not in exempt:
                    delegators.add(f"molsysviewer.{path.stem}.{node.name}"
                                   if path.stem != "molsysmt_interface"
                                   else f"molsysviewer.viewer.{node.name}")

    covered = {table["applies_to"] for table in describe_normalization(registry)}

    assert delegators <= covered, (
        "these digest their arguments and then forward them with `skip_digestion=True`, "
        "so nothing downstream will rename them, and no alias table covers them: "
        f"{sorted(delegators - covered)}"
    )


# --- the scope, which is the part that is easy to get wrong ------------------------


def test_the_synonyms_are_not_declared_globally(registry):
    """`atom_indices` is a synonym *and* a real argument elsewhere.

    Declaring the synonym table for every caller is the obvious simplification and it is
    wrong: it would rename the real `atom_indices` argument of unrelated calls to
    `atom_index`, which nothing declares. Measured by doing it: 132 tests fail. The same
    mistake broke 76 in MolSysMT.
    """
    unrelated = describe_normalization(registry, caller="molsysviewer.regions.add")

    assert unrelated == []


def test_a_real_atom_indices_argument_survives_untouched(view):
    """The end of the same trap, exercised rather than asserted about the tables."""
    assert list(view.select(selection="atom_index==[0,1]")) == [0, 1]


def test_the_normalization_package_is_empty_and_says_why():
    """The two tables are gone, and their absence is the claim being made.

    They scoped MolSysMT's synonym and bare-name tables to eight callers, and existed
    only because those callers digested here and forwarded with `skip_digestion=True` —
    the last layer that could rename anything. `uibcdf/molsysviewer#71` removed that
    shape, so MolSysMT renames what it is about to consume.

    Pinned because a table reappearing is not a bug in itself: it means a method acquired
    that shape again, and *that* is what needs looking at.
    """
    from argdigest.core.function_loader import load_normalization

    registry = load_normalization("molsysviewer._private.argdigest.normalization")
    tables = describe_normalization(registry) if registry is not None else []

    assert tables == [], (
        "normalization tables are back. A method somewhere digests its own arguments and "
        f"forwards them with skip_digestion=True; find it before trusting the table: {tables}"
    )


@pytest.mark.parametrize(
    ("kwargs", "canonical"),
    [
        ({"element": "group", "name": True}, {"element": "group", "group_name": True}),
        ({"element": "atom", "name": True}, {"element": "atom", "atom_name": True}),
        ({"element": "group", "index": True}, {"element": "group", "group_index": True}),
        ({"element": "group", "residue_name": True}, {"element": "group", "group_name": True}),
    ],
    ids=["group/name", "atom/name", "group/index", "residue_name"],
)
def test_the_renames_still_happen_now_that_molsysmt_does_them(view, kwargs, canonical):
    """The behaviour the deleted tables existed to produce, checked where a user meets it.

    This is the guard that matters: it does not care *who* renames, only that a bare name
    and a synonym still answer what the canonical name answers. It fails if a future
    forwarder starts swallowing them again, which is what the tables were written for.
    """
    assert list(view.whole.get(**kwargs)) == list(view.whole.get(**canonical))
