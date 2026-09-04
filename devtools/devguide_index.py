"""Rendering the queue indexes from the front matter that already describes each entry.

`DOCUMENT_POLICY`-style rule, and the reason this exists: a hand-written index of
documents that already describe themselves is two independent authoritative lists, and one
of them will be wrong. Ours was, this session — the proposals index still described four
documents as queue entries after they had been moved out, and it was corrected by hand.
That is the third or fourth hand-edit of these indexes in a week.

So the head of each README stays written — how to read the directory, what precedence it
carries, what it demands, all judgement — and the entry list is rendered between markers:

    <!-- generated: devguide_index -->
    ...
    <!-- /generated -->

Run:
    python devtools/devguide_index.py            # write
    python devtools/devguide_index.py --check    # fail if stale

Offline. `tests/test_reporting_protocol.py` runs `--check` in the suite.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVGUIDE = ROOT / "devguide"

BEGIN = "<!-- generated: devguide_index -->"
END = "<!-- /generated -->"

#: Which directories a README renders. A queue README shows its own entries; the
#: pre-1.0 index also shows what is deferred, because a reader asking "what is open"
#: needs to see the boundary rather than discover a second directory later.
INDEXES = {
    "pending_bugs/README.md": ("pending_bugs", "pending_bugs/post_1.0"),
    "pending_proposals/README.md": ("pending_proposals", "pending_proposals/post_1.0"),
}

#: Presentation order. `open` last of the open set on purpose: a reader scanning for
#: something to pick up wants the started and the stuck first.
STATUS_ORDER = ("active", "partial", "blocked", "open")

STATUS_HEADING = {
    "active": "Being worked on",
    "partial": "Partially done",
    "blocked": "Blocked",
    "open": "Open",
}


def _front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(
            f"{path.relative_to(ROOT)} has no front matter; see devguide/reporting_protocol.md"
        )
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _entries(queue: str) -> list[tuple[str, dict[str, str]]]:
    directory = DEVGUIDE / queue
    if not directory.is_dir():
        return []
    found = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        found.append((path.name, _front_matter(path)))
    return found


def _issue_link(reference: str) -> str:
    """`uibcdf/molsysviewer#34` becomes a link. The number is the stable identity."""
    repository, _, number = reference.partition("#")
    return f"[#{number}](https://github.com/{repository}/issues/{number})"


def _qualifiers(fields: dict[str, str]) -> str:
    parts = [fields[key] for key in ("severity", "verification") if fields.get(key)]
    return f" *({', '.join(parts)})*" if parts else ""


def _render(queues: tuple[str, ...], readme_directory: str) -> str:
    lines: list[str] = []
    for queue in queues:
        entries = _entries(queue)
        if not entries:
            continue
        deferred = queue.endswith("post_1.0")
        if deferred:
            lines += ["", f"### Deferred until after 1.0 ({len(entries)})", ""]
            prefix = "post_1.0/"
            for name, fields in sorted(entries, key=lambda item: item[0]):
                lines.append(
                    f"- [`{name}`]({prefix}{name}) — {_issue_link(fields['issue'])} — "
                    f"{fields['summary']}"
                )
            continue

        by_status: dict[str, list[tuple[str, dict[str, str]]]] = {}
        for name, fields in entries:
            by_status.setdefault(fields["status"], []).append((name, fields))
        for status in STATUS_ORDER:
            group = by_status.get(status)
            if not group:
                continue
            lines += ["", f"### {STATUS_HEADING[status]} ({len(group)})", ""]
            for name, fields in sorted(group, key=lambda item: item[0]):
                blocked_by = fields.get("blocked_by", "[]")
                waiting = f" — waiting on {blocked_by.strip('[]')}" if status == "blocked" and blocked_by != "[]" else ""
                lines.append(
                    f"- [`{name}`]({name}) — {_issue_link(fields['issue'])} — "
                    f"{fields['summary']}{_qualifiers(fields)}{waiting}"
                )
    return "\n".join(lines).strip("\n")


def _block(readme: Path, body: str) -> str:
    text = readme.read_text(encoding="utf-8")
    if BEGIN not in text:
        raise SystemExit(
            f"{readme.relative_to(ROOT)} has no {BEGIN} marker; add it where the entry "
            "list belongs, with {END} after it"
        )
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{BEGIN}\n\n{body}\n\n{END}{tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if a rendered index is out of date")
    arguments = parser.parse_args()

    stale = []
    for relative, queues in INDEXES.items():
        readme = DEVGUIDE / relative
        rendered = _block(readme, _render(queues, str(readme.parent)))
        if rendered == readme.read_text(encoding="utf-8"):
            continue
        if arguments.check:
            stale.append(relative)
        else:
            readme.write_text(rendered, encoding="utf-8")
            print(f"wrote devguide/{relative}")

    if stale:
        print("stale generated indexes: " + ", ".join(stale), file=sys.stderr)
        print("regenerate with `python devtools/devguide_index.py`", file=sys.stderr)
        return 1
    if arguments.check:
        print("generated indexes are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
