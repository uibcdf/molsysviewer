---
summary: Initial molecular Welcome still flashes during human notebook retest
issue: uibcdf/molsysviewer#247
status: resolved
opened: 2026-10-20
closed: 2026-10-20
severity: low
verification: asserted
area: [loading, ui, lifecycle]
guard: molsysviewer/js/tests/e2e/initial-welcome.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Initial Welcome human retest

**Reported:** 2026-10-20, Diego still observes the transient after the source
correction. Existing open/closed reports were checked; #247 was reopened rather
than creating a duplicate. #164 and #240 retain their distinct completed scopes.

## What

The reported `msv.new_view('1TCD')` notebook workflow still shows Welcome for a
fraction of a second. The reporter's current kernel, loaded runtime identity and
restart sequence are not yet known. This is a human reproduction, not a locally
reproduced failure of the corrected runtime.

## How

The previous [source closure](welcome_card_flashes_on_initial_molecular_view.md)
and its passed adapter-based checks are preserved. A new, isolated actual
Jupyter Notebook 7.6.3 / JupyterLab 4.6.4 server was launched with the required
Python 3.14 interpreter. Chromium executed the exact one-cell import/new-view/
display workflow through the real widget manager and kernel. Instrumentation
installed before page startup observed the real controller factory and every
`showWelcomeCard` call; it did not replace rendering or communications.

On source `ace8a80ced55cd9830f52280eabbd2a1aa2a6dca`, construction received
`hasInitialStructures=true` and model `has_molecular_system=true`; 3,983 atoms
loaded, zero Welcome-show calls occurred and no Welcome card remained. A
Jupyter page error reading `schema` was also retained; the molecular widget
rendered despite it. This observation is not a claim of globally clean UI.
The notebook's python3 kernelspec resolves to the required development
interpreter. Logs and screenshot are retained in
`/tmp/msv-247-jupyter-recheck/`; their digests are in the maintained receipt.

## Why

The human result contradicts closing the usability observation. Keep this issue
open until the difference is identified and the real notebook retest succeeds.
No new implementation change is justified by the clean-kernel observation alone.

## What was refuted

A passing adapted transport guard is insufficient evidence to dismiss the human
retest. Conversely, the new actual-Jupyter observation does not reproduce the
reported flash and cannot establish its cause. Runtime caching is a hypothesis:
the Python widget caches the bundle at class import and the page caches its
module, so refreshing just one side need not replace both. Confirmation of the
restart sequence was requested; no stale-runtime diagnosis is asserted yet.

## Next action

Confirm kernel restart plus page refresh and identify the reporter's interpreter,
source path, initial-intent trait and runtime bytes if the observation persists.
Preserve previous test outcomes without rerunning the full Python suite or
changing the product speculatively. Candidate/publication pauses remain.

## Resolution — 2026-10-20

Diego confirms that Welcome no longer appears and considers the problem solved.
He also clarifies that the earlier failing retest had already included a kernel
restart and notebook cache reload. The reason for that earlier persistence is
unidentified; stale runtime remains an unproven hypothesis, not a diagnosis.

Close #247 with the existing source fix `92aef7d74212342df7678756f1735a9a36405269`,
the earlier binary/JSON first-draw guard and actual-Jupyter observation, and this
new human acceptance. No further runtime change or repeated scientific test run
was needed. Guard `molsysviewer/js/tests/e2e/initial-welcome.e2e.ts` observes
Welcome insertions before controller construction through molecular drawing and
checks empty/failure controls. Hosted CI and release qualification retain their
separate scopes in the maintained receiving receipt.
