#!/usr/bin/env python3
"""Validate release citation metadata and its derived public surfaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONCEPT_DOI = "10.5281/zenodo.18072956"
REPOSITORY_URL = "https://github.com/uibcdf/molsysviewer"
PROJECT_TITLE = "MolSysViewer"
VERSION_TEXT = r"\d+\.\d+\.\d+(?:-rc\.\d+)?"
VERSION_RE = re.compile(rf"^{VERSION_TEXT}$")

PUBLIC_SURFACES = (
    "README.md",
    "docs/index.ipynb",
    "docs/content/about/citation.md",
    "docs/_static/bibtex/software.bib",
    "docs/index.AGENTS.md",
)
FOREIGN_OR_VERSION_DOIS = (
    "10.5281/zenodo.8092688",  # MolSysMT 0.8.1, not MolSysViewer
    "10.5281/zenodo.18072957",  # MolSysViewer 0.7.0 version DOI
)


def _cff_scalar(text: str, key: str) -> str:
    match = re.search(
        rf"^{re.escape(key)}:\s*[\"']?([^\n\"']+)", text, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def _cff_creators(text: str) -> set[tuple[str, str]]:
    creators: set[tuple[str, str]] = set()
    for block in re.split(r"^\s+- family-names:\s*", text, flags=re.MULTILINE)[1:]:
        family = block.splitlines()[0].strip()
        given_match = re.search(r"^\s+given-names:\s*(.+)$", block, re.MULTILINE)
        orcid_match = re.search(r"^\s+orcid:\s*[\"']?([^\n\"']+)", block, re.MULTILINE)
        if given_match and orcid_match:
            orcid = orcid_match.group(1).removeprefix("https://orcid.org/")
            creators.add((f"{family}, {given_match.group(1).strip()}", orcid))
    return creators


def _zenodo_creators(payload: dict) -> set[tuple[str, str]]:
    return {
        (
            str(creator.get("name", "")),
            str(creator.get("orcid", "")).removeprefix("https://orcid.org/"),
        )
        for creator in payload.get("creators", [])
    }


def validate_repository(
    repo: Path = ROOT, expected_version: str | None = None
) -> list[str]:
    """Return every citation-policy violation found below *repo*."""

    errors: list[str] = []
    try:
        cff_text = (repo / "CITATION.cff").read_text(encoding="utf-8")
    except OSError as exc:
        return [f"CITATION.cff cannot be read: {exc}"]
    try:
        zenodo = json.loads((repo / ".zenodo.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f".zenodo.json cannot be parsed: {exc}"]

    title = _cff_scalar(cff_text, "title")
    kind = _cff_scalar(cff_text, "type")
    version = _cff_scalar(cff_text, "version")
    released = _cff_scalar(cff_text, "date-released")
    doi = _cff_scalar(cff_text, "doi")
    repository = _cff_scalar(cff_text, "url")
    license_name = _cff_scalar(cff_text, "license")

    if title != PROJECT_TITLE:
        errors.append(f"CITATION.cff title must be {PROJECT_TITLE!r}")
    if kind != "software":
        errors.append("CITATION.cff type must be 'software'")
    if not VERSION_RE.fullmatch(version):
        errors.append("CITATION.cff version must use X.Y.Z or X.Y.Z-rc.N")
    if expected_version is not None and version != expected_version:
        errors.append(
            f"CITATION.cff version {version!r} does not match expected "
            f"{expected_version!r}"
        )
    try:
        date.fromisoformat(released)
    except ValueError:
        errors.append("CITATION.cff date-released must use YYYY-MM-DD")
    if doi != CONCEPT_DOI:
        errors.append(f"CITATION.cff must use concept DOI {CONCEPT_DOI}")
    if repository.rstrip("/").lower() != REPOSITORY_URL.lower():
        errors.append(f"CITATION.cff url must be {REPOSITORY_URL}")
    if license_name.lower() != "mit":
        errors.append("CITATION.cff license must be MIT")

    if zenodo.get("title") != PROJECT_TITLE:
        errors.append(f".zenodo.json title must be {PROJECT_TITLE!r}")
    if zenodo.get("upload_type") != "software":
        errors.append(".zenodo.json upload_type must be 'software'")
    if str(zenodo.get("license", "")).lower() != "mit":
        errors.append(".zenodo.json license must be the string 'mit'")
    if "version" in zenodo or "publication_date" in zenodo:
        errors.append(
            ".zenodo.json must leave version and publication_date to the GitHub Release"
        )
    if _cff_creators(cff_text) != _zenodo_creators(zenodo):
        errors.append("CITATION.cff and .zenodo.json creators/ORCIDs disagree")

    surfaces: dict[str, str] = {}
    for relative in PUBLIC_SURFACES:
        path = repo / relative
        if not path.is_file():
            errors.append(f"missing citation surface: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        surfaces[relative] = text
        if CONCEPT_DOI not in text:
            errors.append(f"{relative} does not name concept DOI {CONCEPT_DOI}")
        for forbidden in FOREIGN_OR_VERSION_DOIS:
            if forbidden in text:
                errors.append(f"{relative} freezes foreign or version DOI {forbidden}")

    index_text = surfaces.get("docs/index.ipynb", "")
    citation_text = surfaces.get("docs/content/about/citation.md", "")
    bibtex_text = surfaces.get("docs/_static/bibtex/software.bib", "")
    if f"release-{version}-white.svg" not in index_text:
        errors.append("docs/index.ipynb release badge does not match CITATION.cff")
    for relative, text in (
        ("docs/index.ipynb", index_text),
        ("docs/content/about/citation.md", citation_text),
    ):
        if f"Version {version}" not in text:
            errors.append(f"{relative} software citation does not match {version}")
        if f"({released[:4]})" not in text:
            errors.append(f"{relative} software citation does not match release year")
    if not re.search(
        rf"^\s*version = \{{{re.escape(version)}\}},$", bibtex_text, re.MULTILINE
    ):
        errors.append("software.bib version does not match CITATION.cff")
    if not re.search(
        rf"^\s*year = \{{{re.escape(released[:4])}\}},$", bibtex_text, re.MULTILINE
    ):
        errors.append("software.bib year does not match CITATION.cff")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--expected-version")
    args = parser.parse_args()

    errors = validate_repository(args.repo_root.resolve(), args.expected_version)
    if errors:
        print("Citation metadata: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Citation metadata: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
