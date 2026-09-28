#!/usr/bin/env python3
"""Recover CI skipped on direct pushes after the last complete green lane.

Each lane keeps its own watermark. Only a successful run that executed all of
its required steps can clear skipped commits. Missing history or API evidence
causes the scheduled lane to run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

SKIP_MARKER = re.compile(
    r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]"
    r"|^skip-checks:\s*true\s*$",
    re.IGNORECASE | re.MULTILINE,
)
PYTHON_VERSIONS = ("3.11", "3.12", "3.13")
WORKFLOWS = {"ci": "CI.yaml", "e2e": "CI_e2e.yaml"}


def api_json(path: str, token: str) -> dict:
    request = Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "molsysviewer-ci-backlog",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], text=True, capture_output=True, check=False)


def is_ancestor(commit: str, head: str) -> bool:
    return git("merge-base", "--is-ancestor", commit, head).returncode == 0


def step_passed(job: dict, name: str) -> bool:
    return any(step["name"] == name and step["conclusion"] == "success" for step in job.get("steps", []))


def lane_passed(repository: str, run_id: int, token: str, lane: str) -> bool:
    jobs = api_json(f"/repos/{repository}/actions/runs/{run_id}/jobs?per_page=100", token)["jobs"]
    successful = {job["name"]: job for job in jobs if job["conclusion"] == "success"}
    if lane == "e2e":
        job = successful.get("Core E2E")
        return job is not None and step_passed(job, "Run core E2E tests")

    for os_name in ("ubuntu-latest", "macos-15"):
        for version in PYTHON_VERSIONS:
            job = successful.get(f"Test on {os_name}, Python {version}")
            if job is None or not step_passed(job, "Run tests"):
                return False
            if os_name == "ubuntu-latest" and version == "3.13":
                if not step_passed(job, "JS unit tests (Node)"):
                    return False
    qt = successful.get("Qt pipeline completes (Xvfb, software WebGL)")
    return qt is not None and all(
        step_passed(qt, name)
        for name in (
            "Qt transport round-trip in a real Qt process",
            "The structure finishes loading through WebGL",
        )
    )


def last_full_success(repository: str, head: str, token: str, lane: str) -> str | None:
    workflow = WORKFLOWS[lane]
    for page in range(1, 4):
        runs = api_json(
            f"/repos/{repository}/actions/workflows/{workflow}/runs"
            f"?branch=main&status=success&per_page=100&page={page}",
            token,
        )["workflow_runs"]
        for run in runs:
            if run["event"] not in {"push", "schedule", "workflow_dispatch"}:
                continue
            commit = run["head_sha"]
            if is_ancestor(commit, head) and lane_passed(repository, run["id"], token, lane):
                return commit
        if len(runs) < 100:
            break
    return None


def skipped_commits_after(anchor: str, head: str) -> list[str]:
    revision = f"{anchor}..{head}" if anchor else head
    result = git("log", "-z", "--format=%H%x00%B", revision)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git log failed")
    fields = result.stdout.split("\x00")
    if fields[-1] != "":
        raise RuntimeError("incomplete git log output")
    return [fields[index] for index in range(0, len(fields) - 1, 2) if SKIP_MARKER.search(fields[index + 1])]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", choices=WORKFLOWS, required=True)
    lane = parser.parse_args().lane
    repository = os.environ["GITHUB_REPOSITORY"]
    head = os.environ["GITHUB_SHA"]
    token = os.environ["GITHUB_TOKEN"]
    try:
        anchor = last_full_success(repository, head, token, lane)
        skipped = skipped_commits_after(anchor or "", head)
        run_full = anchor is None or bool(skipped)
        reason = (
            "no successful executed full lane"
            if anchor is None
            else f"{len(skipped)} skipped commit(s) since full lane {anchor}"
        )
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        anchor = None
        skipped = []
        run_full = True
        reason = f"cannot establish a clean backlog ({exc}); running full lane"

    print(f"{lane} recovery: {'run' if run_full else 'skip'}; {reason}")
    if skipped:
        print(f"Skipped commits pending: {len(skipped)}")
        print("Most recent skipped commits:", ", ".join(skipped[:5]))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"run_full={str(run_full).lower()}\n")
            stream.write(f"anchor={anchor or ''}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
