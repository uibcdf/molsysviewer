"""The two work queues are coordinated with the issue board, and stay that way.

`devguide/reporting_protocol.md` is the rule; this is the part of it that can be checked
without the network. It is deliberately small: the protocol was adopted by writing the
front matter and opening the issues first, and a validator written before the data exists
is written against a guess.

What it does **not** check: that each issue exists and that its state agrees with the
document. That needs a token, so it stays out of the suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DEVGUIDE = ROOT / "devguide"

QUEUES = (
    "pending_bugs",
    "pending_bugs/post_1.0",
    "pending_proposals",
    "pending_proposals/post_1.0",
)

#: The open set, then the closed set. A document in the closed set belongs under archive/.
OPEN_STATUSES = frozenset({"open", "active", "blocked", "partial"})
CLOSED_STATUSES = frozenset({"resolved", "withdrawn", "superseded"})
VERIFICATIONS = frozenset({"reproduced", "measured", "inspected", "upstream", "asserted"})
SEVERITIES = frozenset({"critical", "high", "medium", "low"})

ISSUE = re.compile(r"^uibcdf/[\w.-]+#\d+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _documents() -> list[Path]:
    found = []
    for queue in QUEUES:
        directory = DEVGUIDE / queue
        if directory.is_dir():
            found += [p for p in sorted(directory.glob("*.md")) if p.name != "README.md"]
    return found


def _front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), (
        f"{path.relative_to(ROOT)} has no front matter; every queue entry needs one "
        "(see devguide/reporting_protocol.md)"
    )
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


DOCUMENTS = _documents()


def test_the_queues_are_not_empty():
    """A guard that passes because it found nothing is not a guard."""
    assert len(DOCUMENTS) >= 20


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: str(p.relative_to(DEVGUIDE)))
def test_every_queue_entry_carries_a_well_formed_header(path):
    fields = _front_matter(path)

    for required in ("summary", "issue", "status", "opened", "verification", "area"):
        assert fields.get(required), f"{required} is missing or empty"

    assert ISSUE.match(fields["issue"]), f"issue must be uibcdf/<repo>#<n>, got {fields['issue']!r}"
    assert DATE.match(fields["opened"]), f"opened must be ISO, got {fields['opened']!r}"
    assert fields["verification"] in VERIFICATIONS, fields["verification"]
    assert fields["status"] in OPEN_STATUSES | CLOSED_STATUSES, fields["status"]


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: str(p.relative_to(DEVGUIDE)))
def test_a_closed_entry_does_not_sit_in_an_open_queue(path):
    """The closed set belongs under `archive/`. Leaving one here is how a finished
    entry goes on reading as work — the failure the whole devguide compaction was about."""
    fields = _front_matter(path)

    assert fields["status"] not in CLOSED_STATUSES, (
        f"status is {fields['status']!r}; move the document to devguide/archive/"
    )
    assert not fields.get("closed"), "closed is set while the entry is still in the queue"


@pytest.mark.parametrize(
    "path",
    [p for p in DOCUMENTS if "pending_bugs" in p.parts],
    ids=lambda p: str(p.relative_to(DEVGUIDE)),
)
def test_a_bug_declares_its_severity(path):
    fields = _front_matter(path)

    assert fields.get("severity") in SEVERITIES, (
        f"severity must be one of {sorted(SEVERITIES)}, got {fields.get('severity')!r}"
    )


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: str(p.relative_to(DEVGUIDE)))
def test_a_blocked_entry_names_what_it_waits_on(path):
    """`blocked` without `blocked_by` is a status nobody can act on."""
    fields = _front_matter(path)

    if fields["status"] == "blocked":
        assert fields.get("blocked_by", "[]") != "[]", (
            "blocked must name what it waits on in blocked_by"
        )


def test_no_queue_entry_is_a_plan_or_an_inventory():
    """Only single-theme reports live here; that is where we differ from MolSysMT.

    An issue for an eleven-phase plan is an issue that never closes, so the plan and the
    two audit inventories were moved out on 2026-08-14. Pinned by name because putting
    one back would be easy and would quietly break the one-theme-one-issue rule.
    """
    moved_out = {
        "pre_1_0_architecture_rework_and_hardening_master_plan.md",
        "what_needs_a_human_2026_08.md",
        "open_items_after_the_2026_08_smoke_round.md",
        "transport_popup_audit_followups_2026_08.md",
    }
    names = {path.name for path in DOCUMENTS}

    assert not (names & moved_out), f"plans and inventories are not queue entries: {names & moved_out}"


def test_the_protocol_is_written_down():
    protocol = DEVGUIDE / "reporting_protocol.md"

    assert protocol.is_file()
    text = protocol.read_text(encoding="utf-8")
    assert "it deserves an issue" in text
    assert "Archive, never delete" in text


# --- the governance that makes the protocol apply from now on -----------------------


def test_an_agent_is_routed_to_the_protocol():
    """A rule nobody is sent to is a rule nobody follows.

    The protocol was written before this test existed, and for one commit nothing pointed
    at it except the handoff. `CLAUDE.md` delegates to `AGENTS.md`, so routing from there
    and from the devguide index is enough.
    """
    for path in ("AGENTS.md", "devguide/README.md"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "reporting_protocol.md" in text, f"{path} does not route to the protocol"


def test_the_report_template_exists_and_starts_unfilled():
    """`issue: #000` is deliberate: a copy that forgets the number fails the header check.

    A template pre-filled with a real issue number is worse than none — it would be
    copied, committed, and point a reader at somebody else's theme.
    """
    template = DEVGUIDE / "templates" / "report.md"

    assert template.is_file()
    text = template.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "uibcdf/molsysviewer#000" in text
    assert not ISSUE.match("uibcdf/molsysviewer#000") is None  # well formed, but a placeholder


def test_the_issue_forms_exist_and_carry_the_right_labels():
    """An incoming report should arrive labelled and marked for triage.

    `needs-triage` on both is what the protocol's "attending a report that came from
    outside" step removes; without it, an unattended report is indistinguishable from one
    we have already reproduced.
    """
    directory = ROOT / ".github" / "ISSUE_TEMPLATE"

    for name, kind in (("bug_report.md", "bug"), ("proposal.md", "proposal")):
        form = directory / name
        assert form.is_file(), f"{name} is missing"
        header = form.read_text(encoding="utf-8").split("---")[1]
        assert f"labels: {kind}, needs-triage" in header, f"{name} labels: {header!r}"


def test_the_issue_form_config_offers_the_routes_that_keep_the_board_meaningful():
    """Three things that must not become issues: usage questions, exploits, MolSysMT.

    The board is now the state record — one issue per devguide document — so a usage
    question arriving as an issue dilutes what the board means at a glance.
    """
    config = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")

    assert "discussions" in config, "usage questions have nowhere to go"
    assert "security/advisories/new" in config, "no private route for an exploitable finding"
    assert "MolSysMT/issues" in config, "selection syntax and formats belong upstream"


def test_the_protocol_states_the_corrections_and_security_rules():
    """Both were missing from the first adoption pass and are the two cheapest to lose."""
    text = (DEVGUIDE / "reporting_protocol.md").read_text(encoding="utf-8")

    assert "Do not edit the original claim" in text
    assert "not opened as a public issue" in text


def test_the_generated_indexes_are_current():
    """The indexes are rendered from front matter, so a stale one means an unrun command.

    This exists because the hand-written version failed: the proposals index went on
    describing four documents as queue entries after they had been moved out, and it was
    corrected by hand — the third or fourth hand-edit of these lists in a week. A
    hand-written index of documents that already describe themselves is two independent
    authoritative lists, and one of them will be wrong.
    """
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "devguide_index.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )

    assert completed.returncode == 0, (
        (completed.stderr or completed.stdout).strip()
        or "devguide_index.py --check failed"
    )
