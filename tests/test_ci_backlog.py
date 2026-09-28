"""Guard full PR checks and recovery of deliberately skipped direct pushes."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.error import URLError

import yaml
from devtools import ci_backlog

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def test_skipped_commit_remains_due_until_a_full_run(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "commit", "--allow-empty", "-qm", "green full suite")
    anchor = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "commit", "--allow-empty", "-qm", "rapid iteration [skip ci]")
    skipped = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "commit", "--allow-empty", "-qm", "ordinary change")
    head = git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.chdir(tmp_path)

    assert ci_backlog.skipped_commits_after(anchor, head) == [skipped]
    assert ci_backlog.skipped_commits_after(head, head) == []
    assert ci_backlog.SKIP_MARKER.search("message\n\nskip-checks: true")


def test_only_executed_complete_lanes_clear_backlog(monkeypatch):
    def fake_api(path, _token):
        if "/runs?" in path:
            assert "status=success" not in path
            return {
                "workflow_runs": [
                    {"id": 3, "event": "push", "head_sha": "failed", "conclusion": "failure"},
                    {"id": 2, "event": "schedule", "head_sha": "probe", "conclusion": "success"},
                    {"id": 1, "event": "push", "head_sha": "green", "conclusion": "success"},
                ]
            }
        run_id = 2 if "/runs/2/" in path else 1
        jobs = []
        for os_name in ("ubuntu-latest", "macos-15"):
            for version in ci_backlog.PYTHON_VERSIONS:
                steps = [{"name": "Run tests", "conclusion": "success"}]
                if os_name == "ubuntu-latest" and version == "3.13":
                    steps.append(
                        {
                            "name": "JS unit tests (Node)",
                            "conclusion": "skipped" if run_id == 2 else "success",
                        }
                    )
                jobs.append(
                    {
                        "name": f"Test on {os_name}, Python {version}",
                        "conclusion": "success",
                        "steps": steps,
                    }
                )
        jobs.append(
            {
                "name": "Qt pipeline completes (Xvfb, software WebGL)",
                "conclusion": "success",
                "steps": [
                    {"name": name, "conclusion": "success"}
                    for name in (
                        "Qt transport round-trip in a real Qt process",
                        "The structure finishes loading through WebGL",
                    )
                ],
            }
        )
        jobs.append(
            {
                "name": "Core E2E",
                "conclusion": "success",
                "steps": [
                    {
                        "name": "Run core E2E tests",
                        "conclusion": "skipped" if run_id == 2 else "success",
                    }
                ],
            }
        )
        return {"jobs": jobs}

    monkeypatch.setattr(ci_backlog, "api_json", fake_api)
    monkeypatch.setattr(ci_backlog, "is_ancestor", lambda *_: True)
    assert ci_backlog.last_full_success("uibcdf/molsysviewer", "head", "token", "ci") == "green"
    assert ci_backlog.last_full_success("uibcdf/molsysviewer", "head", "token", "e2e") == "green"


def test_api_uncertainty_runs_the_full_lane(tmp_path, monkeypatch, capsys):
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_REPOSITORY", "uibcdf/molsysviewer")
    monkeypatch.setenv("GITHUB_SHA", "head")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr(ci_backlog, "last_full_success", lambda *_: (_ for _ in ()).throw(URLError("offline")))
    monkeypatch.setattr("sys.argv", ["ci_backlog.py", "--lane", "ci"])

    assert ci_backlog.main() == 0
    assert "running full lane" in capsys.readouterr().out
    assert "run_full=true" in output.read_text(encoding="utf-8")


def test_pr_gates_and_nightly_recovery_are_wired():
    workflows = ROOT / ".github/workflows"
    ci = yaml.load((workflows / "CI.yaml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    e2e = yaml.load((workflows / "CI_e2e.yaml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert "paths-ignore" not in ci["on"]["pull_request"]
    assert any(item.get("timezone") == "America/Mexico_City" for item in ci["on"]["schedule"])
    assert any(item.get("timezone") == "America/Mexico_City" for item in e2e["on"]["schedule"])
    assert "--lane ci" in ci["jobs"]["nightly-decision"]["steps"][1]["run"]
    assert "--lane e2e" in e2e["jobs"]["nightly-decision"]["steps"][1]["run"]
    assert ci["jobs"]["pr-gate"]["name"] == "PR full suite"
    assert set(ci["jobs"]["pr-gate"]["needs"]) == {"test", "qt-pipeline"}
    assert e2e["jobs"]["e2e"]["name"] == "Core E2E"
    for job in (ci["jobs"]["test"], ci["jobs"]["qt-pipeline"], e2e["jobs"]["e2e"]):
        assert "pull_request" not in job["if"]
        assert "run_full" in job["if"]
        assert "probe_backlog" in job["if"]
