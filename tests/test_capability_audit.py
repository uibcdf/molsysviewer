"""The capability audit must stay true, or it is worse than not having one.

A table that once described the project and now describes a previous version is more
dangerous than no table: it gets quoted. So every declared path is checked to exist, the
generated document is checked to be current, and `stable` is held to a definition instead
of a feeling.

The audit is generated — `python devtools/capability_audit.py --write` — so a failure here
is normally either a real drift or a regeneration nobody ran.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from capability_audit import (  # noqa: E402
    CAPABILITIES,
    DOCUMENT,
    _markdown,
    build_audit,
)

E2E_ROOT = ROOT / "molsysviewer" / "js" / "tests" / "e2e"

#: What the report asked the audit to cover. Pinned so a capability cannot quietly leave
#: the table — the row disappearing is exactly as misleading as the row being wrong.
REQUIRED_CAPABILITIES = {
    "Whole", "Regions", "Layers", "Selections and active selection",
    "Representations, styles and presets", "Annotations", "Measurements", "Shapes",
    "Trajectories and frames", "Trajectory plot", "Movie", "Camera",
    "save_state / load_state", "HTML export and replay", "Popup",
    "Standalone (Qt host)", "Add-ons", "MolSysMT integration", "Units",
}


@pytest.fixture(scope="module")
def audit():
    return build_audit()


def test_every_required_capability_has_a_row():
    assert {capability.name for capability in CAPABILITIES} == REQUIRED_CAPABILITIES


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_every_declared_path_exists(capability):
    """A row pointing at a file that moved is the drift this table exists to prevent."""
    assert (ROOT / capability.anchor).exists(), capability.anchor

    if capability.docs is not None:
        assert (ROOT / capability.docs).exists(), capability.docs

    for name in capability.unit:
        assert (ROOT / "tests" / name).exists(), name

    for suite in capability.e2e:
        assert (E2E_ROOT / f"{suite}.e2e.ts").exists(), suite


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_every_row_names_a_public_api_that_exists(capability, audit):
    """`view.popup` was declared before this test; nothing answers to that name.

    A prefix matching zero public callables means the row describes a surface the
    inventory cannot see — either a typo or a capability reached some other way, and both
    need saying rather than rendering as a confident zero.
    """
    row = next(item for item in audit["rows"] if item["capability"] == capability.name)

    assert row["public_callables"] > 0, (
        f"{capability.name} declares {capability.api} and no public callable matches"
    )


def test_the_generated_document_is_current(audit):
    """The document is generated, so a stale one means somebody edited the source only."""
    assert DOCUMENT.exists(), "run python devtools/capability_audit.py --write"

    assert DOCUMENT.read_text(encoding="utf-8") == _markdown(audit) + "\n", (
        "devguide/capability_audit.md is out of date; regenerate it with "
        "`python devtools/capability_audit.py --write`"
    )


def test_the_generated_document_is_not_edited_by_hand():
    assert "do not edit by hand" in DOCUMENT.read_text(encoding="utf-8")


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_status_is_a_word_the_document_defines(capability):
    assert capability.status in {"stable", "experimental", "roadmap"}


@pytest.mark.parametrize(
    "capability",
    [c for c in CAPABILITIES if c.status == "stable"],
    ids=lambda c: c.name,
)
def test_stable_means_someone_could_depend_on_it(capability):
    """`stable` is a claim about what a user may rely on, so it needs evidence.

    The minimum is unit coverage: a capability nobody tests cannot be one whose changes we
    would notice. Documentation and E2E coverage are reported in their own columns rather
    than folded in here, because *implemented and undocumented* is a real and different
    state — four capabilities are in it, and calling them experimental would be a
    different falsehood.
    """
    assert capability.unit, f"{capability.name} claims stable with no unit tests"


def test_experimental_rows_say_why():
    """An `experimental` with no note is an opinion; with a note it is a finding."""
    silent = [c.name for c in CAPABILITIES if c.status == "experimental" and not c.note]

    assert silent == [], f"experimental without a stated reason: {silent}"


def test_the_generator_runs_as_a_command():
    """It is meant to be run by a person before a release, not only imported by a test."""
    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "capability_audit.py")],
        capture_output=True, text=True, cwd=ROOT, timeout=900,
    )

    assert completed.returncode == 0, completed.stderr
    assert "| Capability |" in completed.stdout


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_evidence_is_derived_and_never_asserted(capability, audit):
    """Four of the five labels come from what the audit already knows.

    Only `benchmarked` and `human-observed` are declared, and both must name where the
    evidence is. A label a row simply claims about itself is the failure the whole audit
    exists to prevent.
    """
    from capability_audit import EVIDENCE

    row = next(item for item in audit["rows"] if item["capability"] == capability.name)

    assert set(row["evidence"]) <= set(EVIDENCE), row["evidence"]
    assert "implemented" in row["evidence"]
    assert ("contract-tested" in row["evidence"]) is bool(capability.unit)
    assert ("browser-observed" in row["evidence"]) is bool(capability.e2e)


@pytest.mark.parametrize(
    "capability",
    [c for c in CAPABILITIES if c.benchmark],
    ids=lambda c: c.name,
)
def test_a_benchmarked_capability_names_a_document_that_exists(capability):
    """`benchmarked` without a record is the claim, not the evidence."""
    assert (ROOT / "devguide" / capability.benchmark).is_file(), capability.benchmark


@pytest.mark.parametrize(
    "capability",
    [c for c in CAPABILITIES if c.human_observed],
    ids=lambda c: c.name,
)
def test_human_observation_carries_its_date(capability):
    """Somebody watched it *on some day*, and the day is most of the information.

    An undated "we looked at it" ages into a claim nobody can check. The Qt entry says
    2026-07-04 and says that the session found a defect, which is what a person watching
    is for.
    """
    import re

    assert re.match(r"^\d{4}-\d{2}-\d{2}", capability.human_observed), capability.human_observed


def test_the_document_names_what_nothing_has_watched_draw():
    """The finding is the point of the column, so it must survive regeneration.

    Four capabilities have no browser observation, and two of them are `stable`. That is
    defensible — neither draws anything — but it is a claim the document should make out
    loud rather than leave as a zero somebody has to notice.
    """
    text = DOCUMENT.read_text(encoding="utf-8")

    assert "## Nothing has watched these draw" in text
    for name in ("Trajectory plot", "Movie", "save_state / load_state", "Units"):
        assert name in text.split("## Nothing has watched these draw", 1)[1].split("##", 1)[0]


def test_the_two_axes_are_not_confused_with_each_other():
    """`evidence` qualifies a capability; `verification` qualifies a report.

    They read alike and mean different things, so the document says so where a reader
    meets both.
    """
    text = DOCUMENT.read_text(encoding="utf-8")

    assert "Two columns, two questions" in text
    assert "reporting_protocol.md" in text
