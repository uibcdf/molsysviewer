---
summary: Define reproducible browser and render-worker E2E evidence lanes.
issue: uibcdf/molsysviewer#100
status: open
opened: 2026-09-24
closed:
verification: measured
area: [testing, ci, release]
guard:
normative:
blocked_by: []
supersedes: []
---

# Define reproducible browser and render-worker E2E evidence lanes

**Reported:** 2026-09-24, after a hosted staging run and an exact-source local
run reached different failures in the same 37-scenario suite.
**Scope decision, 2026-09-26:** deferred to post-1.0 by the maintainers. The
remote implementation remains in distributed packages as an unsupported preview,
but remote-client and managed server-GPU E2E certification are not 1.0 gates.
The mandatory 1.0 browser lane is the 34-scenario non-remote core lane; it must
still pass on a real hosted browser. The 36-scenario portable lane, two-scenario
remote-portable lane, one-scenario server-GPU lane and full 37-scenario command
remain available for diagnostic or later certification. No remote failure is
relabelled as a pass, and `E2E_ALLOW_SKIP=1` is not release evidence.
The core lane passed locally on 2026-09-26, 34/34, with Chrome 149 and real
WebGL2/SwiftShader. Hosted exact-commit core evidence remains to be collected;
the local pass does not certify hosted CI or any remote scenario.
`CI_e2e` runs core automatically. A manual dispatch may instead select the
`remote-portable` diagnostic lane on hosted Chrome. The managed server-GPU
scenario still requires a qualified host; it is not silently run on standard
Ubuntu or counted as passing from the remote-portable result.

## What

Separate the client-browser and server-render-worker scenarios into
independently addressable evidence lanes. Keep local browser checks and a
hosted route, with exact source and browser identity; do not silently skip a
capability or call a partial suite green. Decide explicitly which observations
are release requirements and which remain diagnostic.

## How

Hosted staging run `36019810581` reached 22/37 scenarios, then
`remote-client-rendering` failed waiting 30 seconds for the PNG `download`
event. That scenario passed locally using `/usr/bin/google-chrome` and the
`python-3.14-support` MolSysMT and MolSysViewer source branches. The local
full run then stopped in `remote-session` at scenario 25/37: the Python render
worker opened a command-line headless Chrome target for a localhost URL, but
the page remained `about:blank`. This matches the local host limitation
documented in uibcdf/molsysviewer#77. Thus neither environment supplied a
full 37/37 pass, although both supplied valuable non-overlapping evidence.

The redesign should make each suite selectable without editing the runner;
retain a full aggregate command; report scenario, browser version, source
commit, and whether the canvas actually rendered. Export checks should
distinguish a browser error from slow image generation and verify the real
download bytes without treating a fixed 30-second wait as a product SLA.
The render-worker lane needs a host capable of command-line HTTP navigation,
or a validated change to the worker that removes that host dependency. An
explicit release policy must say how local and hosted results compose.

## Why

Making all E2E local-only on this machine would lose server-render-worker
coverage. Keeping a full hosted gate that stops at scenario 23 also prevents
later scenarios from producing evidence. Both are poor choices when the goal
is a truthful 1.0 checkpoint. The original assertion that #77 costs this
repository nothing is now false for `remote-session` and is corrected in its
archived report.

## What was refuted

- The Playwright browser installer was not necessary for these E2E scripts:
  the harness already selected the runner's `/usr/bin/google-chrome`; hosted
  runs stalled extracting an unused browser archive.
- Local success of `remote-client-rendering` does not imply the full 37-case
  suite is green. The local render-worker scenario failed immediately after.
- Hosted failure at a 30-second PNG wait does not establish that exporting is
  broken: the same scenario completed its PNG and HTML downloads locally.

## Resolution

Lane selection is implemented; exact-commit hosted remote validation and a
working server-GPU run remain for post-1.0. No existing E2E has been disabled
or counted as passed by a skip. The 2026-09-26 scope decision supersedes the
earlier assumption below that complete remote E2E must block 1.0.

## 2026-09-24 interim decision for coordinated package publication

The 37 suites are now selectable as 36 `portable` browser suites and one
`server-gpu` suite (`remote-session`); the existing `test:e2e` command still
runs all 37. `CI_e2e` uses the portable lane because a standard hosted Ubuntu
runner is not a certified hardware-GPU render-worker host. The source-pair
portable lane passed locally, 36/36, with Chrome 149 and real WebGL2; this is
provisional evidence for the coordinated pre-1.0 package publication, **not**
a 37/37 claim or a substitute for the later server-rendering gate.
The portable pass printed one `aiohttp` task exception while closing a
WebSocket in `remote-client-rendering`; the scenario still completed its real
reconnect, export, and upload assertions. Review that shutdown noise during
the deferred reliability pass instead of calling it a scenario failure.

The earlier `nvidia-smi` failure occurred inside the development sandbox. A
repeat outside it found a GTX 1080 and Quadro M2000 on `nauta`, so the local
server-GPU failure cannot be classified as absent hardware. The original
command-line URL launch again left the worker at `about:blank`. A focused
attempt to launch `about:blank` and navigate with CDP `Page.navigate` hung until
a 30-second bound, even with `no_sandbox=True`; Playwright with the same GL
flags reached a trivial local HTTP page. That attempted production change was
reverted. The test harness now prints startup stages and bounds its wait for
the Python bridge so the next investigation will not silently hang.

Defer the server-GPU launch fix and full 37/37 validation until after the
coordinated MolSysMT/MolSysViewer package publication. Do not set
`E2E_ALLOW_SKIP=1` in release evidence. A portable pass is labelled portable;
the `server-gpu` lane remains runnable and fails if its capability is broken.

The maintainers explicitly accept this as a **pre-1.0 release exception** for
the coordinated MolSysMT `0.22.4` / MolSysViewer `0.23.4` candidate, not as
passing E2E evidence. Hosted portable run `36038233512` failed at scenario
23/36 (`remote-client-rendering`, 30-second PNG-download timeout); the local
source-pair portable run passed 36/36. The server-GPU lane is still not
certified. This decision permits the pre-1.0 package candidate to proceed
through its other exact-commit and installed-pair gates while #100 stays open.
It does **not** waive the full E2E or real-window gates for 1.0, and must be
visible in any pre-1.0 release decision rather than described as green CI.
