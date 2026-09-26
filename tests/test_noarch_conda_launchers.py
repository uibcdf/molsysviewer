"""Guard the staged Conda launchers that must exist on Windows."""

from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "devtools/conda-build/verify_noarch_launchers.py"
WORKFLOW = ROOT / ".github/workflows/verify_staged_noarch_launchers.yaml"
DIGEST = "a" * 64

spec = importlib.util.spec_from_file_location("verify_noarch_launchers", SCRIPT)
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def _installed_record(prefix: Path) -> None:
    metadata = prefix / "conda-meta"
    metadata.mkdir()
    record = {
        "name": "molsysviewer",
        "version": "0.24.0",
        "build": "py_3",
        "subdir": "noarch",
        "sha256": DIGEST,
        "url": f"{verifier.STAGING_CHANNEL}/molsysviewer-0.24.0-py_3.tar.bz2",
    }
    (metadata / "molsysviewer-0.24.0-py_3.json").write_text(json.dumps(record), encoding="utf-8")


def test_noarch_recipe_declares_every_project_script():
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["scripts"]
    recipe = (ROOT / "devtools/conda-build/meta.yaml").read_text(encoding="utf-8")
    build = recipe.split("\nbuild:\n", 1)[1].split("\nrequirements:\n", 1)[0]
    entries = yaml.safe_load("build:\n" + build)["build"]["entry_points"]

    assert len(entries) == len(scripts)
    assert set(entries) == {f"{name} = {target}" for name, target in scripts.items()}


def test_exact_staged_package_requires_every_installed_launcher(tmp_path, monkeypatch):
    _installed_record(tmp_path)
    monkeypatch.setattr(verifier.sys, "prefix", str(tmp_path))
    monkeypatch.setattr(verifier.importlib.metadata, "version", lambda _name: "0.24.0")
    available = {
        name: str(tmp_path / "Scripts" / f"{name}.exe") for name in verifier.COMMANDS if name != "molsysviewer-qt"
    }
    monkeypatch.setattr(verifier.shutil, "which", available.get)
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *_args, **_kwargs: verifier.subprocess.CompletedProcess([], 0, "help", ""),
    )

    with pytest.raises(ValueError, match="Missing installed launcher: molsysviewer-qt"):
        verifier.verify(tmp_path, "0.24.0", 3, DIGEST)


def test_exact_staged_package_runs_all_three_launchers(tmp_path, monkeypatch):
    _installed_record(tmp_path)
    monkeypatch.setattr(verifier.sys, "prefix", str(tmp_path))
    monkeypatch.setattr(verifier.importlib.metadata, "version", lambda _name: "0.24.0")
    monkeypatch.setattr(
        verifier.shutil,
        "which",
        lambda name: str(tmp_path / "Scripts" / f"{name}.exe"),
    )
    calls: list[list[str]] = []

    def run(args, **_kwargs):
        calls.append(args)
        return verifier.subprocess.CompletedProcess(args, 0, "help", "")

    monkeypatch.setattr(verifier.subprocess, "run", run)
    verifier.verify(tmp_path, "0.24.0", 3, DIGEST)

    assert len(calls) == 3
    assert all(args[-1] == "--help" for args in calls)
    assert {Path(args[0]).stem for args in calls} == set(verifier.COMMANDS)


def test_windows_workflow_installs_an_exact_staged_build():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["windows-launchers"]
    assert job["runs-on"] == "windows-latest"
    setup = next(step for step in job["steps"] if step.get("name", "").startswith("Install"))
    assert "uibcdf/label/staging::molsysviewer=" in setup["with"]["create-args"]
    assert "verify_noarch_launchers.py" in job["steps"][-1]["run"]
