"""Historical archive markers preserve source without changing release identity."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from versioningit import get_version

ROOT = Path(__file__).resolve().parents[1]


def test_archive_policy_caller_observes_slash_tags_unconditionally():
    workflow = yaml.load((ROOT / ".github/workflows/molsyssuite-policy.yml").read_text(), Loader=yaml.BaseLoader)
    assert workflow["on"]["push"]["tags"] == ["**"]
    job = workflow["jobs"]["policy"]
    assert job["uses"] == "uibcdf/molsyssuite/.github/workflows/check-python-repository.yaml@policy-v1.5.7"
    assert not job.get("if")


@pytest.mark.parametrize("tag", ["archive/pre-0.24.1-20261008", "archive/experiments/example"])
def test_archive_tags_do_not_change_the_real_git_derived_package_version(tmp_path, tag):
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")

    def git(*arguments):
        return subprocess.run(
            ["git", "-C", str(tmp_path), *arguments], check=True, capture_output=True, text=True, timeout=15
        )

    git("init", "-b", "main")
    git("add", "pyproject.toml")
    git("-c", "user.name=Archive guard", "-c", "user.email=archive-test@example.invalid", "commit", "-m", "Base")
    git("tag", "0.24.0")
    (tmp_path / "checkpoint.txt").write_text("Unreleased source checkpoint\n")
    git("add", "checkpoint.txt")
    git("-c", "user.name=Archive guard", "-c", "user.email=archive-test@example.invalid", "commit", "-m", "Checkpoint")
    before = get_version(tmp_path, fallback=False)
    git("tag", tag)
    assert get_version(tmp_path, fallback=False) == before
    assert before.startswith("0.24.0+1.")


@pytest.mark.parametrize("event", ["release", "workflow_dispatch"])
def test_conda_route_refuses_archive_before_any_publication(tmp_path, event):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "devtools/conda-build/release_route.py"),
            "--version",
            "archive/pre-0.24.1-20261008",
            "--event",
            event,
            "--github-output",
            str(tmp_path / "route-output"),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "release version must be canonical X.Y.Z" in result.stderr
    assert not (tmp_path / "route-output").exists()
