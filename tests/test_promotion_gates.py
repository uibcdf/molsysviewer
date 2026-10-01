"""Promotion requires current coverage and an installed Windows launcher run."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_promotion_gates", ROOT / "devtools/conda-build/verify_promotion_gates.py"
)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


@pytest.fixture
def records():
    arguments = {
        "viewer_commit": "a" * 40,
        "version": "0.24.0",
        "build_number": 2,
        "sha256": "c" * 64,
        "pair_run_id": 101,
        "windows_run_id": 102,
        "molsysmt_commit": "b" * 40,
        "molsysmt_version": "0.23.0",
        "molsysmt_build_number": 3,
    }
    pair = {
        "id": 101,
        "run_attempt": 2,
        "repository": {"full_name": "uibcdf/molsysmt"},
        "head_sha": "b" * 40,
        "path": ".github/workflows/validate_conda_staging.yaml",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "display_title": "MT 0.23.0 build 3 + Viewer 0.24.0 build 2 | Python 3.14 | all",
    }
    pair_jobs = []
    for platform in ("linux-64", "linux-aarch64", "osx-arm64", "win-64"):
        for python in ("3.11", "3.12", "3.13", "3.14"):
            pair_jobs.append(
                {
                    "name": f"{platform} · Python {python}",
                    "run_id": 101,
                    "run_attempt": 2,
                    "status": "completed",
                    "conclusion": "success",
                    "steps": [
                        {
                            "name": "Validate versions, provenance, native code, BCIF, PDB text, and viewer resources",
                            "conclusion": "success",
                        }
                    ],
                }
            )
    pair_jobs.append(
        {
            "name": "Validate the requested package versions",
            "run_id": 101,
            "run_attempt": 2,
            "status": "completed",
            "conclusion": "success",
        }
    )
    windows = {
        "id": 102,
        "run_attempt": 3,
        "repository": {"full_name": "uibcdf/molsysviewer"},
        "head_sha": "a" * 40,
        "path": ".github/workflows/verify_staged_noarch_launchers.yaml",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "display_title": "Viewer 0.24.0 build 2 | Windows launchers | sha256 " + "c" * 64,
    }
    windows_jobs = [
        {
            "name": "windows-launchers",
            "run_id": 102,
            "run_attempt": 3,
            "status": "completed",
            "conclusion": "success",
            "steps": [
                {"name": name, "conclusion": "success"}
                for name in (
                    "Validate candidate checkout",
                    "Install the exact staged Conda package",
                    "Verify installed record and commands outside the checkout",
                )
            ],
        }
    ]
    return arguments, pair, {"total_count": 17, "jobs": pair_jobs}, windows, {"total_count": 1, "jobs": windows_jobs}


def verify_records(records):
    arguments, pair, pair_jobs, windows, windows_jobs = records
    reader = gate.evidence.LiveEvidence()
    for repository, run, jobs in (("uibcdf/molsysmt", pair, pair_jobs), ("uibcdf/molsysviewer", windows, windows_jobs)):
        base = f"repos/{repository}/actions/runs/{run['id']}"
        reader.cache[base] = json.dumps(run).encode()
        reader.cache[base + f"/attempts/{run['run_attempt']}/jobs?per_page=100"] = json.dumps(jobs).encode()
    return gate.verify(**arguments, reader=reader)


def test_current_matrix_and_candidate_windows_gate_are_accepted(records):
    assert verify_records(records) == "PASS: installed-pair run 101 and Windows launcher run 102"
    workflow = yaml.safe_load((ROOT / ".github/workflows/promote_conda_package.yaml").read_text())
    assert workflow[True]["workflow_dispatch"]["inputs"]["windows_run_id"]["required"] is True
    steps = workflow["jobs"]["promote"]["steps"]
    check = next(step for step in steps if step.get("name") == "Validate release identity and installed-pair gate")
    assert check["env"]["WINDOWS_RUN_ID"] == "${{ inputs.windows_run_id }}"
    assert "python3 devtools/conda-build/verify_promotion_gates.py" in check["run"]
    assert '--pair-run-id "$PAIR_RUN_ID" --windows-run-id "$WINDOWS_RUN_ID"' in check["run"]
    assert steps.index(check) < next(i for i, step in enumerate(steps) if step.get("id") == "promotion")


@pytest.mark.parametrize(
    "change",
    [
        "historical",
        "duplicate",
        "failed",
        "skipped-science",
        "other-attempt",
        "missing",
        "public",
        "other-commit",
        "wrong-build",
        "wrong-workflow",
    ],
)
def test_unqualified_pair_cannot_be_promoted(records, change):
    _, run, jobs, _, _ = records
    if change == "historical":
        for python in ("3.11", "3.12", "3.13", "3.14"):
            job = dict(jobs["jobs"][0], name=f"osx-64 · Python {python}")
            jobs["jobs"].append(job)
        jobs["total_count"] = 21
    elif change == "duplicate":
        jobs["jobs"][1] = jobs["jobs"][0]
    elif change == "failed":
        jobs["jobs"][0]["conclusion"] = "failure"
    elif change == "skipped-science":
        jobs["jobs"][0]["steps"][0]["conclusion"] = "skipped"
    elif change == "other-attempt":
        jobs["jobs"][0]["run_attempt"] = 1
    elif change == "missing":
        jobs["jobs"].pop()
        jobs["total_count"] -= 1
    elif change == "public":
        run["display_title"] += " | public"
    elif change == "other-commit":
        run["head_sha"] = "d" * 40
    elif change == "wrong-build":
        run["display_title"] = run["display_title"].replace("Viewer 0.24.0 build 2", "Viewer 0.24.0 build 7")
    else:
        run["path"] = ".github/workflows/CI.yaml"
    with pytest.raises(gate.evidence.InvalidEvidence):
        verify_records(records)


@pytest.mark.parametrize(
    "change",
    [
        "other-commit",
        "other-version",
        "other-build",
        "other-digest",
        "public-workflow",
        "failure",
        "other-attempt",
        "missing-job",
        "duplicate-job",
        "pull-request",
    ],
)
def test_unqualified_windows_cannot_be_promoted(records, change):
    _, _, _, run, jobs = records
    if change == "other-commit":
        run["head_sha"] = "d" * 40
    elif change == "other-version":
        run["display_title"] = run["display_title"].replace("0.24.0", "0.24.1")
    elif change == "other-build":
        run["display_title"] = run["display_title"].replace("build 2", "build 7")
    elif change == "other-digest":
        run["display_title"] = run["display_title"].replace("c" * 64, "d" * 64)
    elif change == "public-workflow":
        run["path"] = ".github/workflows/verify_public_conda_package.yaml"
    elif change == "failure":
        run["conclusion"] = "failure"
    elif change == "other-attempt":
        jobs["jobs"][0]["run_attempt"] = 2
    elif change == "missing-job":
        jobs["jobs"].clear()
        jobs["total_count"] = 0
    elif change == "duplicate-job":
        jobs["jobs"].append(jobs["jobs"][0])
        jobs["total_count"] = 2
    else:
        run["event"] = "pull_request"
    with pytest.raises(gate.evidence.InvalidEvidence):
        verify_records(records)


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("change", ["missing", "skipped", "failed"])
def test_windows_steps_must_execute(records, index, change):
    steps = records[4]["jobs"][0]["steps"]
    if change == "missing":
        steps.pop(index)
    else:
        steps[index]["conclusion"] = "skipped" if change == "skipped" else "failure"
    with pytest.raises(gate.evidence.InvalidEvidence):
        verify_records(records)


def test_windows_workflow_binds_title_and_checkout_to_candidate():
    workflow = yaml.safe_load((ROOT / ".github/workflows/verify_staged_noarch_launchers.yaml").read_text())
    assert workflow["run-name"] == (
        "Viewer ${{ inputs.version }} build ${{ inputs.build_number }} | Windows launchers | sha256 ${{ inputs.sha256 }}"
    )
    steps = workflow["jobs"]["windows-launchers"]["steps"]
    checkout = next(step for step in steps if step.get("name") == "Validate candidate checkout")
    assert checkout["env"]["CANDIDATE_SHA"] == "${{ inputs.candidate_sha }}"
    assert 'test "$CANDIDATE_SHA" = "$GITHUB_SHA"' in checkout["run"]
    assert 'test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"' in checkout["run"]
    assert steps.index(checkout) < next(i for i, step in enumerate(steps) if step.get("name", "").startswith("Install"))
