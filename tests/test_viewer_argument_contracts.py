"""What the viewer's new digesters actually refuse.

A digester that exists is not a digester that works, and gate 9 is measured in digesters
written — so the count is easy to raise without raising the protection. Each test below
names a value that was accepted before and is refused now, at the seam, with the caller in
the message.

The nine cases are chosen for what they cost when they get through, not for coverage. Most
of them do not raise downstream: they leave the scene plausible and wrong.
"""

from __future__ import annotations

import pytest

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.demo import demo


@pytest.fixture
def view():
    view = demo["dialanine"]
    view.widget.send = lambda _message: None  # type: ignore[attr-defined]
    return view


def test_a_callback_must_be_callable(view):
    """`on_hover` only appends to a list, so this used to fail during a mouse move.

    The traceback then named the event dispatcher, not the registration that caused it.
    """
    with pytest.raises(ArgumentError, match="callback"):
        view.on_click("not a function")


def test_on_conflict_is_a_closed_set(view):
    """A typo silently becoming another policy changes which scene the user ends up with."""
    with pytest.raises(ArgumentError, match="on_conflict"):
        view.import_state({"version": 2}, on_conflict="raies")


def test_clear_first_is_a_strict_boolean(view):
    """`clear_first` erases every region and overlay before restoring.

    A merely truthy value — a non-empty string, a stray `1` from a config file — would
    destroy a user's scene while looking like it was asked to.
    """
    with pytest.raises(ArgumentError, match="clear_first"):
        view.import_state({"version": 2}, clear_first="yes")


def test_import_state_refuses_a_path(view):
    """The two entry points invite this: `load_state(path)` beside `import_state(state)`."""
    with pytest.raises(ArgumentError, match="state"):
        view.import_state("/tmp/some-state.json")


def test_a_wait_needs_a_positive_number_of_seconds(view):
    """`timeout_s=0` reads as "do not wait" and is a poll dressed as a wait."""
    with pytest.raises(ArgumentError, match="timeout_s"):
        view.wait_for_transaction("t", timeout_s=0)


def test_load_blocks_is_a_closed_set(view):
    """Wrong accounting does not raise; it describes a system that is no longer there."""
    with pytest.raises(ArgumentError, match="load_blocks"):
        view.apply_system_edit(view.molsys, load_blocks="colapse")


def test_an_atom_index_map_holds_indices_on_both_sides(view):
    """This map is what every piece of viewer-owned state is remapped through.

    One bad entry does not raise: it moves a region onto different atoms and the scene
    stays plausible.
    """
    with pytest.raises(ArgumentError, match="atom_index_map"):
        view.apply_system_edit(view.molsys, atom_index_map={0: -1})


def test_an_append_that_added_no_atoms_is_refused(view):
    with pytest.raises(ArgumentError, match="appended_n_atoms"):
        view.apply_system_edit(view.molsys, load_blocks="append", appended_n_atoms=0)


def test_visible_atom_indices_are_indices(view):
    with pytest.raises(ArgumentError, match="visible_atom_indices"):
        view.apply_system_edit(view.molsys, visible_atom_indices=[-1])


def test_every_refusal_names_the_call_that_caused_it(view):
    """The upgrade over a bare ValueError, stated once rather than in every test above."""
    with pytest.raises(ArgumentError) as raised:
        view.apply_system_edit(None)

    assert "molsysviewer.viewer.apply_system_edit" in str(raised.value)


def test_the_conditional_rule_stays_in_the_body(view):
    """`load_blocks="append"` requires `appended_n_atoms`, and no digester can say so.

    It is conditional on another argument's *value*, which ArgDigest cannot express:
    `co_required` is symmetric and would reject a valid `keep` call that omits the count.
    Pinned here so that moving it into a contract is a deliberate act, taken when
    ArgDigest grows the capability rather than by someone assuming it already has.
    """
    with pytest.raises(ValueError, match="requires appended_n_atoms"):
        view.apply_system_edit(view.molsys, load_blocks="append")
