"""The runtime our own published views address.

This suite exists because nothing looked. Every exported view under
`docs/_static/views/` pointed at a jsDelivr version that a build hook rewrote
without checking it existed, npm stopped thirteen versions behind Python, and
the next deploy would have broken all of them with a green Sphinx build. See
`devguide/pending_bugs/docs_lite_views_pinned_to_unpublished_npm_version.md`.

The checks are on the *declared* target, not on a placed file: the asset is
generated at build time and gitignored, so requiring it here would only pass on
a machine that had already built the docs.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
VIEWS = DOCS / "_static" / "views"
RUNTIME_TARGET = (DOCS / "_static" / "viewer.js").resolve()

_CANDIDATES = re.compile(
    r'<script id="molsysviewer-runtime-candidates" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _views() -> list[Path]:
    return sorted(VIEWS.glob("*.html"))


def _declared_candidates(path: Path) -> list[str]:
    match = _CANDIDATES.search(path.read_text(encoding="utf-8"))
    assert match is not None, f"{path.name} declares no runtime candidates"
    return json.loads(match.group(1))


def test_there_are_views_to_check():
    """Without this, every check below would pass over an empty set."""
    assert _views(), f"no exported views under {VIEWS}"


@pytest.mark.parametrize("view", _views(), ids=lambda p: p.name)
def test_view_does_not_reach_the_network_for_its_runtime(view):
    """The regression that broke us: a URL to a package version nobody published.

    A published view must not depend on a registry entry surviving, on a CDN
    being reachable, or on our release cadence.
    """
    for candidate in _declared_candidates(view):
        assert not candidate.startswith(("http://", "https://", "//")), (
            f"{view.name} loads its runtime from the network: {candidate}"
        )


@pytest.mark.parametrize("view", _views(), ids=lambda p: p.name)
def test_view_addresses_the_runtime_the_build_places(view):
    candidates = _declared_candidates(view)
    assert candidates, f"{view.name} declares an empty candidate list"
    resolved = [(view.parent / candidate).resolve() for candidate in candidates]
    assert RUNTIME_TARGET in resolved, (
        f"{view.name} points at {resolved}, but the build places the runtime at {RUNTIME_TARGET}"
    )


def test_conf_places_the_runtime_through_the_public_api():
    """Guard. The chain only holds if something actually puts the file there.

    Asserted against the public call rather than any private helper: what our own
    documentation runs must be what we tell third parties to run.
    """
    source = (DOCS / "conf.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "export_runtime_asset" in called, (
        "docs/conf.py no longer places the runtime; every exported view would 404"
    )
    assert "builder-inited" in source, "the placement is not connected to the build"


def test_conf_no_longer_rewrites_runtime_links():
    """Guard. The rewriter substituted a version without checking it existed.

    Reintroducing it would restore the defect exactly, so its absence is pinned
    rather than left to memory.
    """
    source = (DOCS / "conf.py").read_text(encoding="utf-8")
    assert "cdn.jsdelivr.net/npm/@uibcdf/molsysviewer" not in source, (
        "docs/conf.py rewrites lite views to a CDN version again"
    )
