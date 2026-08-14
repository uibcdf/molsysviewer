"""Checking that the issue board still agrees with the front matter.

The two records are maintained by different acts — editing a file, and clicking on GitHub
— so they will drift. Nothing in the suite can catch it: verifying an issue needs the
network and an authenticated `gh`, which is why `devguide/reporting_protocol.md` puts this
outside the test suite and outside the release gate's offline steps.

    python devtools/devguide_issue.py sync --check    # report drift, exit non-zero
    python devtools/devguide_issue.py sync            # apply the derived labels

**It only ever writes labels.** Opening and closing are done by hand, with the two
comments the protocol specifies, because those are the moments that need judgement: what
a reader outside the repository needs to know, and what the fix actually was. A script
that wrote them would write them badly.

The front matter is the source. This never reads state back into a document.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVGUIDE = ROOT / "devguide"

QUEUES = (
    "pending_bugs",
    "pending_bugs/post_1.0",
    "pending_proposals",
    "pending_proposals/post_1.0",
)

#: Labels derived from `status`. Everything else on the board is set by hand: `bug` and
#: `proposal` say what a thing is, and `needs-triage` is a human judgement about whether
#: an incoming report has been attended.
STATE_LABELS = {"in-progress", "blocked", "partial"}
LABEL_FOR_STATUS = {"active": "in-progress", "blocked": "blocked", "partial": "partial"}

CLOSED_STATUSES = {"resolved", "withdrawn", "superseded"}


def _gh(*arguments: str) -> str:
    result = subprocess.run(("gh",) + arguments, capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(arguments)} failed: "
                         f"{(result.stderr or result.stdout).strip()}")
    return result.stdout


def _front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"{path.relative_to(ROOT)} has no front matter")
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _documents() -> list[tuple[Path, dict[str, str]]]:
    found = []
    for queue in QUEUES:
        directory = DEVGUIDE / queue
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.name != "README.md":
                found.append((path, _front_matter(path)))
    return found


def _board() -> dict[int, dict]:
    payload = json.loads(_gh("issue", "list", "--repo", "uibcdf/molsysviewer",
                             "--state", "all", "--limit", "200",
                             "--json", "number,state,labels,milestone"))
    return {item["number"]: item for item in payload}


def sync(check: bool) -> int:
    board = _board()
    drift: list[str] = []
    to_apply: list[tuple[int, set[str], set[str]]] = []

    for path, fields in _documents():
        name = path.relative_to(DEVGUIDE)
        reference = fields.get("issue", "")
        repository, _, number = reference.partition("#")
        if repository != "uibcdf/molsysviewer" or not number.isdigit():
            drift.append(f"{name}: issue {reference!r} is not an issue of this repository")
            continue

        issue = board.get(int(number))
        if issue is None:
            drift.append(f"{name}: {reference} is not on the board")
            continue

        status = fields.get("status", "")
        # A queue entry is open by definition; the guard in the suite already refuses a
        # closed status here, so a closed *issue* means the two records disagree.
        if issue["state"] != "OPEN":
            drift.append(
                f"{name}: front matter says {status!r} and the issue is {issue['state']}. "
                "Either the document should be archived or the issue reopened"
            )
            continue

        labels = {label["name"] for label in issue["labels"]}
        expected = {LABEL_FOR_STATUS[status]} if status in LABEL_FOR_STATUS else set()
        actual = labels & STATE_LABELS
        if expected != actual:
            drift.append(
                f"{name}: status {status!r} wants "
                f"{sorted(expected) or 'no state label'}, board has "
                f"{sorted(actual) or 'none'}"
            )
            to_apply.append((int(number), expected - actual, actual - expected))

    if not drift:
        print(f"{len(_documents())} documents agree with the board")
        return 0

    for line in drift:
        print(f"  {line}")

    if check:
        print(f"\n{len(drift)} disagreement(s) between the front matter and the board.",
              file=sys.stderr)
        print("Fix the document or the issue, then run "
              "`python devtools/devguide_issue.py sync` for the derived labels.",
              file=sys.stderr)
        return 1

    for number, add, remove in to_apply:
        arguments = ["issue", "edit", str(number), "--repo", "uibcdf/molsysviewer"]
        for label in sorted(add):
            arguments += ["--add-label", label]
        for label in sorted(remove):
            arguments += ["--remove-label", label]
        _gh(*arguments)
        print(f"  #{number}: +{sorted(add) or '-'} -{sorted(remove) or '-'}")

    remaining = [line for line in drift if "state label" not in line and "wants" not in line]
    if remaining:
        print(f"\n{len(remaining)} disagreement(s) need a person, not a label.",
              file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    synchronise = subparsers.add_parser("sync", help="compare the board with the front matter")
    synchronise.add_argument("--check", action="store_true",
                             help="report drift and exit non-zero without changing anything")
    arguments = parser.parse_args()

    if arguments.command == "sync":
        return sync(arguments.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
