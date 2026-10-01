"""Keep hosted test selection and evidence intact when using compact output."""

import re
import shlex
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RECEPTOR_VERSION = "1.2.0"


@pytest.mark.parametrize("name", ["test_env", "test_source_pair_py314", "development_env"])
def test_test_environments_pin_the_reviewed_published_receptor(name):
    environment = yaml.safe_load((ROOT / "devtools/conda-envs" / f"{name}.yaml").read_text())
    pins = [item for item in environment["dependencies"] if isinstance(item, str) and "pytest-receptor" in item]
    assert pins == [f"pytest-receptor =={RECEPTOR_VERSION}"]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert f"pytest-receptor=={RECEPTOR_VERSION}" in project["project"]["optional-dependencies"]["dev"]
    assert not any("pytest-receptor" in item for item in project["project"]["dependencies"])


@pytest.mark.parametrize("filename", ["CI.yaml", "ci-python-314-source-pair.yaml"])
def test_every_hosted_pytest_command_selects_ci_and_an_executable_rerun(filename):
    workflow = yaml.load((ROOT / ".github/workflows" / filename).read_text(), Loader=yaml.BaseLoader)
    commands = []
    for job in workflow["jobs"].values():
        job_commands = []
        for step in job["steps"]:
            for line in step.get("run", "").splitlines():
                if line.lstrip().startswith("#") or not re.search(r"(?:^|\s)pytest(?:\s|$)", line):
                    continue
                tokens = shlex.split(line)
                if "pytest" in tokens:
                    commands.append(tokens)
                    job_commands.append(tokens)
        if job_commands:
            version_step = next(
                step for step in job["steps"] if step.get("name") == "Record published pytest tool versions"
            )
            assert f"assert version('pytest-receptor') == '{RECEPTOR_VERSION}'" in version_step["run"]
    assert len(commands) == 3
    for tokens in commands:
        assert tokens[tokens.index("pytest") - 2 : tokens.index("pytest")] == ["python", "-m"]
        assert "--receptor=ci" in tokens
        assert tokens[tokens.index("-o") + 1] == "receptor_rerun_command=python -m pytest"
        assert not any(token.startswith(("--tb=no", "--tb=line", "--receptor-max")) for token in tokens)
    if filename == "CI.yaml":
        main = next(tokens for tokens in commands if "--junitxml=junit.xml" in tokens)
        assert {"--cov-config=.coveragerc", "--cov=molsysviewer", "--cov-report=xml"} <= set(main)
        assert "-k" not in main and "--ignore" not in main
        assert {tokens[tokens.index("-k") + 1] for tokens in commands if "-k" in tokens} == {
            "qt_live_model_smoke_real_window",
            "full_render_gpu",
        }
    else:
        assert any("tests/" in tokens for tokens in commands)
        installed = next(tokens for tokens in commands if "--import-mode=importlib" in tokens)
        assert "molsysviewer-source/tests/integration/test_molsysmt_integration.py" in installed
        assert any(
            "molsysmt-source/tests/basic/test_get_form.py::test_bundled_path_is_detected_and_converted_on_native_platform"
            in tokens
            for tokens in commands
        )
