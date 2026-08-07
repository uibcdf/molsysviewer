"""Every query digester must accept the viewer as its own caller.

ArgDigest hands each digester the fully qualified name of whoever is calling
(`molsysviewer.viewer.get`), and each digester is a whitelist of callers. The
digesters were written for MolSysMT's callers; when MolSysViewer wrapped the same
query API, its caller name was in no whitelist, so calls fell through to the
final `raise`. 58 of 81 query arguments were rejected that way, for months, under
a green suite.

The boundary audit asked "does a digester exist for this argument?" and found 26
missing. It never asked the second question — "does it accept the viewer calling
it?" — which is what this guard adds. Existing is not accepting.

An `ArgumentError` here means our own contract rejects our own public API. Any
other exception belongs to MolSysMT (for instance an attribute that needs an
explicit `element=`, or one this form cannot provide) and is out of scope.
"""

import re
from pathlib import Path

import pytest

from molsysviewer import demo
from molsysviewer._private.exceptions import ArgumentError

ARGUMENT_DIR = (
    Path(__file__).resolve().parents[1]
    / "molsysviewer" / "_private" / "argdigest" / "argument"
)

#: Arguments the digesters themselves declare as MolSysMT-style query flags,
#: derived from the source rather than hardcoded, so a new one is covered the
#: day it is added.
QUERY_ARGUMENTS = sorted(
    path.stem
    for path in ARGUMENT_DIR.glob("*.py")
    if "molsysmt.basic.get.get" in path.read_text(encoding="utf-8")
)

#: Not query flags: these appear in a `get` branch but describe *how* to answer,
#: not *what* to ask for.
NOT_QUERY_FLAGS = {"output_type", "mask"}


@pytest.fixture(scope="module")
def view():
    return demo["dialanine"]


def test_the_query_argument_inventory_is_not_empty():
    # If this ever collapses to nothing, the sweep below silently passes.
    assert len(QUERY_ARGUMENTS) > 50


@pytest.mark.parametrize("argument", [a for a in QUERY_ARGUMENTS if a not in NOT_QUERY_FLAGS])
def test_a_query_digester_accepts_the_viewer_as_caller(view, argument):
    try:
        view.get(**{argument: True})
    except ArgumentError as error:
        pytest.fail(
            f"digest_{argument} rejects its own caller: {error}\n"
            f"Add 'molsysviewer.viewer.get' to the accepted callers in "
            f"{ARGUMENT_DIR.name}/{argument}.py"
        )
    except Exception:
        # MolSysMT's business: needs element=, or not available in this form.
        pass


def test_every_query_digester_names_the_viewer_caller():
    """Static twin of the sweep above: catches the gap without executing a query.

    The call-based test can be masked when MolSysMT raises before the digester is
    reached; this one reads the source directly.
    """
    missing = [
        argument
        for argument in QUERY_ARGUMENTS
        if "molsysviewer.viewer.get"
        not in (ARGUMENT_DIR / f"{argument}.py").read_text(encoding="utf-8")
    ]
    assert not missing, (
        "these query digesters never accept 'molsysviewer.viewer.get', so "
        f"view.get(...) raises for them: {missing}"
    )


def test_the_caller_reaching_a_digester_is_the_one_whitelisted(view):
    """Pin the caller string itself, since the whitelists are literal matches.

    If ArgDigest ever changes how it builds the caller, or the viewer package is
    reorganized, every whitelist silently stops matching. This fails loudly
    instead.

    The caller is read back from a deliberate rejection rather than by patching a
    digester: ArgDigest resolves each digester once and caches it, so a late
    monkeypatch never runs and the check would silently pass.
    """
    with pytest.raises(ArgumentError) as rejection:
        view.get(n_structures="not a boolean")

    assert "molsysviewer.viewer.get" in str(rejection.value), (
        f"the caller reaching the digester changed ({rejection.value}); every "
        "whitelist matching 'molsysviewer.viewer.get' literally is now dead"
    )


def test_solvate_and_neighbour_arguments_are_left_out_on_purpose():
    """These look like query flags but are not, and must not be blanket-patched."""
    for argument in ("n_anions", "n_cations", "n_neighbors"):
        source = (ARGUMENT_DIR / f"{argument}.py").read_text(encoding="utf-8")
        assert "molsysmt.basic.get.get" not in source, (
            f"{argument} became a query flag; it must now be covered by the sweep"
        )
