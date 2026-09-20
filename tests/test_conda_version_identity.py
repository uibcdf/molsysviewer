"""Guarding exact version identity in the MolSysViewer Conda package."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FREEZER = ROOT / "devtools" / "conda-build" / "freeze_project_version.py"


def _freezer_module():
    spec = importlib.util.spec_from_file_location("freeze_project_version", FREEZER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_freezer_writes_one_exact_version_source(tmp_path):
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    package = tmp_path / "molsysviewer"
    package.mkdir()

    _freezer_module().freeze_project_version(tmp_path, "0.23.1")

    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.23.1"' in pyproject
    assert 'dynamic = ["version"]' not in pyproject
    assert "[tool.versioningit" not in pyproject
    assert (package / "_version.py").read_text(encoding="utf-8") == (
        '__version__ = "0.23.1"\n'
    )


def test_freezer_rejects_an_untrusted_version(tmp_path):
    with pytest.raises(ValueError, match="Invalid package version"):
        _freezer_module().freeze_project_version(tmp_path, '0.23.1"; echo unsafe')


def test_conda_build_freezes_version_before_generating_assets():
    build_script = (ROOT / "devtools" / "conda-build" / "build.sh").read_text(
        encoding="utf-8"
    )
    freeze = build_script.index("freeze_project_version.py")
    javascript = build_script.index("npm run build")
    install = build_script.index("pip install")
    assert freeze < javascript < install

    recipe = (ROOT / "devtools" / "conda-build" / "meta.yaml").read_text(
        encoding="utf-8"
    )
    assert "md.version('molsysviewer') == expected" in recipe
    assert "molsysviewer.__version__ == expected" in recipe
