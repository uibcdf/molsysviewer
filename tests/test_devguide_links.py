"""Every link inside the devguide points at something, on anybody's machine.

The devguide moves documents between `pending_bugs/`, `pending_proposals/` and `archive/`
whenever an entry closes -- that is the reporting protocol, and it happens on almost every
session that finishes something. Nothing followed the links behind them, so they rotted
quietly: on 2026-09-06 a sweep found **six** broken relative links, two of them made that
same morning by archiving #81 and #33, and four older ones nobody had noticed.

They rot silently because a dead link in Markdown looks exactly like a live one. Only
following it says otherwise, and no reader follows every link.

The second rule is about a subtler kind of dead: a link that works for exactly one person.
Eight targets were `file:///home/diego/...` absolute paths -- five into a sibling checkout
of MolSysMT, which now point at github.com/uibcdf/molsysmt, and two inside this repository,
which are relative now. A path that resolves only on the machine that wrote it is not a
reference, and the reader who most needs it is the one who does not have that machine.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEVGUIDE = ROOT / "devguide"

#: `[label](target)`. Bare URLs and reference-style links are not used in the devguide.
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

#: A link nobody can resolve by walking the repository: the network, an anchor within the
#: page, or a mail address. Their liveness is not this suite's question.
EXTERNAL = ("http://", "https://", "#", "mailto:")


def _links() -> list[tuple[Path, str]]:
    found = []
    for document in sorted(DEVGUIDE.rglob("*.md")):
        text = document.read_text(encoding="utf-8", errors="replace")
        for _label, target in LINK.findall(text):
            found.append((document, target))
    return found


@pytest.fixture(scope="module")
def links() -> list[tuple[Path, str]]:
    return _links()


def test_the_sweep_actually_reads_the_devguide(links):
    """Guard the guard: a regex that matches nothing passes every assertion below."""
    assert len(list(DEVGUIDE.rglob("*.md"))) > 50, "the devguide is not where this expects"
    assert len(links) > 200, f"only {len(links)} links found; the pattern stopped matching"


def test_every_relative_link_resolves(links):
    """A document that moved queues takes every link into it with it."""
    broken = []
    for document, target in links:
        if target.startswith(EXTERNAL):
            continue
        path = target.split("#", 1)[0]
        if not path:
            continue
        if not (document.parent / path).exists():
            broken.append(f"{document.relative_to(ROOT)} -> {target}")

    assert broken == [], "broken links in the devguide:\n  " + "\n  ".join(broken)


def test_no_link_resolves_only_on_the_machine_that_wrote_it(links):
    """`file:///home/someone/...` is a note to self wearing a link's clothes.

    Inside this repository the answer is a relative path; in a sibling repository it is
    that project's URL. Either travels; an absolute path off this disk does not.
    """
    local = [
        f"{document.relative_to(ROOT)} -> {target}"
        for document, target in links
        if target.startswith("file://")
    ]

    assert local == [], (
        "links to an absolute path on one developer's machine:\n  " + "\n  ".join(local)
    )
