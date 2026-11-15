---
summary: Receive the integrated Movie story through its current saved-key action.
issue: uibcdf/molsysviewer#395
status: active
opened: 2026-11-15
closed:
severity: medium
verification: reproduced
area: [movie, testing, ci, accessibility]
guard:
normative:
blocked_by: []
supersedes: []
---

# Integrated story targets an obsolete saved-key action

Full source run [43686277372](https://github.com/uibcdf/molsysviewer/actions/runs/43686277372)
on `b9f7dfb2` / scientific source `aee7aa65` passes the first 62/63 core
entries and all 25 notebooks. The final `movie-story` entry fails after its
initial scene load, waiting 30 seconds for the exact button name `Edit 1.000 s`.
The full run remains failure; later story assertions are unreached.

The editor intentionally refined in #393 now gives the 1000-ms phase key a
visible `Edit 1 s` caption and accessible name
`Edit phase key at 1 seconds (1000 ms)`. Its row carries
`data-molsysviewer-movie-key="1000"`. The dedicated Studio keyboard guard
already receives those complete identities; the story still uses the former
caption as its accessible selector. This source mismatch is not evidence that
the user edit action or the molecular renderer is broken.

Select the actual saved-key row/action and assert the prepared key-time field
before editing and saving its text. Preserve all original scientific,
coordinate, sparse-occurrence, native/reference-pixel, encoder, session and
offline assertions. Keep the same individual operation deadlines and the
mandatory complete story/core routes. Receive the causal browser boundary
and full affected entry; a shortened diagnostic is not complete story
acceptance. Retain the original failed source run and privately preserved
receipts. Exact installed, actual-host and postponed human scopes remain
separate.

The complete all-state inventory has four pages, 393 records and 365 non-PR
issues. #383's separate live-Jupyter time field and #393's deliberate
precision/accessibility change are related; neither reports this remaining
story selector. Parent #320/#372/#369.

## Scoped receiving — 2026-11-15

The test now selects the exact 1000-ms row and its current accessible action,
then checks that the real form prepares `1` second before editing. The causal
control `883` finds zero obsolete actions and exactly one current action;
Python accepts the actual form save with unchanged scientific data and no
hidden calculations. This control alone is not complete Movie receiving.

The complete unchanged `movie-story` entry passes in `884`: 213.795 seconds
for the browser owner, 241.094 seconds including native-input verification and
supervision. It retains the normal 360-second suite budget and every operation
deadline. Forward/reverse/preview, sparse coverage and occurrence identity,
native geometry, independent session recovery, PNG/MP4/WebM reference pixels
and offline playback all pass without hidden scientific calls. All 6,356
native inputs match the original Mol* 5.13.1 manifest, all 9,979 selected
inputs remain unchanged and all 19 owned processes retire. Peak summed own
RSS is 2,688.5 MiB under the 8 CPU/4 GiB scope; no resource stop occurs.

The [three-block receipt](../molstar_closeout_three_blocks_20261115.json)
preserves the original failed hosted run and these distinct local scopes.
Complete current core receiving remains required before closing this report;
the 62-entry hosted prefix and this local suffix do not form a complete pass.
