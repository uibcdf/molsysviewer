"""Regression guards for the Python-wheel/runtime release contract."""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from validate_python_wheel_runtime import (  # noqa: E402
    embedded_runtime_version,
    validate_source,
    validate_wheel,
)


def _bundle(version: str) -> bytes:
    return f'const runtimeVersion = true ? "{version}" : "";\n'.encode()


def _wheel(path: Path, package_version: str, runtime_version: str) -> Path:
    with ZipFile(path, "w") as archive:
        archive.writestr(
            f"molsysviewer-{package_version}.dist-info/METADATA",
            f"Metadata-Version: 2.3\nName: molsysviewer\nVersion: {package_version}\n",
        )
        archive.writestr("molsysviewer/viewer.js", _bundle(runtime_version))
    return path


def test_source_rejects_a_previous_release_runtime(tmp_path):
    runtime = tmp_path / "molsysviewer" / "viewer.js"
    runtime.parent.mkdir()
    runtime.write_bytes(_bundle("0.23.0"))

    with pytest.raises(ValueError, match="embeds '0.23.0', expected release '0.23.4'"):
        validate_source(tmp_path, "0.23.4")


def test_wheel_rejects_a_runtime_that_disagrees_with_its_metadata(tmp_path):
    wheel = _wheel(tmp_path / "molsysviewer.whl", "0.23.4", "0.23.0")

    with pytest.raises(ValueError, match="embeds '0.23.0'.*declares '0.23.4'"):
        validate_wheel(wheel, "0.23.4")


def test_wheel_rejects_a_wrong_metadata_version_even_with_a_matching_runtime(tmp_path):
    wheel = _wheel(tmp_path / "molsysviewer.whl", "0.23.0", "0.23.0")

    with pytest.raises(ValueError, match="METADATA declares '0.23.0'"):
        validate_wheel(wheel, "0.23.4")


def test_wheel_accepts_only_the_matching_package_and_runtime(tmp_path):
    wheel = _wheel(tmp_path / "molsysviewer.whl", "0.23.4", "0.23.4")

    validate_wheel(wheel, "0.23.4")


def test_uninspectable_runtime_fails_closed():
    with pytest.raises(ValueError, match="exactly one compiled runtimeVersion assignment"):
        embedded_runtime_version(b'const otherVersion = "0.23.4";')
