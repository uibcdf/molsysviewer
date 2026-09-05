"""The release gate itself, pinned.

`devtools/release_gate.py` is gate 11 of the pre-1.0 plan: the final smoke matrix and the
release-version consistency checks, in one command. It is the one place that must not
quietly skip: a step whose prerequisite is missing is reported `BLOCKED` with the reason
and the gate exits non-zero, because a gate that skips what it cannot do passes on an
untested release.

These tests check that property rather than running the gate. Running it takes the whole
suite plus a browser, and a test that invokes the suite from inside the suite is a
recursion nobody wants.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from release_gate import STEPS, _check_version_consistency  # noqa: E402


def test_the_gate_lists_its_steps_without_running_them():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "release_gate.py"), "--list"],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )

    assert completed.returncode == 0, completed.stderr
    assert "the full Python suite" in completed.stdout


def test_every_step_can_either_run_or_say_why_not():
    """A step with no command and no reason is a hole the gate would pass through."""
    holes = [step.name for step in STEPS if step.command is None
             and step.blocked_by is None and step.name != "version"]

    assert holes == [], f"steps that neither run nor explain themselves: {holes}"


def test_the_blocked_steps_name_what_they_are_waiting_for():
    """The two that cannot run here are Phase 7's screen and Phase 10's sibling releases.

    Their reasons are the load-bearing part: this repository's remaining pre-1.0 work is
    almost entirely those two, and a gate that said only "skipped" would hide it.
    """
    reasons = {step.name: step.blocked_by() for step in STEPS if step.blocked_by}

    assert reasons.get("conda"), "the conda step must always state why it cannot run"
    assert "gates 1-5" in reasons["conda"]
    # `qt` is blocked here and not on a machine with a screen, which is the point.
    if reasons.get("qt"):
        assert "DISPLAY" in reasons["qt"]


def test_the_version_check_enforces_the_runtime_and_only_reports_the_manifest():
    """Two invariants with different strengths, and the distinction is deliberate.

    `viewer.js` is enforced: Python packaging never runs npm, so a stale runtime ships in
    the wheel exactly as it sits in the checkout. `package.json` is reported: the publish
    workflow runs `npm run build`, which syncs it, so failing on it would make the gate
    refuse a release over something CI repairs — and a false gate teaches people to pass
    `--only`.
    """
    passed, detail = _check_version_consistency()

    assert passed, detail
    assert "viewer.js carries" in detail


def test_the_gate_reports_blocked_steps_as_a_non_zero_exit():
    """Exit 2 means "not cleared", distinct from exit 1 "failing".

    Both are non-zero on purpose. The distinction matters to a human reading the tail of a
    log: one says something is broken, the other says something was never checked.
    """
    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "release_gate.py"), "--only", "conda"],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )

    assert completed.returncode == 2, completed.stdout
    assert "RELEASE NOT CLEARED" in completed.stdout


def test_the_gate_does_not_run_a_writer_where_a_check_belongs():
    """An early draft ran `capability_audit.py --write` and `--write-baseline` as steps.

    Both regenerate rather than refuse, so the gate would have repaired a stale artefact
    and passed. The suite checks their currency instead; pinned here so the writers do not
    come back.
    """
    source = (ROOT / "devtools" / "release_gate.py").read_text(encoding="utf-8")
    commands = [" ".join(step.command) for step in STEPS if step.command]

    assert not any("--write" in command for command in commands), commands
    assert "worse than not checking" in source
