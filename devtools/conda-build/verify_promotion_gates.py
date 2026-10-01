"""Require current installed-pair and exact Windows evidence before promotion.

This is a read-only workflow gate, not the complete release qualification.
The pair checks share the local release gate's matrix semantics (#103).
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "promotion_release_evidence", Path(__file__).parents[1] / "release_evidence.py"
)
assert _SPEC is not None and _SPEC.loader is not None
evidence = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(evidence)

WINDOWS_WORKFLOW = ".github/workflows/verify_staged_noarch_launchers.yaml"
WINDOWS_STEP = "Verify installed record and commands outside the checkout"


def windows_title(version, build_number, sha256):
    return f"Viewer {version} build {build_number} | Windows launchers | sha256 {sha256}"


def verify(
    *,
    viewer_commit,
    version,
    build_number,
    sha256,
    pair_run_id,
    molsysmt_commit,
    molsysmt_version,
    molsysmt_build_number,
    windows_run_id,
    reader=None,
):
    """Check authoritative runs and all jobs of their current attempts."""
    for commit in (viewer_commit, molsysmt_commit):
        evidence.require(
            isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit), "candidate requires a full commit SHA"
        )
    for item in (version, molsysmt_version):
        evidence.require(
            isinstance(item, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", item),
            "candidate version must be stable X.Y.Z",
        )
    for number in (build_number, molsysmt_build_number):
        evidence.require(type(number) is int and number >= 0, "invalid candidate build number")
    for number in (pair_run_id, windows_run_id):
        evidence.require(type(number) is int and number > 0, "invalid gate run ID")
    evidence.require(
        isinstance(sha256, str) and re.fullmatch(r"[0-9a-f]{64}", sha256), "candidate requires a SHA-256 digest"
    )
    reader = reader or evidence.LiveEvidence()

    def acquire(repository, run_id):
        base = f"repos/{repository}/actions/runs/{run_id}"
        run = reader.github(base)
        attempt = run.get("run_attempt")
        evidence.require(type(attempt) is int and attempt > 0, "invalid gate run attempt")
        expected = {"id": run_id, "attempt": attempt}
        jobs = reader.github(base + f"/attempts/{attempt}/jobs?per_page=100")
        evidence.require(run.get("event") == "workflow_dispatch", "gate must be an explicit candidate run")
        return run, jobs, expected

    pair, pair_jobs, expected = acquire("uibcdf/molsysmt", pair_run_id)
    plan = {
        "conda": expected,
        "molsysviewer": {"commit": viewer_commit, "version": version, "build_number": build_number},
        "molsysmt": {"commit": molsysmt_commit, "version": molsysmt_version, "build_number": molsysmt_build_number},
    }
    evidence.check_pair_run(plan, "staging", pair, pair_jobs)

    windows, windows_jobs, expected = acquire("uibcdf/molsysviewer", windows_run_id)
    evidence.check_run(windows, expected, "uibcdf/molsysviewer", WINDOWS_WORKFLOW, viewer_commit)
    evidence.require(
        windows.get("display_title") == windows_title(version, build_number, sha256),
        "Windows launcher version, build or SHA-256 differs",
    )
    jobs = evidence.check_jobs(windows_jobs, expected["id"], expected["attempt"])
    evidence.require(
        len(jobs) == 1 and jobs[0].get("name") == "windows-launchers", "Windows launcher job is absent or ambiguous"
    )
    for required in ("Validate candidate checkout", "Install the exact staged Conda package", WINDOWS_STEP):
        matches = [step for step in jobs[0].get("steps", []) if step.get("name") == required]
        evidence.require(
            len(matches) == 1 and matches[0].get("conclusion") == "success", f"Windows gate did not execute {required}"
        )
    return f"PASS: installed-pair run {pair_run_id} and Windows launcher run {windows_run_id}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("viewer-commit", "version", "sha256", "molsysmt-commit", "molsysmt-version"):
        parser.add_argument("--" + flag, required=True)
    for flag in ("build-number", "pair-run-id", "molsysmt-build-number", "windows-run-id"):
        parser.add_argument("--" + flag, required=True, type=int)
    try:
        print(verify(**vars(parser.parse_args())))
    except (evidence.InvalidEvidence, evidence.MissingEvidence) as error:
        parser.exit(1, f"Promotion blocked: {error}\n")


if __name__ == "__main__":
    main()
