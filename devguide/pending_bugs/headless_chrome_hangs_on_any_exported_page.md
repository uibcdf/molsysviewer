---
summary: Headless Chrome hangs rendering any exported page on this machine, failing three screenshot tests.
issue: uibcdf/molsysviewer#77
status: open
opened: 2026-09-04
closed:
severity: low
verification: reproduced
area: [testing, export, tooling]
guard:
normative:
blocked_by: []
supersedes: []
---

# Three screenshot tests time out, and it is not the code

**Found:** 2026-09-04, during `uibcdf/molsysviewer#75` phase E2. Severity is low because
nothing in the library is wrong; it is recorded because the three failures sit in a
otherwise-green suite and the next person will suspect the code, as I did.

## What happens

The three colour tests of `tests/test_exported_page_opens_from_disk.py` fail with
`subprocess.TimeoutExpired` after 300 s: headless Chrome never finishes rendering the
exported page.

## Why it is not the change that surfaced it

Phase E2 rebuilt `viewer.js`, which made the bundle the obvious suspect. **It is not, and
that was checked rather than argued:** stashing every uncommitted change and running the
test on the previous commit reproduces the failure. The Playwright e2e suite that loads an
exported page passes with the new bundle, the 272 JS unit tests pass, and `tsc --noEmit` is
clean.

## What was ruled out, measured

| suspicion | result |
| --- | --- |
| Chrome is broken | **no** — a trivial page dumps its DOM and exits 0 |
| the exported page is malformed | **no** — 7.4 MB, well-formed |
| structure size | **no** — 22 atoms hangs exactly like 3,983 |
| stray browsers | **no** — killed, still hangs |
| a bound port | **no** — fresh ports, same result |
| the *previous* bundle | **also hangs** |

Chrome writes nothing to stderr. It simply never finishes, under `--screenshot` and under
`--dump-dom` alike.

## The environmental lead

`/` is at **92%**, `/tmp` holds **62 GB**, and about 43 GB of that is eight
`molsysmt-conda-render-*` directories of 5.4 GB each — unrelated to this repository.
Swiftshader compiles shaders to a disk cache, and hanging with no error is what a browser
that cannot write looks like.

Those directories were **not deleted**: they are MolSysMT's, not this work's, and clearing
43 GB of somebody else's build output is their call. If they are stale, removing them and
re-running the three tests is the cheapest next step.

## Exposure

CI runs single-process on a clean runner and is not exposed. The rest of the suite is green
at 1,699 passed, 4 skipped.
