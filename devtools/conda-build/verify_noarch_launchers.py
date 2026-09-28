"""Verify one exact installed noarch package and its Windows console launchers."""

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
CHANNELS = {
    "staging": "https://conda.anaconda.org/uibcdf/label/staging/noarch",
    "main": "https://conda.anaconda.org/uibcdf/noarch",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_record(record: dict, *, version: str, build_number: int, sha256: str, label: str) -> None:
    """Require the installed file to be the exact candidate named by the release receipt."""
    _require(label in CHANNELS, "Invalid channel label")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", sha256)), "Invalid expected SHA-256")
    _require(
        bool(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version)),
        "Invalid version",
    )
    _require(build_number >= 0, "Invalid build number")
    filename = f"molsysviewer-{version}-py_{build_number}.tar.bz2"
    _require(record.get("name") == "molsysviewer", "Wrong package")
    _require(record.get("version") == version, "Wrong installed version")
    _require(record.get("build") == f"py_{build_number}", "Wrong installed build")
    _require(record.get("subdir") == "noarch", "Package is not noarch")
    _require(record.get("sha256") == sha256, "Installed digest mismatch")
    _require(record.get("url") == f"{CHANNELS[label]}/{filename}", "Wrong package URL")


def verify(prefix: Path, *, version: str, build_number: int, sha256: str, label: str) -> None:
    _require(sys.platform == "win32", "This check must run on Windows")
    _require(prefix.resolve() == Path(sys.prefix).resolve(), "Wrong environment prefix")
    record_path = prefix / "conda-meta" / f"molsysviewer-{version}-py_{build_number}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    check_record(record, version=version, build_number=build_number, sha256=sha256, label=label)
    _require(importlib.metadata.version("molsysviewer") == version, "Wrong import metadata")

    for name in COMMANDS:
        launcher = shutil.which(name)
        _require(launcher is not None, f"Missing installed launcher: {name}")
        path = Path(launcher).resolve()
        _require(path.is_relative_to(prefix.resolve()), f"Launcher outside installed environment: {name}")
        _require(path.suffix.lower() == ".exe", f"Windows executable missing: {name}")
        completed = subprocess.run(
            [str(path), "--help"], capture_output=True, check=False, text=True, timeout=30
        )
        _require(completed.returncode == 0, f"{name} --help failed: {completed.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build-number", required=True, type=int)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--label", choices=tuple(CHANNELS), required=True)
    args = parser.parse_args()
    verify(args.prefix, version=args.version, build_number=args.build_number, sha256=args.sha256, label=args.label)
    print(f"PASS: exact {args.label} noarch package and all three installed Windows launchers")


if __name__ == "__main__":
    main()
