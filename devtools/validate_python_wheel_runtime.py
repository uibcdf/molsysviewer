"""Check that a release wheel contains the runtime built for its Python version.

Run on the unmodified candidate source before tagging, then on a wheel built
from that same commit. Conda and npm rebuild the runtime separately and cannot
certify the ordinary Python wheel route.
"""

from __future__ import annotations

import argparse
import re
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ASSIGNMENT = re.compile(r'\bconst\s+runtimeVersion\s*=\s*true\s*\?\s*"([^"\\]+)"\s*:\s*""\s*;')


def embedded_runtime_version(bundle: bytes) -> str:
    """Return the actual version operand used by the compiled runtime check."""

    source = bundle.decode("utf-8")
    versions = RUNTIME_ASSIGNMENT.findall(source)
    if len(versions) != 1:
        raise ValueError(
            "Expected exactly one compiled runtimeVersion assignment in viewer.js; "
            "the build output changed or the version is not inspectable"
        )
    return versions[0]


def validate_source(root: Path, expected_version: str) -> None:
    """Reject a release source tree whose tracked runtime is from another version."""

    runtime = root / "molsysviewer" / "viewer.js"
    actual = embedded_runtime_version(runtime.read_bytes())
    if actual != expected_version:
        raise ValueError(f"Source viewer.js embeds {actual!r}, expected release {expected_version!r}")


def validate_wheel(wheel: Path, expected_version: str) -> None:
    """Reject a wheel whose metadata and packaged runtime disagree."""

    with ZipFile(wheel) as archive:
        members = archive.namelist()
        metadata_files = [name for name in members if re.fullmatch(r"molsysviewer-[^/]+\.dist-info/METADATA", name)]
        if len(metadata_files) != 1:
            raise ValueError("Expected exactly one MolSysViewer METADATA record in the wheel")
        metadata = Parser().parsestr(archive.read(metadata_files[0]).decode("utf-8"))
        package_version = metadata.get("Version")
        if package_version != expected_version:
            raise ValueError(f"Wheel METADATA declares {package_version!r}, expected {expected_version!r}")
        runtime_path = "molsysviewer/viewer.js"
        if members.count(runtime_path) != 1:
            raise ValueError("Expected exactly one packaged molsysviewer/viewer.js")
        runtime_version = embedded_runtime_version(archive.read(runtime_path))
        if runtime_version != package_version:
            raise ValueError(f"Wheel viewer.js embeds {runtime_version!r}, but METADATA declares {package_version!r}")


def main() -> int:
    """Validate the intended release coordinate against source and wheel bytes."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args()

    try:
        validate_source(args.source_root, args.expected_version)
        if args.wheel is not None:
            validate_wheel(args.wheel, args.expected_version)
    except (OSError, ValueError) as exc:
        print(f"Python wheel runtime contract: FAIL — {exc}")
        return 1
    scope = "source and wheel" if args.wheel is not None else "source"
    print(f"Python wheel runtime contract: PASS ({scope}, {args.expected_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
