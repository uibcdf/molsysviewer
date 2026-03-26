#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


PACKAGES = ["shiboken6", "PySide6_Essentials", "PySide6_Addons"]


def pip_show_files(python_bin: str, package: str) -> tuple[dict, list[str]]:
    proc = subprocess.run(
        [python_bin, "-m", "pip", "show", "-f", package],
        check=True,
        capture_output=True,
        text=True,
    )
    meta: dict[str, str] = {}
    files: list[str] = []
    in_files = False
    for line in proc.stdout.splitlines():
        if in_files:
            stripped = line.strip()
            if stripped:
                files.append(stripped)
            continue
        if line == "Files:":
            in_files = True
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, files


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {}
    for package in PACKAGES:
        meta, files = pip_show_files(args.python_bin, package)
        files = sorted(files)
        summary[package] = {
            "name": meta.get("Name", package),
            "version": meta.get("Version", ""),
            "location": meta.get("Location", ""),
            "requires": [
                item.strip()
                for item in meta.get("Requires", "").split(",")
                if item.strip()
            ],
            "file_count": len(files),
        }
        base_name = package.lower()
        write_lines(output_dir / f"{base_name}.files.txt", files)
        write_lines(
            output_dir / f"{base_name}.runtime.txt",
            [
                item
                for item in files
                if item.startswith("PySide6/Qt/")
                or item.endswith(".so")
                or item.endswith(".so.6")
                or "libshiboken6" in item
                or "libpyside6" in item
            ],
        )

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
