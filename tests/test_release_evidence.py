"""Candidate identity and independent release evidence must fail closed."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from release_evidence import (  # noqa: E402
    PLATFORMS,
    PYTHONS,
    CandidateEvidence,
    InvalidEvidence,
    LiveEvidence,
    MissingEvidence,
    check_environment,
    check_pair_run,
    check_registry,
    check_run,
    read_environment_archive,
    validate_plan,
)
from release_gate import STEPS, _run, _summarize  # noqa: E402


@pytest.fixture
def candidate(tmp_path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Release test",
            "-c",
            "user.email=release@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "Candidate",
        ],
        cwd=checkout,
        check=True,
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
    plan = {
        "schema": "molsysviewer.release-evidence/1",
        "molsysviewer": {
            "version": "1.0.0",
            "commit": commit,
            "build_number": 2,
            "files": [{"subdir": "noarch", "filename": "molsysviewer-1.0.0-py_2.tar.bz2", "sha256": "a" * 64}],
        },
        "molsysmt": {
            "version": "0.23.0",
            "commit": "b" * 40,
            "build_number": 3,
            "files": [
                {"subdir": platform, "filename": "molsysmt-0.23.0-pyabi3habcdef_3.conda", "sha256": str(index + 1) * 64}
                for index, platform in enumerate(PLATFORMS)
            ],
        },
        "conda": {"id": 101, "attempt": 1},
        "public_conda": {"id": 102, "attempt": 1},
        "hosted_e2e": {"id": 103, "attempt": 1},
    }
    path = tmp_path / "evidence.json"
    return checkout, plan, path


def pair_snapshot(plan, source):
    expected = plan["conda" if source == "staging" else "public_conda"]
    mt, viewer = plan["molsysmt"], plan["molsysviewer"]
    run = {
        "id": expected["id"],
        "run_attempt": expected["attempt"],
        "head_sha": mt["commit"],
        "repository": {"full_name": "uibcdf/molsysmt"},
        "path": ".github/workflows/validate_conda_staging.yaml",
        "status": "completed",
        "conclusion": "success",
        "run_started_at": "2026-10-01T10:00:00Z",
        "display_title": f"MT {mt['version']} build 3 + Viewer {viewer['version']} build 2 | Python 3.14 | all"
        + (" | public" if source == "public" else ""),
    }
    jobs = []
    for platform in PLATFORMS:
        for python in PYTHONS:
            jobs.append(
                {
                    "name": f"{platform} · Python {python}",
                    "run_id": run["id"],
                    "run_attempt": run["run_attempt"],
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
    jobs.append(
        {
            "name": "Validate the requested package versions",
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "status": "completed",
            "conclusion": "success",
        }
    )
    return run, {"total_count": len(jobs), "jobs": jobs}


def registry_snapshot(package, version, file):
    md5 = "c" * 32
    build = file["filename"].removeprefix(f"{package}-{version}-").removesuffix(".conda").removesuffix(".tar.bz2")
    release = {
        "distributions": [
            {
                "basename": file["subdir"] + "/" + file["filename"],
                "sha256": file["sha256"],
                "md5": md5,
                "labels": ["staging", "main"],
                "attrs": {"subdir": file["subdir"]},
            }
        ]
    }
    section = "packages.conda" if file["filename"].endswith(".conda") else "packages"
    index = {
        "info": {"subdir": file["subdir"]},
        section: {
            file["filename"]: {
                "name": package,
                "version": version,
                "sha256": file["sha256"],
                "md5": md5,
                "build": build,
                "build_number": int(build.rsplit("_", 1)[1]),
            }
        },
    }
    return release, index


def environment_snapshot(plan, platform, source):
    channel = "uibcdf/label/staging" if source == "staging" else "uibcdf"
    lines = ["@EXPLICIT"]
    for name in ("molsysviewer", "molsysmt"):
        file = next(
            item for item in plan[name]["files"] if item["subdir"] == ("noarch" if name == "molsysviewer" else platform)
        )
        lines.append(f"https://conda.anaconda.org/{channel}/{file['subdir']}/{file['filename']}#" + "c" * 32)
    return "\n".join(lines)


def archive_snapshot(text, run, platform, python):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(f"conda-{platform}-py{python}.txt", text)
    payload = buffer.getvalue()
    artifact = {
        "id": 1000,
        "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "workflow_run": {"id": run["id"], "head_sha": run["head_sha"]},
        "created_at": "2026-10-01T11:00:00Z",
        "expired": False,
    }
    return payload, artifact


def recorded_pair(plan, source):
    """Preload the live reader's cache with bounded offline evidence fixtures."""
    reader = LiveEvidence()
    run, jobs = pair_snapshot(plan, source)
    base = f"repos/uibcdf/molsysmt/actions/runs/{run['id']}"
    reader.cache[base] = json.dumps(run).encode()
    reader.cache[base + f"/attempts/{run['run_attempt']}/jobs?per_page=100"] = json.dumps(jobs).encode()
    for package in ("molsysviewer", "molsysmt"):
        distributions = []
        for file in plan[package]["files"]:
            release, index = registry_snapshot(package, plan[package]["version"], file)
            distributions.extend(release["distributions"])
            channel = "uibcdf/label/staging" if source == "staging" else "uibcdf"
            reader.cache[f"https://conda.anaconda.org/{channel}/{file['subdir']}/repodata.json"] = index
        reader.cache[f"https://api.anaconda.org/release/uibcdf/{package}/{plan[package]['version']}"] = {
            "distributions": distributions
        }
    artifacts = []
    for platform in PLATFORMS:
        for python in PYTHONS:
            payload, artifact = archive_snapshot(environment_snapshot(plan, platform, source), run, platform, python)
            artifact.update(id=1000 + len(artifacts), name=f"conda-{source}-{platform}-py{python}")
            artifacts.append(artifact)
            reader.cache[f"repos/uibcdf/molsysmt/actions/artifacts/{artifact['id']}/zip"] = payload
    reader.cache[base + "/artifacts?per_page=100"] = json.dumps(
        {"total_count": len(artifacts), "artifacts": artifacts}
    ).encode()
    return reader


def test_staging_pass_never_clears_public_or_hosted_gates(candidate):
    checkout, plan, path = candidate
    reader = recorded_pair(plan, "staging")
    del plan["public_conda"]
    del plan["hosted_e2e"]
    path.write_text(json.dumps(plan))
    context = CandidateEvidence(path, checkout, reader=reader)
    steps = {step.name: step for step in STEPS}
    assert _run(steps["conda"], context)[0] == "PASS"
    assert _run(steps["public_conda"], context)[0] == "BLOCKED"
    assert _run(steps["hosted_e2e"], context)[0] == "BLOCKED"


@pytest.mark.parametrize("source", ["staging", "public"])
def test_pair_checks_all_environment_artifacts_and_registry_bindings(candidate, source):
    checkout, plan, path = candidate
    path.write_text(json.dumps(plan))
    reader = recorded_pair(plan, source)
    context = CandidateEvidence(path, checkout, reader=reader)
    step = "conda" if source == "staging" else "public_conda"
    assert context.evaluate(step)[0] == "PASS"
    url = "https://api.anaconda.org/release/uibcdf/molsysviewer/1.0.0"
    reader.cache[url]["distributions"][0]["sha256"] = "f" * 64
    assert context.evaluate(step)[0] == "FAIL"


@pytest.mark.parametrize(
    "field,value",
    [
        ("head_sha", "d" * 40),
        ("id", 999),
        ("run_attempt", 2),
        ("conclusion", "failure"),
        ("path", ".github/workflows/CI.yaml"),
    ],
)
def test_rejects_other_or_failed_pair_runs(candidate, field, value):
    _, plan, _ = candidate
    run, jobs = pair_snapshot(plan, "staging")
    run[field] = value
    with pytest.raises(InvalidEvidence):
        check_pair_run(plan, "staging", run, jobs)


@pytest.mark.parametrize("change", ["missing", "duplicate", "failed", "skipped-science", "other-attempt", "incomplete"])
def test_rejects_incomplete_or_unqualified_matrix(candidate, change):
    _, plan, _ = candidate
    run, jobs = pair_snapshot(plan, "staging")
    if change == "missing":
        jobs["jobs"].pop()
        jobs["total_count"] -= 1
    elif change == "duplicate":
        jobs["jobs"][1] = copy.deepcopy(jobs["jobs"][0])
    elif change == "failed":
        jobs["jobs"][0]["conclusion"] = "failure"
    elif change == "skipped-science":
        jobs["jobs"][0]["steps"][0]["conclusion"] = "skipped"
    elif change == "other-attempt":
        jobs["jobs"][0]["run_attempt"] = 2
    else:
        jobs["total_count"] += 1
    with pytest.raises(InvalidEvidence):
        check_pair_run(plan, "staging", run, jobs)


@pytest.mark.parametrize("change", ["hash", "channel", "filename", "duplicate", "unhashed", "no-explicit"])
def test_environment_inventory_cannot_substitute_another_package(candidate, change):
    _, plan, _ = candidate
    platform = PLATFORMS[0]
    text = environment_snapshot(plan, platform, "staging")
    if change == "hash":
        text = text.replace("c" * 32, "d" * 32)
    elif change == "channel":
        text = text.replace("/label/staging", "")
    elif change == "filename":
        text = text.replace("py_2", "py_7")
    elif change == "duplicate":
        text += "\n" + text.splitlines()[1]
    elif change == "unhashed":
        text = text.replace("#" + "c" * 32, "")
    else:
        text = text.replace("@EXPLICIT", "")
    md5s = {("molsysviewer", "noarch"): "c" * 32, ("molsysmt", platform): "c" * 32}
    with pytest.raises(InvalidEvidence):
        check_environment(text, plan, platform, "staging", md5s)


@pytest.mark.parametrize("change", ["hash", "run", "old-attempt", "wrong-file"])
def test_environment_archive_is_bound_to_the_github_artifact(candidate, change):
    _, plan, _ = candidate
    run, _ = pair_snapshot(plan, "staging")
    payload, artifact = archive_snapshot(
        environment_snapshot(plan, PLATFORMS[0], "staging"), run, PLATFORMS[0], PYTHONS[0]
    )
    if change == "hash":
        artifact["digest"] = "sha256:" + "f" * 64
    elif change == "run":
        artifact["workflow_run"]["id"] = 999
    elif change == "old-attempt":
        artifact["created_at"] = "2026-09-30T10:00:00Z"
    else:
        payload, artifact = archive_snapshot("unexpected", run, "win-64", "3.14")
    with pytest.raises(InvalidEvidence):
        read_environment_archive(payload, artifact, run, PLATFORMS[0], PYTHONS[0])


def test_registry_binds_md5_and_sha256_not_only_the_filename(candidate):
    _, plan, _ = candidate
    file = plan["molsysviewer"]["files"][0]
    release, index = registry_snapshot("molsysviewer", "1.0.0", file)
    assert check_registry(release, index, "molsysviewer", "1.0.0", file, "main") == "c" * 32
    index["packages"][file["filename"]]["md5"] = "e" * 32
    with pytest.raises(InvalidEvidence, match="MD5 differ"):
        check_registry(release, index, "molsysviewer", "1.0.0", file, "main")


@pytest.mark.parametrize("label", ["staging", "main"])
@pytest.mark.parametrize("change", ["build", "build-number", "boolean-build-number", "label", "missing-index"])
def test_installed_registry_bindings_survive_shared_verifier_adoption(candidate, label, change):
    _, plan, _ = candidate
    file = plan["molsysviewer"]["files"][0]
    release, index = registry_snapshot("molsysviewer", "1.0.0", file)
    record = index["packages"][file["filename"]]
    if change == "build":
        record["build"] = "py_7"
    elif change == "build-number":
        record["build_number"] = 7
    elif change == "boolean-build-number":
        record["build_number"] = True
    elif change == "label":
        release["distributions"][0]["labels"] = ["staging" if label == "main" else "main"]
    else:
        del index["packages"][file["filename"]]
    error = InvalidEvidence if change in ("build", "build-number", "boolean-build-number") else MissingEvidence
    with pytest.raises(error):
        check_registry(release, index, "molsysviewer", "1.0.0", file, label)


def test_candidate_checkout_cannot_differ_or_be_dirty(candidate):
    checkout, plan, path = candidate
    reader = recorded_pair(plan, "staging")
    path.write_text(json.dumps(plan))
    (checkout / "uncommitted").write_text("unreviewed")
    assert CandidateEvidence(path, checkout, reader=reader).evaluate("conda") == (
        "FAIL",
        "Viewer candidate checkout is dirty; freeze the candidate first",
    )
    (checkout / "uncommitted").unlink()
    plan["molsysviewer"]["commit"] = "e" * 40
    path.write_text(json.dumps(plan))
    assert CandidateEvidence(path, checkout, reader=reader).evaluate("conda")[0] == "FAIL"


def test_installed_viewer_version_must_match_the_candidate(candidate):
    checkout, plan, path = candidate
    path.write_text(json.dumps(plan))
    context = CandidateEvidence(path, checkout, reader=recorded_pair(plan, "staging"), reported_version="0.23.4")
    assert context.evaluate("conda") == ("FAIL", "Viewer package version differs from candidate")


def test_pre_1_0_exception_is_never_a_pass_or_a_1_0_waiver(candidate, capsys):
    checkout, plan, path = candidate
    plan["molsysviewer"]["version"] = "0.24.0"
    plan["molsysviewer"]["files"][0]["filename"] = "molsysviewer-0.24.0-py_2.tar.bz2"
    del plan["hosted_e2e"]
    plan["exceptions"] = [
        {
            "step": "hosted_e2e",
            "version": "0.24.0",
            "commit": plan["molsysviewer"]["commit"],
            "issue": "uibcdf/molsysviewer#103",
            "approved_by": "named maintainer",
            "reason": "bounded review",
        }
    ]
    path.write_text(json.dumps(plan))
    context = CandidateEvidence(path, checkout, pre_release=True)
    state, detail = context.evaluate("hosted_e2e")
    assert state == "EXCEPTION"
    step = next(item for item in STEPS if item.name == "hosted_e2e")
    assert _summarize([(step, state, detail)], pre_release=True) == 2
    output = capsys.readouterr().out
    assert "0 passed" in output and "1 exceptions" in output
    assert "RELEASE NOT CLEARED" in output
    assert CandidateEvidence(path, checkout).evaluate("hosted_e2e")[0] == "FAIL"
    plan["molsysviewer"]["version"] = "1.0.0"
    plan["molsysviewer"]["files"][0]["filename"] = "molsysviewer-1.0.0-py_2.tar.bz2"
    plan["exceptions"][0]["version"] = "1.0.0"
    path.write_text(json.dumps(plan))
    assert CandidateEvidence(path, checkout, pre_release=True).evaluate("hosted_e2e")[0] == "FAIL"
    assert CandidateEvidence(path, checkout).evaluate("hosted_e2e")[0] == "FAIL"


def test_exception_cannot_hide_contradictory_evidence(candidate):
    checkout, plan, path = candidate
    plan["molsysviewer"]["version"] = "0.24.0"
    plan["molsysviewer"]["files"][0]["filename"] = "molsysviewer-0.24.0-py_2.tar.bz2"
    plan["exceptions"] = [
        {
            "step": "conda",
            "version": "0.24.0",
            "commit": plan["molsysviewer"]["commit"],
            "issue": "uibcdf/molsysviewer#103",
            "approved_by": "named maintainer",
            "reason": "bounded review",
        }
    ]
    path.write_text(json.dumps(plan))
    reader = recorded_pair(plan, "staging")
    base = "repos/uibcdf/molsysmt/actions/runs/101"
    run = json.loads(reader.cache[base])
    run["conclusion"] = "failure"
    reader.cache[base] = json.dumps(run).encode()
    assert CandidateEvidence(path, checkout, pre_release=True, reader=reader).evaluate("conda")[0] == "FAIL"


@pytest.mark.parametrize("change", ["expired", "missing", "ambiguous", "bad-digest"])
def test_pair_conclusion_cannot_replace_environment_artifacts(candidate, change):
    checkout, plan, path = candidate
    path.write_text(json.dumps(plan))
    reader = recorded_pair(plan, "staging")
    key = "repos/uibcdf/molsysmt/actions/runs/101/artifacts?per_page=100"
    inventory = json.loads(reader.cache[key])
    if change == "expired":
        inventory["artifacts"][0]["expired"] = True
    elif change == "missing":
        inventory["artifacts"].pop(0)
        inventory["total_count"] -= 1
    elif change == "ambiguous":
        inventory["artifacts"].append(inventory["artifacts"][0].copy())
        inventory["total_count"] += 1
    else:
        inventory["artifacts"][0]["digest"] = "sha256:" + "e" * 64
    reader.cache[key] = json.dumps(inventory).encode()
    result = CandidateEvidence(path, checkout, reader=reader).evaluate("conda")
    assert result[0] == ("BLOCKED" if change in ("expired", "missing") else "FAIL")


@pytest.mark.parametrize("mode", ["partial", "pre-release"])
def test_diagnostic_success_does_not_claim_complete_1_0_clearance(mode, capsys):
    step = STEPS[0]
    assert _summarize([(step, "PASS", "")], partial=mode == "partial", pre_release=mode == "pre-release") == 0
    output = capsys.readouterr().out
    assert "Every gate step passed" not in output
    assert "complete release gate was not run" in output or "strict 1.0 release is not cleared" in output


@pytest.mark.parametrize("change", ["schema", "version", "commit", "build", "files", "filename", "digest", "run"])
def test_invalid_or_ambiguous_candidate_plan_is_rejected_before_acquisition(candidate, change):
    _, plan, _ = candidate
    viewer = plan["molsysviewer"]
    if change == "schema":
        plan["schema"] = "unknown"
    elif change == "version":
        viewer["version"] = "1.0.0+dirty"
    elif change == "commit":
        viewer["commit"] = "abcdef"
    elif change == "build":
        viewer["build_number"] = True
    elif change == "files":
        plan["molsysmt"]["files"].pop()
    elif change == "filename":
        viewer["files"][0]["filename"] = "../molsysviewer-1.0.0-py_2.tar.bz2"
    elif change == "digest":
        viewer["files"][0]["sha256"] = "abc"
    else:
        plan["conda"]["id"] = True
    with pytest.raises(InvalidEvidence):
        validate_plan(plan)


def test_hosted_core_is_independent_of_a_successful_remote_job(candidate):
    checkout, plan, path = candidate
    path.write_text(json.dumps(plan))
    reader = LiveEvidence()
    expected = plan["hosted_e2e"]
    base = f"repos/uibcdf/molsysviewer/actions/runs/{expected['id']}"
    run = {
        "id": expected["id"],
        "run_attempt": 1,
        "head_sha": plan["molsysviewer"]["commit"],
        "repository": {"full_name": "uibcdf/molsysviewer"},
        "path": ".github/workflows/CI_e2e.yaml",
        "status": "completed",
        "conclusion": "success",
    }
    jobs = {
        "total_count": 1,
        "jobs": [
            {
                "name": "e2e",
                "run_id": run["id"],
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "success",
                "steps": [{"name": "Run core E2E tests", "conclusion": "success"}],
            }
        ],
    }
    reader.cache[base] = json.dumps(run).encode()
    job_path = base + "/attempts/1/jobs?per_page=100"
    reader.cache[job_path] = json.dumps(jobs).encode()
    context = CandidateEvidence(path, checkout, reader=reader)
    assert context.evaluate("hosted_e2e")[0] == "PASS"
    jobs["jobs"][0]["steps"][0]["conclusion"] = "skipped"
    jobs["jobs"][0]["steps"].append({"name": "Run remote preview E2E diagnostics", "conclusion": "success"})
    reader.cache[job_path] = json.dumps(jobs).encode()
    assert context.evaluate("hosted_e2e")[0] == "FAIL"
    run["head_sha"] = "e" * 40
    with pytest.raises(InvalidEvidence, match="commit differs"):
        check_run(run, expected, "uibcdf/molsysviewer", ".github/workflows/CI_e2e.yaml", plan["molsysviewer"]["commit"])


@pytest.mark.parametrize(
    "change,expected",
    [
        ("none", "PASS"),
        ("control-success", "PASS"),
        ("control-failure", "FAIL"),
        ("unknown-skip", "FAIL"),
        ("core-job-skipped", "FAIL"),
        ("core-step-skipped", "FAIL"),
        ("duplicate-control", "FAIL"),
        ("other-attempt", "FAIL"),
        ("incomplete", "FAIL"),
    ],
)
def test_hosted_core_allows_only_inactive_backlog_control(candidate, change, expected):
    checkout, plan, path = candidate
    path.write_text(json.dumps(plan))
    identity = plan["hosted_e2e"]
    run, _ = pair_snapshot(plan, "staging")
    run.update(
        id=identity["id"],
        head_sha=plan["molsysviewer"]["commit"],
        repository={"full_name": "uibcdf/molsysviewer"},
        path=".github/workflows/CI_e2e.yaml",
    )
    core = {
        "name": "Core E2E",
        "run_id": identity["id"],
        "run_attempt": identity["attempt"],
        "status": "completed",
        "conclusion": "success",
        "steps": [{"name": "Run core E2E tests", "conclusion": "success"}],
    }
    control = dict(core, name="Check skipped-commit backlog", conclusion="skipped", steps=[])
    jobs = {"total_count": 2, "jobs": [core, control]}
    if change == "control-success":
        control["conclusion"] = "success"
    elif change == "control-failure":
        control["conclusion"] = "failure"
    elif change == "unknown-skip":
        control["name"] = "Other validation"
    elif change == "core-job-skipped":
        core["conclusion"] = "skipped"
    elif change == "core-step-skipped":
        core["steps"][0]["conclusion"] = "skipped"
    elif change == "duplicate-control":
        jobs["jobs"].append(dict(control))
        jobs["total_count"] += 1
    elif change == "other-attempt":
        control["run_attempt"] += 1
    elif change == "incomplete":
        jobs["total_count"] += 1
    reader = LiveEvidence()
    base = f"repos/uibcdf/molsysviewer/actions/runs/{identity['id']}"
    reader.cache[base] = json.dumps(run).encode()
    reader.cache[base + f"/attempts/{identity['attempt']}/jobs?per_page=100"] = json.dumps(jobs).encode()
    assert CandidateEvidence(path, checkout, reader=reader).evaluate("hosted_e2e")[0] == expected


@pytest.mark.parametrize("selection", ["does-not-exist", "conda,", "conda,conda"])
def test_partial_selection_cannot_succeed_without_running_any_gate(selection):
    result = subprocess.run(
        [sys.executable, str(ROOT / "devtools/release_gate.py"), "--only", selection],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "distinct existing steps" in result.stderr
