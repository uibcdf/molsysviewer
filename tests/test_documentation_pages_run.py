"""The user pages that document an API by running it must actually run.

`docs/execute_notebooks.py` executes the notebooks. The python blocks in the markdown are
executed by nothing, and that is not theoretical: four pages were found carrying
`import molsysviewer as msv` followed by `viewer.config…`, a `NameError` in every one,
because a rename had been applied to the import line and not to the bodies.

This closes the gap for the pages listed below rather than for all of them. The rest is
`what_needs_a_human_2026_08.md`'s parked finding, and widening this list is how it gets
closed — a page joins when its blocks are self-contained enough to run in sequence.

Each page's blocks run **in order, in one namespace**, because that is how a reader meets
them: block two is allowed to use what block one defined.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

#: Pages whose python blocks are executable as written. Adding one here is the way to
#: retire a piece of the unexecuted-markdown finding.
EXECUTABLE_PAGES = (
    "docs/content/user/scene_management/selections.md",
    "docs/content/user/overlays/measurements.md",
    "docs/content/user/export/state.md",
)

BLOCK = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)


def _blocks(page: Path) -> list[str]:
    return [match.group(1) for match in BLOCK.finditer(page.read_text(encoding="utf-8"))]


@pytest.mark.parametrize("relative", EXECUTABLE_PAGES)
def test_the_page_runs_as_written(relative, tmp_path, monkeypatch):
    """Run every block in order, in one namespace, with warnings promoted to errors.

    A `DigestNotDigestedWarning` or a deprecation in a documented example is a defect in
    the example: the page is telling a reader to write something the library complains
    about.
    """
    page = ROOT / relative
    blocks = _blocks(page)
    assert blocks, f"{relative} has no python blocks; remove it from the list"

    # `state.md` writes `scene.json` relative to the working directory.
    monkeypatch.chdir(tmp_path)

    namespace: dict = {}
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        warnings.simplefilter("error", DeprecationWarning)
        for number, block in enumerate(blocks, start=1):
            try:
                exec(compile(block, f"{relative}#{number}", "exec"), namespace)  # noqa: S102
            except Exception as error:  # noqa: BLE001 — the point is to name the block
                pytest.fail(
                    f"{relative}, python block {number} failed:\n"
                    f"{block}\n{type(error).__name__}: {error}"
                )
            view = namespace.get("view")
            if view is not None and hasattr(view, "widget"):
                # A demo view would otherwise try to talk to a frontend that is not there.
                view.widget.send = lambda _message: None


def test_every_documented_page_is_reachable_from_a_toctree():
    """A page nobody links is a page nobody reads, whatever it says.

    The check reads the `toctree` block rather than the whole file. Searching the file for
    the stem passes on prose: `export/index.md` opens with "the current state of a
    viewer", which made `state` look listed while it was not — caught by mutating the
    toctree and watching this pass.
    """
    missing = []
    for relative in EXECUTABLE_PAGES:
        page = Path(relative)
        index = ROOT / page.parent / "index.md"
        assert index.exists(), f"{page.parent} has no index"

        text = index.read_text(encoding="utf-8")
        assert "```{toctree}" in text, f"{index} has no toctree"
        block = text.split("```{toctree}", 1)[1].split("```", 1)[0]
        entries = {line.strip() for line in block.splitlines() if line.strip()}
        if page.stem not in entries:
            missing.append(relative)

    assert missing == [], f"pages not listed in their section's toctree: {missing}"
