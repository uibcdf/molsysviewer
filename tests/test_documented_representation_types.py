"""The representation-types page has to say what the API accepts.

CI already resolves documented `view.x.y` chains through `scripts/api_resolver.py`, so a
page naming a method that does not exist fails. Nothing checked documented *values*, and
the page had drifted six ways at once:

- `label`, `orientation` and `plane` were listed as supported types; all three raise;
- `licorice` was documented as an alias of `line` and is really `ball-and-stick` — the
  bad kind of wrong, since it draws something rather than complaining;
- `cylinders` and `dots` are real aliases nobody had written down.

A user reads this page to pick a string. That makes it API surface, and it is pinned here
the same way a signature would be.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from molsysviewer.demo import demo
from molsysviewer.viewer.representations import (
    ALLOWED_REPRESENTATIONS,
    REPRESENTATION_ALIASES,
)


PAGE = Path(__file__).resolve().parents[1] / "docs/content/user/representations/types.md"

#: Names people expect to be representation types, that deliberately are not. Each one is
#: a capability reached through its own entry point.
NOT_REPRESENTATION_TYPES = {
    "label": "view.annotations.add_annotation",
    "orientation": "view.show_orientation_axes",
    "plane": "view.show_best_fit_plane",
}


@pytest.fixture(scope="module")
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


def _documented_types(page: str) -> set[str]:
    block = page.split("Supported types (normalized)", 1)[1].split("Common aliases", 1)[0]
    return set(re.findall(r"^- `([^`]+)`", block, re.MULTILINE))


def _documented_aliases(page: str) -> dict[str, str]:
    block = page.split("Common aliases", 1)[1].split("Not representation types", 1)[0]
    aliases: dict[str, str] = {}
    for line in block.strip().splitlines():
        match = re.match(r"- (.+) → `([^`]+)`", line.strip())
        if match:
            for alias in re.findall(r"`([^`]+)`", match.group(1)):
                aliases[alias] = match.group(2)
    return aliases


def test_the_documented_types_are_exactly_the_accepted_ones(page):
    assert _documented_types(page) == ALLOWED_REPRESENTATIONS


def test_the_documented_aliases_are_exactly_the_real_ones(page):
    """Including their targets. A wrong target draws the wrong thing without an error."""
    assert _documented_aliases(page) == REPRESENTATION_ALIASES


def test_every_alias_resolves_to_a_supported_type():
    assert set(REPRESENTATION_ALIASES.values()) <= ALLOWED_REPRESENTATIONS


@pytest.mark.parametrize("name", sorted(NOT_REPRESENTATION_TYPES))
def test_the_names_that_are_not_types_are_rejected(name):
    """Pinned as behaviour, not only as a list: the page now promises they raise."""
    view = demo["dialanine"]
    view.widget.send = lambda _message: None  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="Unsupported representation type"):
        view.whole.set_representation(representation=name)


@pytest.mark.parametrize("name, entry_point", sorted(NOT_REPRESENTATION_TYPES.items()))
def test_the_page_says_where_each_capability_actually_lives(page, name, entry_point):
    """Rejecting a name is only half the answer; a reader needs the other half."""
    section = page.split("Not representation types", 1)[1]

    assert entry_point in section, f"the page rejects {name!r} without naming {entry_point}"


def test_the_geometry_helpers_bypass_the_setter_rather_than_widening_it():
    """The two overlays work while their type names raise, and that is the design.

    They send `set_region_representation` themselves instead of going through
    `set_representation`, which is why `ALLOWED_REPRESENTATIONS` can stay structural. If
    someone ever routes them through the public setter, that list has to grow and this
    page's promise changes with it.
    """
    source = (Path(__file__).resolve().parents[1]
              / "molsysviewer/viewer/regions.py").read_text(encoding="utf-8")

    for helper in ("show_orientation_axes", "show_best_fit_plane"):
        body = source.split(f"def {helper}(", 1)[1].split("\n    @", 1)[0]
        assert "set_region_representation" in body, helper
        assert "self.set_representation" not in body, helper

    assert not ({"orientation", "plane"} & ALLOWED_REPRESENTATIONS)
