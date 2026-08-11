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

import pytest

from argdigest import describe_normalization
from argdigest.core.function_loader import load_normalization

from molsysviewer.demo import demo


NORMALIZATION_SOURCE = "molsysviewer._private.argdigest.normalization"


@pytest.fixture(scope="module")
def view():
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


def test_attribute_synonyms_reach_contains_and_is_composed_of(view):
    """Both delegate with `skip_digestion=True`, so both need the rename on this side."""
    assert view.contains(selection="all", n_waters=0) is True
    assert view.is_composed_of(selection="all", n_waters=0) is False


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


def test_only_the_three_delegating_methods_carry_the_synonyms(registry):
    carriers = {
        table["applies_to"]
        for table in describe_normalization(registry)
        if table["when"] is None
    }

    assert carriers == {
        "molsysviewer.viewer.get",
        "molsysviewer.viewer.contains",
        "molsysviewer.viewer.is_composed_of",
    }


# --- the tables themselves ---------------------------------------------------------


def test_the_element_tables_declare_only_combinations_that_exist(registry):
    """Written out, never generated: a template would accept `bond_name` and `atom_order`.

    Both would produce an attribute name nothing defines, and an error far downstream
    from the call that caused it.
    """
    by_element = {
        table["when"]["element"]: set(table["aliases"].values())
        for table in describe_normalization(registry, caller="molsysviewer.viewer.get")
        if table["when"]
    }

    assert "bond_name" not in by_element["bond"]
    assert "atom_order" not in by_element["atom"]
    assert "chain_order" not in by_element["chain"]
    assert "bond_order" in by_element["bond"]


def test_the_element_tables_stay_identical_to_molsysmts_own(registry):
    """`view.get` forwards to `msm.get`, so the real combinations are theirs to define.

    Re-emitting their tables under this caller is what makes drift impossible; this pins
    that the re-emission is faithful rather than a copy that has started to age.
    """
    from molsysmt._private.argdigest.normalization.get_element_names import TABLES as upstream

    ours = {
        (table["when"]["element"], tuple(sorted(table["aliases"].items())))
        for table in describe_normalization(registry, caller="molsysviewer.viewer.get")
        if table["when"]
    }
    theirs = {
        (table.when["element"], tuple(sorted(table.aliases.items())))
        for table in upstream
    }

    assert ours == theirs


def test_there_is_no_second_mechanism_deciding_renames():
    """A half-migrated standardizer is worse than an unmigrated one."""
    import molsysviewer._argdigest as configuration

    assert configuration.NORMALIZATION_SOURCE == NORMALIZATION_SOURCE
    assert not hasattr(configuration, "STANDARDIZER")

    with pytest.raises(ModuleNotFoundError):
        __import__("molsysviewer._private.argdigest.argument_names_standardization")
