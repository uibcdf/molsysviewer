"""The development source handoff includes real notebooks and browser workflows."""

import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_exact_source_pair_executes_all_notebooks_and_core_browser_suites():
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    for event in ("push", "pull_request"):
        assert "docs/**" in workflow["on"][event]["paths"]
    steps = workflow["jobs"]["source-pair"]["steps"]
    audit = next(step for step in steps if "--installed-source" in step.get("run", ""))
    kernel = next(step for step in steps if step.get("id") == "notebook-kernel")
    browser = next(step for step in steps if step.get("run") == "npm run test:e2e:core")
    notebooks = next(step for step in steps if "python docs/execute_notebooks.py" in step.get("run", ""))
    assert steps.index(audit) < steps.index(kernel) < steps.index(browser) < steps.index(notebooks)
    assert kernel["run"].startswith("python -m ipykernel install --sys-prefix --name python3 ")
    assert browser["if"] == "runner.os == 'Linux'"
    assert browser["env"]["PW_CHROMIUM_BIN"] == "/usr/bin/google-chrome"
    assert browser["working-directory"] == "molsysviewer-source/molsysviewer/js"
    assert notebooks["working-directory"] == "molsysviewer-source"
    assert notebooks["run"] == "python docs/execute_notebooks.py -q -n 4 -r -f docs/content"
    assert "always()" in notebooks["if"] and "steps.notebook-kernel.outcome == 'success'" in notebooks["if"]
    assert "E2E_ALLOW_SKIP" not in str(steps)
    logs = next(step for step in steps if step.get("uses") == "actions/upload-artifact@v4")
    assert "failure()" in logs["if"]
    assert "molsysviewer-source/docs/content/**/*.nbconvert.log" in logs["with"]["path"]
    environment = yaml.safe_load((ROOT / "devtools/conda-envs/test_source_pair_py314.yaml").read_text(encoding="utf-8"))
    assert {"nbconvert", "ipykernel"} <= set(environment["dependencies"])


def test_candidate_versions_are_bound_before_source_installation():
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["molsysmt_version"]["default"] == "0.23.0"
    steps = workflow["jobs"]["source-pair"]["steps"]
    provider_tag = next(step for step in steps if step["name"] == "Locally tag the exact MolSysMT candidate version")
    install = next(step for step in steps if step["name"] == "Install both exact source candidates")
    assert steps.index(provider_tag) < steps.index(install)
    assert provider_tag["working-directory"] == "molsysmt-source"
    assert 'git rev-list -n 1 "$EXPECTED_VERSION"' in provider_tag["run"]
    assert '= "$MOLSYSMT_SHA"' in provider_tag["run"]
    assert 'git tag "$EXPECTED_VERSION" HEAD' in provider_tag["run"]

    browser_workflow = yaml.load(
        (ROOT / ".github/workflows/CI_e2e.yaml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    steps = browser_workflow["jobs"]["e2e"]["steps"]
    tag = next(
        step for step in steps if step.get("name") == "Validate and locally tag the exact Viewer source candidate"
    )
    install = next(step for step in steps if step.get("name") == "Install package")
    assert steps.index(tag) < steps.index(install)
    assert tag["if"] == "github.event_name == 'workflow_dispatch' && inputs.use_staging"
    assert "validate_python_wheel_runtime.py" in tag["run"]
    assert 'git rev-list -n 1 "$EXPECTED_VERSION"' in tag["run"]
    assert '= "$GITHUB_SHA"' in tag["run"]


def test_temporary_candidate_tags_are_removed_after_installation():
    for name in ("CI.yaml", "CI_e2e.yaml", "ci-python-314-source-pair.yaml"):
        workflow = yaml.load((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        for job in workflow["jobs"].values():
            steps = job.get("steps", [])
            for create in (step for step in steps if step.get("id", "").endswith("-candidate-tag")):
                identifier = create["id"]
                cleanup = next(
                    step for step in steps if f"steps.{identifier}.outputs.created == 'true'" in step.get("if", "")
                )
                install = next(step for step in steps if "pip install" in step.get("run", ""))
                assert steps.index(create) < steps.index(install) < steps.index(cleanup)
                # Ownership is recorded only when this job creates the tag; a preexisting
                # public tag must not enter the cleanup branch.
                branch = create["run"].split("else\n", 1)[1]
                assert 'git tag "$EXPECTED_VERSION" HEAD' in branch
                assert 'echo "created=true" >> "$GITHUB_OUTPUT"' in branch
                assert 'echo "created=true"' not in create["run"].split("else\n", 1)[0]
                assert 'git rev-list -n 1 "$EXPECTED_VERSION"' in cleanup["run"]
                assert 'git tag -d "$EXPECTED_VERSION"' in cleanup["run"]
                assert cleanup.get("working-directory") == create.get("working-directory")
                if sys.platform != "win32":
                    syntax = subprocess.run(["bash", "-n"], input=cleanup["run"], text=True, capture_output=True)
                    assert syntax.returncode == 0, syntax.stderr


def test_automatic_source_pair_uses_the_prepared_runtime_version():
    """Push/PR installs must agree with the committed release-preparation runtime."""
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    plan = tomllib.loads((ROOT / "devtools/conda-build/release_plan.toml").read_text(encoding="utf-8"))
    expected = "${{ inputs.viewer_version || '" + plan["version"] + "' }}"
    steps = workflow["jobs"]["source-pair"]["steps"]
    tag = next(step for step in steps if step.get("id") == "viewer-candidate-tag")
    cleanup = next(step for step in steps if step["name"] == "Remove the temporary Viewer tag after installation")
    install = next(step for step in steps if step["name"] == "Install both exact source candidates")
    assert "if" not in tag, "automatic source builds must also bind the intended version"
    assert tag["env"]["EXPECTED_VERSION"] == cleanup["env"]["EXPECTED_VERSION"] == expected
    assert "validate_python_wheel_runtime.py" in tag["run"]
    assert steps.index(tag) < steps.index(install) < steps.index(cleanup)
