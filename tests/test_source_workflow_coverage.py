"""The development source handoff includes real notebooks and browser workflows."""

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_source_recovery_matrix_keeps_complete_default_and_whitelisted_subsets():
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    option = workflow["on"]["workflow_dispatch"]["inputs"]["platform"]
    assert option["default"] == "all" and option["type"] == "choice"
    scope = workflow["on"]["workflow_dispatch"]["inputs"]["receiving_scope"]
    assert scope["default"] == "full" and scope["options"] == ["full", "diagnostics"]
    expression = workflow["jobs"]["source-pair"]["strategy"]["matrix"]["cfg"]
    prefix, suffix = "${{ fromJSON('", "')[inputs.platform || 'all'] }}"
    assert expression.startswith(prefix) and expression.endswith(suffix)
    matrices = json.loads(expression[len(prefix) : -len(suffix)])
    assert set(option["options"]) == set(matrices)
    platforms = ["ubuntu-latest", "macos-15", "windows-2025"]
    assert matrices["all"] == [{"os": name, "python-version": "3.14"} for name in platforms]
    for platform in platforms:
        assert matrices[platform] == [{"os": platform, "python-version": "3.14"}]
    steps = workflow["jobs"]["source-pair"]["steps"]
    assert steps[0]["name"] == "Validate source-recovery scope"
    assert steps[0]["env"] == {
        "SELECTED_PLATFORM": "${{ inputs.platform || 'all' }}",
        "SOURCE_RECEIVING": "${{ inputs.source_receiving || false }}",
        "PANDAS_VERSION": "${{ inputs.pandas_version || '2.3.3' }}",
        "RECEIVING_SCOPE": "${{ inputs.receiving_scope || 'full' }}",
        "ENCODER_DIAGNOSTICS": "${{ inputs.encoder_diagnostics || false }}",
    }


@pytest.mark.parametrize("platform", ["all", "ubuntu-latest", "macos-15", "windows-2025", "unknown"])
@pytest.mark.parametrize("receiving", [False, True])
@pytest.mark.parametrize("receiving_scope", ["full", "diagnostics", "unknown"])
def test_source_recovery_guard_executes_without_waiving_candidate_platforms(platform, receiving, receiving_scope):
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    script = workflow["jobs"]["source-pair"]["steps"][0]["run"]
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required to execute the workflow's actual scope guard")
    result = subprocess.run(
        [bash],
        input=script,
        text=True,
        capture_output=True,
        env=dict(
            os.environ,
            SELECTED_PLATFORM=platform,
            SOURCE_RECEIVING=str(receiving).lower(),
            PANDAS_VERSION="2.3.3",
            RECEIVING_SCOPE=receiving_scope,
        ),
    )
    accepted = platform != "unknown" and (platform == "all" or receiving)
    if receiving_scope != "full":
        accepted = receiving_scope == "diagnostics" and receiving and platform == "ubuntu-latest"
    assert result.returncode == (0 if accepted else 1), result.stdout + result.stderr


@pytest.mark.parametrize("platform", ["all", "ubuntu-latest", "macos-15", "windows-2025"])
@pytest.mark.parametrize("receiving", [False, True])
@pytest.mark.parametrize("scope", ["full", "diagnostics"])
def test_encoder_diagnostic_cannot_qualify_or_broaden_a_candidate(platform, receiving, scope):
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    steps = workflow["jobs"]["source-pair"]["steps"]
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required for the actual workflow guard")
    result = subprocess.run(
        [bash],
        input=steps[0]["run"],
        capture_output=True,
        text=True,
        env=dict(
            os.environ,
            SELECTED_PLATFORM=platform,
            SOURCE_RECEIVING=str(receiving).lower(),
            PANDAS_VERSION="3.1.0",
            RECEIVING_SCOPE=scope,
            ENCODER_DIAGNOSTICS="true",
        ),
    )
    assert (result.returncode == 0) is (platform == "windows-2025" and receiving and scope == "full")
    tests = next(step for step in steps if step.get("name") == "Run MolSysViewer Python tests")
    diagnostic, full = tests["run"].split("else", 1)
    assert "tests/test_movie_export.py" in diagnostic
    assert '-m "not qt_runtime" tests/' in full
    receipt = next(step for step in steps if step.get("name") == "Preserve native Movie encoder diagnostic logs")
    assert receipt["if"] == "always() && inputs.encoder_diagnostics == true"
    assert receipt["with"]["path"].endswith("/**/encoder.log")


@pytest.mark.parametrize(
    ("version", "accepted"),
    [
        ("2.3.3", True),
        ("3.1.0", True),
        ("latest", False),
        ("3.1", False),
        ("3.1.0 --override-channels", False),
        ("", False),
        ("3.1.0\n", False),
    ],
)
@pytest.mark.parametrize("implicit_errexit", [True, False])
def test_source_receiving_rejects_nonversion_pandas_inputs_before_provisioning(version, accepted, implicit_errexit):
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(), Loader=yaml.BaseLoader
    )
    guard = workflow["jobs"]["source-pair"]["steps"][0]
    script = guard["run"]
    if not implicit_errexit:
        # Validation must reject explicitly, including shells where errexit does
        # not terminate after a failed conditional command (hosted macOS #295).
        assert script.startswith("set -euo pipefail\n")
        script = script.replace("set -euo pipefail\n", "set -uo pipefail\n", 1)
    bash = shutil.which("bash")
    assert bash is not None, "The workflow guard regression requires Bash"
    result = subprocess.run(
        [bash],
        input=script,
        text=True,
        capture_output=True,
        env=dict(os.environ, SELECTED_PLATFORM="all", SOURCE_RECEIVING="true", PANDAS_VERSION=version),
    )
    assert (result.returncode == 0) is accepted, result.stdout + result.stderr
    if not accepted:
        assert result.returncode == 1
        assert "Platform scope:" not in result.stdout
        assert "pandas_version must be an exact numeric X.Y.Z version" in result.stdout


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
    assert browser["if"] == "runner.os == 'Linux' && inputs.receiving_scope != 'diagnostics'"
    assert browser["env"]["PW_CHROMIUM_BIN"] == "/usr/bin/google-chrome"
    assert browser["working-directory"] == "molsysviewer-source/molsysviewer/js"
    assert notebooks["working-directory"] == "molsysviewer-source"
    assert notebooks["run"] == "python docs/execute_notebooks.py -q -n 4 -r -f docs/content"
    assert "always()" in notebooks["if"] and "steps.notebook-kernel.outcome == 'success'" in notebooks["if"]
    assert "E2E_ALLOW_SKIP" not in str(steps)
    logs = next(step for step in steps if step.get("name") == "Preserve source-pair notebook failure logs")
    assert "failure()" in logs["if"]
    assert "molsysviewer-source/docs/content/**/*.nbconvert.log" in logs["with"]["path"]
    environment = yaml.safe_load((ROOT / "devtools/conda-envs/test_source_pair_py314.yaml").read_text(encoding="utf-8"))
    assert {"nbconvert", "ipykernel", "jupyterlab", "psutil"} <= set(environment["dependencies"])


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
    for name in ("CI.yaml", "CI_qt_experimental.yaml", "CI_e2e.yaml", "ci-python-314-source-pair.yaml"):
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
    """Explicit candidate installs use the prepared version; development rebuilds it."""
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    plan = tomllib.loads((ROOT / "devtools/conda-build/release_plan.toml").read_text(encoding="utf-8"))
    assert workflow["on"]["workflow_dispatch"]["inputs"]["viewer_version"]["default"] == plan["version"]
    for name in ("CI.yaml", "CI_e2e.yaml"):
        dispatch = yaml.load((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        assert dispatch["on"]["workflow_dispatch"]["inputs"]["viewer_version"]["default"] == plan["version"], name
    steps = workflow["jobs"]["source-pair"]["steps"]
    tag = next(step for step in steps if step.get("id") == "viewer-candidate-tag")
    cleanup = next(step for step in steps if step["name"] == "Remove the temporary Viewer tag after installation")
    install = next(step for step in steps if step["name"] == "Install both exact source candidates")
    assert tag["if"] == "github.event_name == 'workflow_dispatch' && inputs.source_receiving != true"
    assert tag["env"]["EXPECTED_VERSION"] == cleanup["env"]["EXPECTED_VERSION"] == "${{ inputs.viewer_version }}"
    assert "validate_python_wheel_runtime.py" in tag["run"]
    assert steps.index(tag) < steps.index(install) < steps.index(cleanup)


def test_development_runtime_is_installed_before_source_validation():
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    steps = workflow["jobs"]["source-pair"]["steps"]
    install = next(step for step in steps if step["name"] == "Install both exact source candidates")
    dependencies = next(step for step in steps if step["name"] == "Install JavaScript test dependencies")
    runtime = next(
        step for step in steps if step["name"] == "Synchronize the development runtime before source validation"
    )
    audit = next(
        step for step in steps if step["name"] == "Audit dependency routes and the installed exact source provider"
    )
    tests = next(step for step in steps if step["name"] == "Run MolSysViewer Python tests")
    assert (
        steps.index(install)
        < steps.index(dependencies)
        < steps.index(runtime)
        < steps.index(audit)
        < steps.index(tests)
    )
    assert runtime["if"] == "github.event_name != 'workflow_dispatch' || inputs.source_receiving == true"
    assert runtime["working-directory"] == "molsysviewer-source/molsysviewer/js"
    lines = runtime["run"].splitlines()
    assert lines.index("npm run build:runtime") < lines.index(
        "python -m pip install --no-deps --no-build-isolation ../.."
    )
    assert "git tag" not in runtime["run"] and "npm run build\n" not in runtime["run"]


def test_development_receiving_preserves_source_identity_and_original_test_results():
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci-python-314-source-pair.yaml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    option = workflow["on"]["workflow_dispatch"]["inputs"]["source_receiving"]
    assert option["type"] == "boolean" and option["default"] == "false"
    steps = workflow["jobs"]["source-pair"]["steps"]
    provider = next(step for step in steps if step.get("id") == "provider-candidate-tag")
    assert provider["if"] == "inputs.source_receiving != true"
    native_tests = next(step for step in steps if step.get("name") == "Run MolSysViewer Python tests")
    assert native_tests["if"] == "inputs.receiving_scope != 'diagnostics'"
    assert '--receptor=ci -m "not qt_runtime" tests/' in native_tests["run"]
    assert "--junitxml=source-receiving.xml" in native_tests["run"]
    receipt = next(step for step in steps if step.get("name") == "Preserve the original source-receiving JUnit")
    assert receipt["if"] == "always() && inputs.receiving_scope != 'diagnostics'"
    assert receipt["with"]["path"] == "molsysviewer-source/source-receiving.xml"
    assert "runner.os" in receipt["with"]["name"]
    diagnostic = next(
        step for step in steps if step.get("name") == "Preserve safe source-pair receiving diagnostic receipts"
    )
    assert diagnostic["if"] == "always() && inputs.receiving_scope == 'diagnostics'"
    assert diagnostic["with"]["path"].endswith("/**/command-result.json")
    assert "source-receiving.xml" not in diagnostic["with"]["path"]
