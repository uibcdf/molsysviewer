"""The README add-on table reports; it must not grade, invent, or fall behind.

Two dimensions live in that table — the integration exists, and how finished it is — and
they drift for different reasons. The rows drift when an add-on is added or renamed; the
maturity column drifts when someone writes a level that sounds right.

The column is *reported*, never asserted: MolSysViewer does not decide the readiness of
code it does not own. So the guard is deliberately asymmetric. Row names are pinned hard
against `KNOWN_ADDON_MODULES`. The declared level is compared with the installed add-on
only when it is installed, because a contributor without the whole MolSysSuite checked out
must still be able to run the suite.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path

import pytest

from molsysviewer.addons import KNOWN_ADDON_MODULES


README = Path(__file__).resolve().parents[1] / "README.md"

#: Every word the column may contain: the vocabulary defined in
#: `devguide/pending_proposals/addon_maturity_and_ownership.md`, the two pre-existing
#: declarations it replaces, and the honest answer for an add-on that says nothing.
PERMITTED_MATURITY = {
    "experimental", "development", "beta", "stable",  # the vocabulary
    "skeleton", "alpha",                              # what four add-ons said before it
    "undeclared",                                     # TopoMT, which declares nothing
}


def _table_rows() -> dict[str, str]:
    text = README.read_text(encoding="utf-8")
    rows = re.findall(r"^\| `(molsysviewer_\w+)` \|[^|]*\|[^|]*\| ([^|]+) \|$",
                      text, re.MULTILINE)
    return {module: maturity.strip() for module, maturity in rows}


def test_the_table_lists_exactly_the_known_addons():
    """A new sibling add-on must appear here, and a renamed one must not linger.

    `KNOWN_ADDON_MODULES` is the host's own list, so the two cannot disagree without
    someone having edited one and forgotten the other.
    """
    assert set(_table_rows()) == set(KNOWN_ADDON_MODULES)


def test_the_maturity_column_uses_only_declared_words():
    """Guards against `stable` appearing because a paragraph needed it to."""
    unknown = {module: level for module, level in _table_rows().items()
               if level not in PERMITTED_MATURITY}

    assert unknown == {}, f"maturity levels outside the vocabulary: {unknown}"


def test_the_readme_does_not_claim_any_addon_is_production_ready():
    """The distinction the table exists to make.

    All four integrations exist; none is production-ready. If that changes, it changes by
    an add-on declaring `beta` or `stable`, not by prose.
    """
    text = README.read_text(encoding="utf-8").lower()

    assert "production-ready" not in text.split("### addon system")[1].split("###")[0] \
        or "none of them is production-ready" in text


@pytest.mark.parametrize("module", sorted(KNOWN_ADDON_MODULES))
def test_the_reported_level_is_the_one_the_addon_declares(module):
    """Reported, not graded — so the README must equal the source, not interpret it.

    Skipped when the add-on is not installed: the MolSysSuite toolkits are optional here,
    and a contributor with only MolSysViewer checked out is not failing anything.
    """
    if importlib.util.find_spec(module) is None:
        pytest.skip(f"{module} is not installed")

    imported = importlib.import_module(module)
    spec = getattr(imported, "addon", None) or getattr(imported, "ADDON", None)
    if spec is None and hasattr(imported, "get_addon"):
        spec = imported.get_addon()
    assert spec is not None, f"{module} exposes no AddonSpec"

    declared = (spec.meta or {}).get("status", "undeclared")

    assert _table_rows()[module] == declared, (
        f"the README reports {_table_rows()[module]!r} for {module}, which declares "
        f"{declared!r}"
    )
