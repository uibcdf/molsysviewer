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
from public_api_inventory import build_inventory  # noqa: E402

E2E_ROOT = ROOT / "molsysviewer" / "js" / "tests" / "e2e"

#: What the report asked the audit to cover. Pinned so a capability cannot quietly leave
#: the table — the row disappearing is exactly as misleading as the row being wrong.
REQUIRED_CAPABILITIES = {
    "Whole", "Regions", "Layers", "Selections and active selection",
    "Representations, styles and presets", "Annotations", "Measurements", "Shapes",
    "Trajectories and frames", "Trajectory plot", "Movie", "Camera",
    "save_state / load_state",
    # Added 2026-09-02 with the capability itself (#38): a session carries the molecular
    # system, which a state document deliberately does not, so it is a second capability
    # rather than a wider first one.
    "save_session / load_session",
    "HTML export and replay", "Popup",
    "Standalone (Qt host)", "Add-ons", "MolSysMT integration", "Units",
}


#: Capability entry points that no documentation mentions yet, and where the gap is.
#:
#: **Empty, and meant to stay that way.** `uibcdf/molsysviewer#68` was one instance —
#: `save_session` shipped with no page naming it — and the guard written to catch it found
#: fifteen more. Nine were index lines in `public_api.md` and were fixed on the spot; the
#: seven that needed user-facing prose were `uibcdf/molsysviewer#72`, and writing it emptied
#: this list.
#:
#: Nothing may be added here to make a failure go away. Adding an entry means deciding, on
#: purpose, to ship a capability users cannot find.
KNOWN_UNDOCUMENTED = frozenset()


@pytest.fixture(scope="module")
def audit():
    return build_audit()


@pytest.fixture(scope="module")
def inventory_paths():
    """Module-scoped because `build_inventory` costs ~3.9 s and ~557 MiB per call.

    The parametrised guard below runs once per capability; calling it inside the test
    would pay that twenty times over, in each of twelve xdist workers at once.
    """
    return {item["path"] for item in build_inventory()["callables"]}


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


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_every_declared_api_entry_resolves_on_its_own(capability, inventory_paths):
    """The row-level check above is not enough, and uibcdf/molsysviewer#79 is the proof.

    It asks whether a *row* matches anything, so a dead entry sitting beside live siblings
    is invisible. `view.convert` sat in the MolSysMT row for the whole of 0.22 matching
    nothing at all, and the row stayed green on the strength of `view.extract`.

    `view.get` was worse. It had been removed too, but `_api_evidence` matches by prefix,
    so it absorbed ten unrelated methods that merely start with those characters --
    `view.get_camera_snapshot`, `view.get_last_click_event` and eight more frontend event
    accessors -- into a row whose provenance is declared "MolSysMT (scientific authority)".
    The row did not just survive; it reported 17 public callables where it has 7. A guard
    asking "does this prefix match anything" passes for `view.get`, which is precisely the
    entry that was lying.

    The distinction is punctuation, and the table is already written with it: an entry
    ending in `.` is a namespace and needs at least one member; an entry that does not name
    one callable and must resolve exactly. Nothing extra has to be declared.
    """
    for entry in capability.api:
        if entry.endswith("."):
            assert any(path.startswith(entry) for path in inventory_paths), (
                f"{capability.name} declares the namespace {entry!r} and it has no public "
                f"members; the row describes a surface the inventory cannot see"
            )
        else:
            assert entry in inventory_paths, (
                f"{capability.name} declares {entry!r}, which does not exist. If a longer "
                f"unrelated name shares its prefix the row will still look healthy and its "
                f"public count will be inflated -- see uibcdf/molsysviewer#79"
            )


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_every_capability_is_documented_where_its_row_points(capability):
    """The direction `test_public_api_docs.py` does not check: does the doc mention it?

    That test verifies every *documented* symbol exists. Nothing verified the converse, so
    `save_session` and `load_session` shipped with no prose page naming them and no line in
    `public_api.md` — `uibcdf/molsysviewer#68`. A capability whose own row links a page that
    never mentions it is a capability users cannot find.

    Both places are checked because they fail apart: `public_api.md` is the developer
    index, the linked page is where a user is sent.
    """
    page = ROOT / capability.docs
    assert page.exists(), f"{capability.name} links {capability.docs}, which does not exist"

    page_text = page.read_text(encoding="utf-8")
    api_text = (ROOT / "docs" / "content" / "developer" / "public_api.md").read_text(
        encoding="utf-8"
    )

    for entry_point in capability.api:
        # A row may declare a prefix (`view.layers.`), a whole name (`view.save_state`)
        # or an indexed form (`view.regions[…].`). The bare attribute is what prose
        # actually writes, so reduce every shape to that.
        name = entry_point.rstrip(".").split(".")[-1].split("[")[0]

        if (entry_point, "page") not in KNOWN_UNDOCUMENTED:
            assert name in page_text, (
                f"{capability.name} points at {capability.docs}, which never mentions "
                f"{entry_point!r}. A user sent there cannot find the capability."
            )
        if (entry_point, "public_api") not in KNOWN_UNDOCUMENTED:
            assert name in api_text, (
                f"{capability.name} declares {entry_point!r} and public_api.md does not "
                f"mention it."
            )


def test_the_undocumented_baseline_does_not_rot():
    """An entry that got documented must leave the list, or the list stops meaning anything.

    Without this, documenting something would silently keep its exemption and the next
    regression on the same symbol would pass.
    """
    api_text = (ROOT / "docs" / "content" / "developer" / "public_api.md").read_text(
        encoding="utf-8"
    )
    pages = {c.api: (ROOT / c.docs) for c in CAPABILITIES}

    stale = []
    for entry_point, where in KNOWN_UNDOCUMENTED:
        name = entry_point.rstrip(".").split(".")[-1].split("[")[0]
        if where == "public_api":
            if name in api_text:
                stale.append((entry_point, where))
        else:
            for api, page in pages.items():
                if entry_point in api and name in page.read_text(encoding="utf-8"):
                    stale.append((entry_point, where))

    assert stale == [], (
        f"these are documented now — remove them from KNOWN_UNDOCUMENTED: {stale}"
    )


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_a_stable_capability_has_earned_the_label(capability):
    """`uibcdf/molsysviewer#65`: nothing stopped a `stable` claim being inherited.

    A capability is `stable` on evidence, and for a viewer the strongest evidence is that
    somebody or something watched it draw. Two rows carried the label with neither an E2E
    suite nor a human observation, and the audit itself called that "the kind of claim that
    should be made on purpose rather than inherited". Nothing had made it on purpose.

    So a `stable` capability must carry one of three things: an E2E suite, a dated human
    observation, or a written statement that it draws nothing and therefore cannot have
    either. The third is a claim in its own right, and the next test checks it is not used
    to wave away something that does draw.
    """
    if capability.status != "stable":
        return

    assert capability.e2e or capability.human_observed or capability.stable_without_drawing, (
        f"{capability.name} is declared stable with no browser evidence and no reason given. "
        f"Add an E2E suite, a dated human_observed, or state in stable_without_drawing why "
        f"it draws nothing."
    )


@pytest.mark.parametrize("capability", CAPABILITIES, ids=lambda c: c.name)
def test_the_draws_nothing_claim_is_not_an_escape_hatch(capability):
    """A capability that has watched evidence cannot also claim it draws nothing.

    Without this, `stable_without_drawing` would be a sentence anybody could add to silence
    the test above, which would make the exemption worse than no exemption.
    """
    if not capability.stable_without_drawing:
        return

    assert not capability.e2e and not capability.human_observed, (
        f"{capability.name} claims it draws nothing, yet carries browser evidence "
        f"({capability.e2e or capability.human_observed}). One of the two is wrong."
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


def test_the_document_names_what_nothing_has_watched_draw(audit):
    """The finding is the point of the column, so it must survive regeneration.

    Derived rather than listed. It used to name four capabilities outright, which made it
    a record of one afternoon: when `trajectory-plot` and `movie-playback` earned
    `browser-observed` on 2026-09-05 the test failed for having been right before. What
    must hold is that *whatever* currently lacks the label is named in the document, not
    that a particular set of four still lacks it.
    """
    text = DOCUMENT.read_text(encoding="utf-8")
    unobserved = [
        row["capability"] for row in audit["rows"]
        if "browser-observed" not in row["evidence"]
    ]
    assert unobserved, "every capability is browser-observed; this section should be gone"

    assert "## Nothing has watched these draw" in text
    section = text.split("## Nothing has watched these draw", 1)[1].split("##", 1)[0]
    for name in unobserved:
        assert name in section, f"{name} has no browser observation and the document does not say so"


def test_the_undrawable_reasons_reach_the_reader():
    """A reason written where nobody reads it is not a reason given.

    `stable_without_drawing` existed and was filled for both rows, and the generator
    never rendered it: it lived in `devtools/capability_audit.py`, which a reader of the
    audit does not open. The claim therefore still looked inherited in the only place it
    is published, which is what uibcdf/molsysviewer#65 asked to fix.
    """
    text = DOCUMENT.read_text(encoding="utf-8")
    undrawable = [c for c in CAPABILITIES if c.stable_without_drawing]
    assert undrawable, "nothing declares stable_without_drawing; this guard is vacuous"

    assert "## Declared `stable` without drawing anything" in text
    section = text.split("## Declared `stable` without drawing anything", 1)[1].split("\n## ", 1)[0]
    for capability in undrawable:
        assert capability.name in section, f"{capability.name} states its reason only in the source"
        # The reason itself, not just the name: a bare list would read as another gap.
        opening = capability.stable_without_drawing.split(".")[0]
        assert opening in section, f"{capability.name} is named without its reason"


def test_the_two_axes_are_not_confused_with_each_other():
    """`evidence` qualifies a capability; `verification` qualifies a report.

    They read alike and mean different things, so the document says so where a reader
    meets both.
    """
    text = DOCUMENT.read_text(encoding="utf-8")

    assert "Two columns, two questions" in text
    assert "reporting_protocol.md" in text
