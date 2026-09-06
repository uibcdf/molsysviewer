---
summary: The three exported-page colour tests need an http origin, which command-line Chrome cannot give them here; Playwright can.
issue: uibcdf/molsysviewer#81
status: resolved
opened: 2026-09-05
closed: 2026-09-06
verification: measured
area: [testing, export, tooling]
guard: molsysviewer/js/tests/e2e/exported-page-colour.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Three tests in the wrong test suite

**Measured:** 2026-09-05, while resolving the symptom of
[`../archive/headless_chrome_hangs_on_any_exported_page.md`](headless_chrome_hangs_on_any_exported_page.md).

## What

The three colour tests of `tests/test_exported_page_opens_from_disk.py` skip on this
machine. The skip is honest — a canary probes the capability and names what is missing —
but a test that skips permanently checks nothing.

## Why they cannot just use `file://`

This is the part worth reading before touching them. `file://` fixes the symptom in 3.6 s
and **guts the test**: they read the host document's `data-theme` from inside the iframe,
which is a same-origin access, and `file://` gives every file an opaque origin. They would
pass and measure nothing. The local server is the object of the test.

## Why the TypeScript suite

| | |
| --- | ---: |
| command-line Chrome to `http://127.0.0.1` | hangs indefinitely |
| Playwright driving the same URL | **0.2 s** |

And three reasons beyond the one that forced it: `exported-page-framing.e2e.ts` and
`export-replay.e2e.ts` already open real exported pages; the Python bridge for *generating*
one already exists there (`spawnSync(PYTHON_BIN, [".../bridge.py"])`); and Playwright pins
its browser, where the system Chrome auto-updated to 149 and broke the navigation with
nobody deciding anything.

They would then run in the gate's `e2e` step rather than its `python` step, where an
unpinned browser can block a release.

## What stays, and why that is not laziness

The other seven use `file://`, work, and are a five-line `subprocess.run` against **the
browser the reader actually has**. That is a different question from the one Playwright
answers — an exported page is opened by whatever Chrome its recipient installed, not by a
pinned Chromium — and it is worth keeping asked. Migrating them would cost that and buy
nothing.

## What was refuted

**"Add the `playwright` Python package."** Not installed, pulls a second browser download
into the Python test environment, and the bridge already crosses the boundary in the
direction that works.

**"Migrate all ten for consistency."** Consistency is not the goal; the seven answer a
question the three do not.

## Acceptance criteria

1. The three assertions hold in the TypeScript suite over a real http origin.
2. Registered in `e2e-runner.ts` and `build:e2e:all`.
3. The Python file loses the three, `_canvas_colour`, the canary and its mark, and says
   where they went.
4. Mutation-verified: a runtime that ignores the host's colour fails them.

## Carry the sampling note across

The helper samples the **background** deliberately: under a software rasteriser the same
page measured three times gave 6186, 0 and 6172 lit pixels, so an assertion about the
molecule would be a flake generator.
