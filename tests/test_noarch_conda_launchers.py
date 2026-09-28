"""Pin the Conda console entry points and their installed-package release gates."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "devtools/conda-build/verify_noarch_launchers.py"

spec = importlib.util.spec_from_file_location("verify_noarch_launchers", SCRIPT)
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_noarch_recipe_declares_every_project_script():
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["scripts"]
    recipe = (ROOT / "devtools/conda-build/meta.yaml").read_text(encoding="utf-8")
    build = recipe.split("\nbuild:\n", 1)[1].split("\nrequirements:\n", 1)[0]
    entries = yaml.safe_load("build:\n" + build)["build"]["entry_points"]

    assert set(entries) == {f"{name} = {target}" for name, target in scripts.items()}
    assert len(entries) == len(scripts)
    assert set(verifier.COMMANDS) == set(scripts)


@pytest.mark.parametrize("label", ["staging", "main"])
def test_installed_record_requires_exact_channel_and_digest(label):
    version, build_number, sha256 = "0.24.0", 3, "a" * 64
    filename = f"molsysviewer-{version}-py_{build_number}.tar.bz2"
    record = {
        "name": "molsysviewer",
        "version": version,
        "build": f"py_{build_number}",
        "subdir": "noarch",
        "sha256": sha256,
        "url": f"{verifier.CHANNELS[label]}/{filename}",
    }

    verifier.check_record(record, version=version, build_number=build_number, sha256=sha256, label=label)
    with pytest.raises(ValueError, match="Installed digest mismatch"):
        verifier.check_record(record, version=version, build_number=build_number, sha256="b" * 64, label=label)
    with pytest.raises(ValueError, match="Wrong package URL"):
        other = "main" if label == "staging" else "staging"
        verifier.check_record(record, version=version, build_number=build_number, sha256=sha256, label=other)


@pytest.mark.parametrize(
    ("workflow", "label", "channel_spec"),
    [
        ("verify_staged_noarch_launchers.yaml", "staging", "uibcdf/label/staging::molsysviewer="),
        ("verify_public_conda_package.yaml", "main", "uibcdf::molsysviewer="),
    ],
)
def test_windows_release_workflows_check_installed_commands(workflow, label, channel_spec):
    jobs = yaml.safe_load((ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8"))["jobs"]
    job = jobs["windows-launchers"]
    assert job["runs-on"].startswith("windows-")
    setup = next(step for step in job["steps"] if step.get("name", "").startswith("Install"))
    assert channel_spec in setup["with"]["create-args"]
    check = job["steps"][-1]["run"]
    assert "verify_noarch_launchers.py" in check
    assert f"--label {label}" in check
    assert all(option in check for option in ("--prefix", "--version", "--build-number", "--sha256"))
