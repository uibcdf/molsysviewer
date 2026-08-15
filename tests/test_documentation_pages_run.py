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

import ast
import json
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


# --- no documented example teaches a deprecated call -------------------------------
#
# The three executable pages already catch this by running: the harness above promotes
# `DeprecationWarning` to an error, which is how a `Selection.add_label(...)` example
# was caught. But that only covers three markdown pages out of the whole documentation
# tree, and the deprecation is what a reader copies — running the page is not what makes
# the example wrong. This reads every page instead, statically, so the rest of the
# documentation is covered before `EXECUTABLE_PAGES` grows to meet it.

SUBJECT = re.compile(
    r'^(?:The |the )?[\'"`]?([A-Za-z_][\w.]*)[\'"`]?(\(\.\.\.\)|\(\))?(?: parameter)? is deprecated'
)


def _deprecations() -> tuple[set[str], dict[str, set[str]]]:
    """Read what is deprecated out of the source, rather than restating it here.

    A hand-written list is a second place to forget: it would still be describing today's
    deprecations after the next one is added. Every `DeprecationWarning` in the package
    names its subject in the first words of its message, so the message is the declaration.

    A warning raised straight from the function body deprecates the **function**; one
    raised under a condition deprecates an **argument** of the function it sits in — the
    distinction matters because `add_set_alpha_spheres(centers=...)` is correct while
    `add_sphere(centers=...)` is not, and a check on the bare name `centers` flags 59
    correct examples.
    """
    callables: set[str] = set()
    keywords: dict[str, set[str]] = {}

    for path in sorted((ROOT / "molsysviewer").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            unconditional = {
                id(call)
                for statement in function.body
                if isinstance(statement, ast.Expr)
                for call in ast.walk(statement)
            }
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                if not ast.unparse(node.func).endswith("warn"):
                    continue
                if "DeprecationWarning" not in ast.unparse(node):
                    continue
                if not node.args or not isinstance(node.args[0], ast.Constant):
                    continue
                match = SUBJECT.match(str(node.args[0].value).strip())
                assert match, (
                    f"{path.relative_to(ROOT)}: a deprecation message must open with what it "
                    f"deprecates, or nothing can tell the documentation about it: "
                    f"{node.args[0].value!r}"
                )
                name = match.group(1).split(".")[-1]
                if id(node) in unconditional and name == function.name:
                    callables.add(name)
                elif not function.name.startswith("_"):
                    # A private helper's deprecated argument is only reachable through a
                    # public method that also declares it, and those are already whole
                    # deprecated functions (`add_label`, `set_group_index`). Attributing it
                    # to the helper would name something no example can call.
                    keywords.setdefault(function.name, set()).add(name)

    return callables, keywords


def _documentation_blocks() -> list[tuple[str, int, str]]:
    """Every python block and code cell under `docs/content`, as (page, number, source)."""
    blocks = []
    for page in sorted((ROOT / "docs" / "content").rglob("*.md")):
        relative = str(page.relative_to(ROOT))
        for number, match in enumerate(BLOCK.finditer(page.read_text(encoding="utf-8")), 1):
            blocks.append((relative, number, match.group(1)))
    for notebook in sorted((ROOT / "docs" / "content").rglob("*.ipynb")):
        relative = str(notebook.relative_to(ROOT))
        document = json.loads(notebook.read_text(encoding="utf-8"))
        for number, cell in enumerate(document.get("cells", []), 1):
            if cell.get("cell_type") != "code":
                continue
            # `!rm …` and `%timeit …` are IPython, not python, and never a library call.
            # Dropped line by line rather than by cell, because a cell that opens with a
            # comment and then shells out is still mostly python worth checking.
            source = "\n".join(
                line
                for line in "".join(cell.get("source", [])).splitlines()
                if not line.lstrip().startswith(("!", "%"))
            )
            if not source.strip():
                continue
            blocks.append((relative, number, source))
    return blocks


def test_no_documented_example_calls_a_deprecated_api():
    """What the documentation shows is what a reader will write.

    `scene_management/selections.md` taught `view.selections[tag].add_label(text=...)`,
    which delegates to the deprecated `annotations.add_label` — so the page was telling
    readers to write a call the library itself asks them to stop writing. The receiver is
    deliberately ignored: that example's deprecation was one delegation away from the name
    that carries it.

    Killed by restoring the `add_label(...)` line in that page, and by re-spelling
    `add_sphere(center=…)` as `centers=`.
    """
    callables, keywords = _deprecations()
    assert callables, "no deprecated callable was found; the derivation has stopped working"

    found = []
    for relative, number, source in _documentation_blocks():
        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            pytest.fail(
                f"{relative}, block {number} is not valid python, so nothing can check what "
                f"it teaches:\n{source}\n{error}"
            )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = ast.unparse(node.func).split(".")[-1]
            if called in callables:
                found.append(f"{relative}, block {number}: {called}() is deprecated")
            for keyword in node.keywords:
                if keyword.arg in keywords.get(called, ()):
                    found.append(
                        f"{relative}, block {number}: {called}({keyword.arg}=…) is deprecated"
                    )

    assert found == [], "documented examples use deprecated APIs:\n" + "\n".join(found)
