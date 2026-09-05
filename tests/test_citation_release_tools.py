"""Regression tests for citation preparation and Zenodo verification."""

from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from prepare_release import prepare_release  # noqa: E402
from validate_citation import _cff_scalar, CONCEPT_DOI, validate_repository  # noqa: E402
from verify_zenodo_release import validate_record  # noqa: E402


def test_repository_citation_surfaces_agree():
    """Every surface must agree with CITATION.cff, which is the metadata authority.

    The expected version is read rather than written down. It used to be the literal
    "0.20.1", which passed for a year and then failed the first time it mattered: the
    release gate for 0.22.0 stopped on it, because `prepare_release.py` updates four
    surfaces and cannot update a test. A pin that must be bumped by hand at each release,
    with nothing saying so, is a trap that only springs during a release.

    Nothing is lost by deriving it. The contract this file exists for is that the BibTeX
    entry, the citation page, the docs badge and Zenodo all say what CITATION.cff says;
    a literal adds no check to that, only a second place to remember.
    `test_expected_version_mismatch_is_rejected` still proves the validator rejects a
    version that does not match.
    """
    declared = _cff_scalar((ROOT / "CITATION.cff").read_text(encoding="utf-8"), "version")
    assert declared, "CITATION.cff declares no version"

    assert validate_repository(ROOT, expected_version=declared) == []


def test_expected_version_mismatch_is_rejected():
    errors = validate_repository(ROOT, expected_version="9.9.9")
    assert any("does not match expected" in error for error in errors)


def test_prepare_release_updates_canonical_and_derived_surfaces(tmp_path):
    for relative in (
        "CITATION.cff",
        ".zenodo.json",
        "README.md",
        "docs/index.ipynb",
        "docs/index.AGENTS.md",
        "docs/content/about/citation.md",
        "docs/_static/bibtex/software.bib",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    prepare_release(tmp_path, "0.21.0", date(2026, 8, 14))

    assert validate_repository(tmp_path, expected_version="0.21.0") == []
    assert "release-0.21.0-white.svg" in (tmp_path / "docs/index.ipynb").read_text()


def test_prepare_release_accepts_the_documented_release_candidate_format(tmp_path):
    for relative in (
        "CITATION.cff",
        ".zenodo.json",
        "README.md",
        "docs/index.ipynb",
        "docs/index.AGENTS.md",
        "docs/content/about/citation.md",
        "docs/_static/bibtex/software.bib",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    prepare_release(tmp_path, "1.0.0-rc.1", date(2026, 8, 14))

    assert validate_repository(tmp_path, expected_version="1.0.0-rc.1") == []


def test_zenodo_record_requires_version_doi_archive_and_matching_tag():
    record = {
        "conceptdoi": CONCEPT_DOI,
        "doi": "10.5281/zenodo.99999999",
        "status": "published",
        "files": [{"key": "uibcdf/molsysviewer-0.20.1.zip"}],
        "metadata": {
            "version": "0.20.1",
            "custom": {
                "code:codeRepository": "https://github.com/uibcdf/molsysviewer"
            },
            "related_identifiers": [
                {
                    "identifier": "https://github.com/uibcdf/molsysviewer"
                }
            ],
        },
    }

    assert validate_record(
        record,
        "0.20.1",
        CONCEPT_DOI,
        "https://github.com/uibcdf/molsysviewer",
    ) == []
