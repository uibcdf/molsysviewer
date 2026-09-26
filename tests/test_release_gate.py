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

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from release_gate import STEPS, _check_version_consistency  # noqa: E402


def test_release_gate_requires_core_e2e_without_requiring_remote_preview():
    e2e_step = next(step for step in STEPS if step.name == "e2e")

    assert e2e_step.command == ["npm", "run", "test:e2e:core"]
    assert "remote preview is post-1.0" in e2e_step.what


def test_the_gate_lists_its_steps_without_running_them():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "release_gate.py"), "--list"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
    )

    assert completed.returncode == 0, completed.stderr
    assert "the full Python suite" in completed.stdout


def test_every_step_can_either_run_or_say_why_not():
    """A step with no command and no reason is a hole the gate would pass through."""
    holes = [step.name for step in STEPS if step.command is None and step.blocked_by is None and step.name != "version"]

    assert holes == [], f"steps that neither run nor explain themselves: {holes}"


def test_the_blocked_steps_name_what_they_are_waiting_for():
    """The two that cannot run here are Phase 7's screen and the final 1.0 pair.

    Their reasons are the load-bearing part: this repository's remaining pre-1.0 work is
    almost entirely those two, and a gate that said only "skipped" would hide it.
    """
    reasons = {step.name: step.blocked_by() for step in STEPS if step.blocked_by}

    assert reasons.get("conda"), "the conda step must always state why it cannot run"
    assert "final-version Conda pair" in reasons["conda"]
    assert "pre-1.0 pair" in reasons["conda"]
    assert "gates 1-5 of Phase 10 are open" not in reasons["conda"]
    # `qt` is blocked here and not on a machine with a screen, which is the point.
    if reasons.get("qt"):
        assert "DISPLAY" in reasons["qt"]


def _checkout(tmp_path, runtime_version, manifest_version="4.5.6"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    runtime = tmp_path / "viewer.js"
    runtime.write_text(f'var v="{runtime_version}";\n', encoding="utf-8")
    manifest = tmp_path / "package.json"
    manifest.write_text(json.dumps({"version": manifest_version}), encoding="utf-8")
    return runtime, manifest


def test_the_version_check_notices_a_runtime_built_from_another_version(tmp_path):
    """The failure it exists for: a wheel shipping a runtime someone else's checkout built.

    Checked on versions this test chooses rather than on the versions this machine happens
    to have. Asserting the latter made the suite fail on every development checkout from
    the first commit after a release — a true statement about a released artefact, made in
    the one place where it is routinely false (uibcdf/molsysviewer#88). The gate still
    makes it, on the checkout, where it is the question being asked.
    """
    runtime, manifest = _checkout(tmp_path, "1.2.3")

    passed, detail = _check_version_consistency("4.5.6", runtime=runtime, manifest=manifest)

    assert not passed
    assert "4.5.6" in detail, "the message must name the version the package reports"
    assert "npm run build:runtime" in detail, "and say what to do about it"


def test_the_version_check_accepts_a_runtime_that_carries_the_reported_version(tmp_path):
    """The other direction, so the check cannot pass by always refusing.

    The manifest is *reported*, not enforced: `npm run build` syncs it at publish time, so
    failing on it would make the gate refuse a release over something CI repairs — and a
    false gate teaches people to pass `--only`.
    """
    runtime, manifest = _checkout(tmp_path, "4.5.6+7.gabcdef", manifest_version="4.5.6")

    passed, detail = _check_version_consistency("4.5.6+7.gabcdef", runtime=runtime, manifest=manifest)

    assert passed, detail
    assert "viewer.js carries 4.5.6+7.gabcdef" in detail

    lagging, _ = _checkout(tmp_path / "lagging", "4.5.6+7.gabcdef", manifest_version="4.5.5")
    passed, detail = _check_version_consistency(
        "4.5.6+7.gabcdef", runtime=lagging, manifest=lagging.parent / "package.json"
    )

    assert passed, "a lagging manifest is reported, not enforced"
    assert "lags at '4.5.5'" in detail


def test_the_version_check_refuses_a_runtime_that_is_not_there(tmp_path):
    """`viewer.js` is a build product and git-ignored in some checkouts; absence is a failure,
    not an exemption."""
    passed, detail = _check_version_consistency("4.5.6", runtime=tmp_path / "absent.js")

    assert not passed
    assert "missing" in detail


def test_the_gate_reports_blocked_steps_as_a_non_zero_exit():
    """Exit 2 means "not cleared", distinct from exit 1 "failing".

    Both are non-zero on purpose. The distinction matters to a human reading the tail of a
    log: one says something is broken, the other says something was never checked.
    """
    completed = subprocess.run(
        [sys.executable, str(ROOT / "devtools" / "release_gate.py"), "--only", "conda"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
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
