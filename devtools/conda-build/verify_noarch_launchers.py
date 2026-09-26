"""Verify the exact staged noarch package and its installed Windows launchers."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMMANDS = ("molsysviewer", "molsysviewer-qt", "molsysviewer-server")
STAGING_CHANNEL = "https://conda.anaconda.org/uibcdf/label/staging/noarch"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(prefix: Path, version: str, build_number: int, sha256: str) -> None:
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", sha256)), "Invalid expected SHA-256")
    _require(
        bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)),
        "Invalid version",
    )
    _require(build_number >= 0, "Invalid build number")
    _require(prefix.resolve() == Path(sys.prefix).resolve(), "Wrong environment prefix")

    filename = f"molsysviewer-{version}-py_{build_number}.tar.bz2"
    record = json.loads(
        (prefix / "conda-meta" / f"molsysviewer-{version}-py_{build_number}.json").read_text(encoding="utf-8")
    )
    _require(record.get("name") == "molsysviewer", "Wrong package")
    _require(record.get("version") == version, "Wrong installed version")
    _require(record.get("build") == f"py_{build_number}", "Wrong installed build")
    _require(record.get("subdir") == "noarch", "Package is not noarch")
    _require(record.get("sha256") == sha256, "Installed digest mismatch")
    _require(record.get("url") == f"{STAGING_CHANNEL}/{filename}", "Wrong package URL")
    _require(importlib.metadata.version("molsysviewer") == version, "Wrong import metadata")

    for name in COMMANDS:
        launcher = shutil.which(name)
        _require(launcher is not None, f"Missing installed launcher: {name}")
        _require(
            Path(launcher).resolve().is_relative_to(prefix.resolve()),
            f"Launcher outside installed environment: {name}",
        )
        completed = subprocess.run(
            [launcher, "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
        _require(completed.returncode == 0, f"{name} --help failed: {completed.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build-number", required=True, type=int)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    verify(args.prefix, args.version, args.build_number, args.sha256)
    print("PASS: exact staged noarch package and all installed launchers")


if __name__ == "__main__":
    main()
