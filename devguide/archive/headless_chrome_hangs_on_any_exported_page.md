---
summary: Command-line headless Chrome never completes a navigation to http:// on this machine.
issue: uibcdf/molsysviewer#77
status: withdrawn
opened: 2026-09-04
closed: 2026-09-06
severity: low
verification: reproduced
area: [testing, export, tooling]
guard:
normative:
blocked_by: []
supersedes: []
---

# Command-line headless Chrome will not navigate to http here, and it is not the code

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


## Second pass — 2026-09-05 — the environmental lead was wrong, and the title is too

The 43 GB were deleted. **It still hangs.** Every hypothesis in the first pass is refuted
below, including the one it recommended acting on.

### What it is

**Command-line headless Chrome does not complete a navigation to `http://` on this
machine.** It has nothing to do with this project.

The measurement that settled it: the server records **no request at all**. Nothing is
served slowly; the request is never issued. `urllib` gets a 200 from the same server in the
same process a moment earlier.

| | |
| --- | ---: |
| `file://` + `--dump-dom` | 0.5 s |
| `http://127.0.0.1` + `--dump-dom` | **hangs** |
| `http://localhost` + `--dump-dom` | **hangs** |
| `file://` + `--screenshot` | 0.6 s |
| Playwright driving the same browser to the same http URL | **0.2 s** |

It reproduces with a **sixty-byte** HTML file. With `--timeout=20000` Chrome gives up after
20 s and dumps an empty document rather than fetching one.

### Everything the first pass suspected, and one thing it recommended

| suspicion | result |
| --- | --- |
| disk pressure / Swiftshader shader cache | **no** — 42 GB free and unchanged; Chrome writes **5.1 MB** to the profile in total, GPU caches included |
| Swiftshader | **no** — `--use-angle=swiftshader --screenshot` over `file://` takes 3.6 s and produces the image |
| the exported page (6.7 MB) | **no** — a 60-byte page hangs identically |
| the iframe | **no** — hangs without one |
| `msv.tools.preview` being single-threaded | **no** — a `ThreadingMixIn` server changes nothing |
| proxy resolution | **no** — `--no-proxy-server` changes nothing; system proxy is `none` |
| Chrome's background networking | **no** — `--disable-background-networking --disable-component-update` change nothing |
| `--virtual-time-budget` | **no** — hangs without the flag too |
| the browser version | **no** — Chrome 149 and Playwright's Chromium 143 both hang from the command line |

The first pass's own recommendation — *"if they are stale, removing them and re-running the
three tests is the cheapest next step"* — was followed and did not work. Recorded because
the reasoning was sound and the conclusion was still wrong: Swiftshader does cache shaders
to disk, and a browser that cannot write does hang silently, so the story fitted. It was
not tested against the amount actually written, which is 5.1 MB.

### Why the tests cannot simply use `file://`

`file://` fixes the symptom in 3.6 s, and it would gut the tests. They read the host
document's `data-theme` from **inside the iframe**, which is a same-origin access; `file://`
gives every file an opaque origin. The server is not scaffolding that could be dropped —
without it the three would pass while measuring nothing.

### What was done

A canary, not an `xfail`. `_command_line_chrome_can_load_http()` probes the one capability
these three need, with a sixty-byte page and a 40 s ceiling, and skips them naming the
reason. If it returns `None` the browser can do what they need and a failure below is a
real one.

Mutation-verified: making the canary claim the environment is healthy puts the three back
to hanging until the runner's timeout.

`tests/test_exported_page_opens_from_disk.py` now reports `...sss....` in seconds rather
than failing after 15 minutes 33 seconds, and the `python` step of the release gate is no
longer blocked by an environment defect.

### Still open, and what would close it

The skip is a bridge, not a destination: a test that skips permanently checks nothing. The
three belong in the TypeScript E2E suite, where Playwright loads http on this machine in
0.2 s, where `exported-page-framing.e2e.ts` and `export-replay.e2e.ts` already open real
exported pages, and where the Python bridge for generating one already exists. Tracked
separately.

## Third pass — 2026-09-06 — the bridge was crossed

The three are in `molsysviewer/js/tests/e2e/exported-page-colour.e2e.ts` now
(uibcdf/molsysviewer#81). The canary and its mark came out with them, and
`tests/test_exported_page_opens_from_disk.py` keeps the seven that open the page from
`file://`, which this defect does not touch. Nothing in the repository depends on
command-line http navigation any more.

The issue was rewritten the same day: its title described a symptom in our tests rather
than the defect, and its body still led with the disk-pressure lead refuted in the second
pass. Both are corrected there, with the old reasoning kept as a comment.

What remains here is a record of the machine, not work owed.

## Withdrawn, not resolved — 2026-09-06

`withdrawn` rather than `resolved` because nothing was fixed. The browser on this machine
still will not navigate to `http://` from the command line, and it never will because of
anything written here: the defect is in a browser, or a distribution, or this host, and no
change to MolSysViewer reaches it. `resolved` would also require a `guard` — the test that
fails if the defect returns — and no such test can exist for a capability this project no
longer uses.

It leaves the queue because the queue is for defects that affect current MolSysViewer
behaviour, and after uibcdf/molsysviewer#81 this one affects none. It is archived rather
than deleted so that the next person who watches `chrome --headless` hang against a local
server on this machine finds two passes of ruled-out hypotheses instead of starting over.

**Not established:** why command-line navigation to http hangs when CDP-driven navigation
to the same URL does not. Chrome's own `--v=1` log shows the component updater completing
and a QUIC handshake continuing, and no error. Whether this is a Chrome defect, a
distribution one, or something about this host is unknown, and the canary does not depend
on knowing.
