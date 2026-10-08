"""Keep npm publication bound to one automatic release event."""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "npm-publish.yaml"


def test_npm_publisher_has_only_one_automatic_trigger():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow[True]

    assert set(triggers) == {"push", "workflow_dispatch"}
    assert triggers["push"]["tags"] == ["*", "!archive/**"]
    manual_tag = triggers["workflow_dispatch"]["inputs"]["tag"]
    assert manual_tag["required"] is True
    assert "default" not in manual_tag


@pytest.mark.parametrize("initial_version", ["0.23.4", "0.24.0"])
def test_npm_version_injection_accepts_synced_and_stale_manifests(tmp_path, initial_version):
    """Run the actual publisher command; the synchronized case caught #176."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    step = next(item for item in workflow["jobs"]["publish"]["steps"] if item["name"] == "Inject version and repo info")
    line = next(line.strip() for line in step["run"].splitlines() if line.strip().startswith("npm version "))
    command = shlex.split(line)
    command = ["0.24.0" if part == "$CLEAN_VERSION" else part for part in command]
    assert "--no-git-tag-version" in command
    npm = shutil.which("npm")
    assert npm is not None, "The npm publication regression requires the real npm CLI"
    command[0] = npm
    manifest = json.loads((WORKFLOW.parents[2] / "molsysviewer/js/package.json").read_text(encoding="utf-8"))
    manifest["version"] = initial_version
    target = tmp_path / "package.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(target.read_text(encoding="utf-8"))["version"] == "0.24.0"


@pytest.mark.parametrize(
    ("tag", "accepted"),
    [("0.24.1", True), ("archive/pre-0.24.1-20261008", False), ("0.24.1rc1", False)],
)
def test_npm_refuses_non_release_identity_before_package_commands(tag, accepted):
    """Execute the early publisher guard, including an accidental archive dispatch."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["publish"]["steps"]
    guard = next(step for step in steps if step.get("name") == "Validate public release identity")
    assert steps.index(guard) < steps.index(next(step for step in steps if step["name"] == "Install latest npm"))
    assert steps.index(guard) < steps.index(next(step for step in steps if step["name"] == "Publish to npm"))
    assert guard["env"]["RELEASE_TAG"] == "${{ github.event.inputs.tag || github.ref_name }}"
    bash = shutil.which("bash")
    assert bash is not None
    result = subprocess.run(
        [bash, "-e", "-o", "pipefail", "-c", guard["run"]],
        env={**os.environ, "RELEASE_TAG": tag},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) is accepted, result.stdout + result.stderr
