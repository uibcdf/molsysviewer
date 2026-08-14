#!/usr/bin/env python3
"""Verify that Zenodo archived one published GitHub Release."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://zenodo.org/api/records"


def _cff_scalar(path: Path, key: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}:\s*[\"']?([^\n\"']+)", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"CITATION.cff has no {key!r} field")
    return match.group(1).strip()


def validate_record(
    record: dict, version: str, concept_doi: str, repository: str
) -> list[str]:
    """Return violations for a record expected to archive *version*."""

    errors: list[str] = []
    metadata = record.get("metadata", {})
    if metadata.get("version") != version:
        errors.append(f"metadata.version is {metadata.get('version')!r}, expected {version!r}")
    if record.get("conceptdoi") != concept_doi:
        errors.append(f"concept DOI is {record.get('conceptdoi')!r}, expected {concept_doi!r}")
    if record.get("status") != "published":
        errors.append(f"record status is {record.get('status')!r}, expected 'published'")
    files = record.get("files", [])
    if not files:
        errors.append("record has no archived files")
    if record.get("doi") == concept_doi or not record.get("doi"):
        errors.append("record has no distinct version DOI")

    expected_repository = repository.rstrip("/").lower()
    related = {
        str(item.get("identifier", "")).rstrip("/").lower()
        for item in metadata.get("related_identifiers", [])
    }
    code_repository = str(
        metadata.get("custom", {}).get("code:codeRepository", "")
    ).rstrip("/").lower()
    if expected_repository not in related and code_repository != expected_repository:
        errors.append(f"record does not identify repository {expected_repository}")
    archive_suffix = f"-{version}.zip".lower()
    if files and not any(
        str(item.get("key", "")).lower().endswith(archive_suffix) for item in files
    ):
        errors.append(f"record has no archive ending in {archive_suffix}")
    return errors


def fetch_records(concept_record: str, version: str, timeout: float = 30.0) -> list[dict]:
    query = f'conceptrecid:{concept_record} AND metadata.version:"{version}"'
    url = f"{API}?{urlencode({'q': query, 'size': 10})}"
    request = Request(url, headers={"User-Agent": "molsysviewer-release-verifier/1"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return payload.get("hits", {}).get("hits", [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    cff = args.repo_root.resolve() / "CITATION.cff"
    concept_doi = _cff_scalar(cff, "doi")
    repository = _cff_scalar(cff, "url")
    concept_record = concept_doi.rsplit(".", 1)[-1]
    deadline = time.monotonic() + args.timeout
    last_error = "record not visible yet"

    while True:
        try:
            for record in fetch_records(concept_record, args.version):
                errors = validate_record(record, args.version, concept_doi, repository)
                if not errors:
                    print(
                        "Zenodo release: PASS — "
                        f"{args.version} -> {record['doi']} (concept {concept_doi})"
                    )
                    return 0
                last_error = "; ".join(errors)
        except Exception as exc:
            last_error = str(exc)
        if time.monotonic() >= deadline:
            print(f"Zenodo release: FAIL — {last_error}")
            return 1
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
