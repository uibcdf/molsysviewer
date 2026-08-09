"""The README's quick start must run.

Every python block under ``## Quick start`` is executed here, in order, in one
shared namespace. The README is the first thing a newcomer copies, and until
this test existed it had drifted: it named regions that the code does not
create, passed a bare array where units are required, omitted a required
argument, and showed an addon registration pattern that had been replaced by a
one-liner. None of that is visible to a reader — they conclude the tool is
broken, or that they misunderstood it, and close the tab.

Warnings are escalated to errors: a snippet that "works" only by printing
"Region 'B' has no own representation to hide" is not a snippet we want in the
first page of the project.
"""

from __future__ import annotations

import importlib.util
import re
import socket
import warnings
from pathlib import Path

import pytest

README = Path(__file__).parents[1] / "README.md"

QUICK_START = "## Quick start"
SECTION_END = "## Installation"
PYTHON_BLOCK = re.compile(r"^```python\n(.*?)^```", re.DOTALL | re.MULTILINE)

# The opening snippet fetches a structure from the PDB. It is the right thing
# for the README to show first, and the wrong thing for CI to depend on.
NEEDS_NETWORK = 'msv.new_view("1TRS")'
NEEDS_ADDON = "molsysviewer_molsysmt"


def _quick_start_blocks() -> list[str]:
    text = README.read_text(encoding="utf-8")
    start = text.index(QUICK_START)
    end = text.index(SECTION_END, start)
    return [match.group(1) for match in PYTHON_BLOCK.finditer(text[start:end])]


def _has_network() -> bool:
    try:
        socket.create_connection(("files.rcsb.org", 443), timeout=5).close()
    except OSError:
        return False
    return True


def test_the_quick_start_has_the_blocks_this_test_thinks_it_has():
    blocks = _quick_start_blocks()
    assert len(blocks) >= 6, f"only {len(blocks)} python blocks found in the quick start"
    assert any(NEEDS_NETWORK in block for block in blocks)
    assert any("save_state(" in block and "load_state(" in block for block in blocks), (
        "the quick start no longer closes the reproducibility loop; that snippet is "
        "the one thing in this README that no other viewer can copy"
    )


def test_every_quick_start_snippet_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {}
    executed = 0

    for number, block in enumerate(_quick_start_blocks(), start=1):
        if NEEDS_NETWORK in block and not _has_network():
            continue
        if NEEDS_ADDON in block and importlib.util.find_spec(NEEDS_ADDON) is None:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            try:
                exec(compile(block, f"<README quick start block {number}>", "exec"), namespace)
            except Exception as error:  # noqa: BLE001 - the message is the point
                pytest.fail(
                    f"README quick start block {number} failed with "
                    f"{type(error).__name__}: {error}\n\n{block}"
                )
        executed += 1

    assert executed >= 5, "almost nothing ran; the guards are too eager"


def test_the_quick_start_reproducibility_claim_holds(tmp_path, monkeypatch):
    """The README promises the restored view carries the same scene. Check it."""
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {}
    for block in _quick_start_blocks():
        if NEEDS_NETWORK in block or NEEDS_ADDON in block:
            continue
        exec(compile(block, "<README quick start>", "exec"), namespace)

    view = namespace["view"]
    restored = namespace["restored"]

    assert list(restored.regions) == list(view.regions)
    assert restored.regions["B"].visible is view.regions["B"].visible is False
    assert restored.regions["A"].representation == view.regions["A"].representation == "cartoon"
    assert len(restored.export_state()["shapes"]) == len(view.export_state()["shapes"]) == 1
