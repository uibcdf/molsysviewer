---
summary: Devguide issue synchronization truncates the board at 200 items.
issue: uibcdf/molsysviewer#261
status: resolved
opened: 2026-10-22
closed: 2026-10-22
severity: low
verification: reproduced
area: [tooling, devguide]
guard: tests/test_devguide_issue.py::test_board_keeps_older_issues_across_native_pages
normative:
blocked_by: []
supersedes: []
---

# Truncated board produces false missing-issue reports

## What

The final `devguide_issue.py sync --check` reports 17 older issues as absent.
Those issues exist; the source query only requests the latest 200 items.
The original failing output is retained in the cleanup evidence directory.

## How

Replace the fixed `gh issue list --limit 200` window with
`gh api --paginate --slurp` over the complete issues endpoint. REST includes
pull requests and lower-case states, so exclude PRs and normalize states while
preserving the existing label-only synchronization boundary.

The bounded fixture projects actual returned page positions, states, labels
and a PR marker without issue bodies. Receiving must retain #35 beyond the
first 200 items, keep closed #256 closed, preserve #259's labels and omit PRs.
An empty board still reports missing maintained issues instead of passing.

## Why

This is a reporting-tool defect, not a missing GitHub issue or viewer failure.
It was discovered while verifying the authorized #256/#260 cleanup.

## Resolution — 2026-10-22

The tool now reads all native REST pages with `gh api --paginate --slurp`,
excludes PRs and preserves uppercase state/label semantics. The selected guard
replays a bounded projection of the actual 100/100/59-item pages, retaining
old #35, closed #256, blocked #259 and the real #135 PR exclusion. A second
guard confirms that missing board evidence still reports disagreement.
Both checks pass. The live read-only full inventory reconciles all 31 queued
records before this report's archival; the 17 former missing-issue reports
were false positives. No issue body or state was changed by the check.

This administrative follow-up was discovered after the 3,224-pass core run
on `e4f8c7c5`; that run is not relabeled as testing this later tool change.
Only the owning tool and reporting/link guards are rerun. See
[cleanup receiving](../pre_documentation_cleanup_20261022.json).
