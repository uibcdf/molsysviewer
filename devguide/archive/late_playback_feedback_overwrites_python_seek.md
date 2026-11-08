---
summary: Late playback-stop feedback overwrites a newer explicit Python frame selection.
issue: uibcdf/molsysviewer#331
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [trajectory, authority, synchronization, capture]
guard: tests/test_player_frame_notifications.py::test_late_playback_feedback_cannot_undo_newer_python_seek
normative:
blocked_by: []
supersedes: []
---

# Late playback feedback and explicit navigation

**Resolved:** bounded correction received; see the final section and shared receipt.


The A5 real-browser empty-selection control calls public `player.pause()` and
`player.go_to_structure(1)` consecutively. The actual frames become
`[0, 1, 2, 1, 2]`: frame 1 applies and is then undone. A received stop feedback
for frame 2 updates Python and echoes another `set_trajectory_frame(index=2)`.
At failure, playback is stopped, no frame/dynamic work remains and both sides
describe frame 2. This is independent of intermediate state/session restores.

Baseline `5390fadb` plus the unadvertised moving-capture prototype, real
pentalanine `[0, 8, 3]`, Molstar 5.4.1, Chromium and a real Python authority.
The isolated run exits 1 after 45.66 seconds, with 4,318 fixed inputs and all
thirteen owned processes closed. Full commands and original logs remain in
the private working evidence. No unchanged published artifact is claimed.

`viewer/core.py` accepts every `trajectory_frame_changed`, overwrites the
accepted index and echoes stopped feedback. There is no generation identifying
the Python intent the event describes. A newer accepted seek is therefore
indistinguishable from the state before a delayed stop acknowledgment.

Complete issue acquisition has four pages, 329 entries and final page 29.
#291 concerns missing Python callbacks, #312 missing measurement summaries,
#314 plot-origin authority, #328 shape refresh and #329 native box following.
None records this command/feedback ordering. This child remains inside A5/#319
and the original 46-leaf denominator; it does not advance the delivered count.

## Required correction and receiving

Preserve the latest explicit navigation/playback intent with bounded, validated
correlation metadata. Older stop or playing feedback cannot alter Python's
index, playback, callbacks, cell or measurement summaries. Accept valid current
feedback, preserve ordinary legacy behavior, view/window isolation, no-op
semantics and one playback clock. Do not insert a delay between the two public
calls to hide the race.

Keep the real molecular browser control, plus directed delayed/reordered-event
coverage, stopped and playing cases and explicit selection of a frame with an
empty dynamic region. Moving state/session capture, popup/hidden qualification
and #330's presentation receiving retain their separate acceptance. Publication
remains paused.

## Working correction

The two directed real-demo cases first fail with `assert 2 == 1`, for stopped
and playing stale feedback. Python now stamps each accepted navigation/play/
pause/rate command with a monotonic per-view intent revision. Current frontend
handlers retain it in periodic feedback, stop completion and popup projection;
a stop keeps the revision it began with while awaiting native work. Python
rejects mismatched or malformed supplied revisions before changing authority,
callbacks or summaries. Old frontend events without the optional field keep
their legacy behavior; they do not gain this new correlation guarantee.
Replays retain the current revision without creating another user intent.

The source and new directed guards are still working-tree changes. Native
receiving of the originally failing public calls is the next causal check.
The separate intermittent uninterrupted-capture timeout remains unresolved;
this navigation fix must not be credited as its cause without evidence.

The six-file Python player/popup/capture receiving passes 173/173 in 89.35
seconds, retaining 153 legacy-H5MSM warnings. TypeScript checks and the
directed handler entry pass (the sandbox aggregates that entry as one file,
so it is not a canonical per-case Node count). The native empty-frame control
now reaches/captures frame 1 and passes the no-rollback checks; its later
independent restored-region assertion fails under #332. Keep that overall
exit 1, 20.66 seconds, 4,319 fixed inputs and thirteen closed processes; this
is causal receiving of navigation, not a passing full persistence guard.

Complete native moving receiving subsequently passes state, session and the
empty saved frame in 36.20 seconds after #332/#333. All 4,319 inputs remain
fixed and thirteen owned processes close. This does not qualify hidden/v2
endpoints or explain every earlier intermittent failure.

Final source review exposes another incomplete-rejection path: an obsolete
frame command is ignored by the trajectory handler, but its containing
controller case still applies the old cell and playback metadata. A directed
probe using the real controller/handler first fails because the cell moves
from structure 0 to 1. The internal frame operation now returns acceptance,
and the controller applies projections only for accepted commands. A guard
checks both rejection and the newer accepted command; native geometry remains
covered separately. Type checking additionally requires Movie's existing
completion callback to await the operation while retaining its void result.

The accepted/rejected-envelope Node guard passes in the 405-case canonical
entry. Three older Python wire/rebuild modules first report 47 passes and
four failures because their full expected dictionaries omit the revision (and
the already introduced box-follow marker). Exact dictionaries now retain all
fields, including fixed revision counts; all 51 then pass. The overlapping
fourteen-file Python boundary passes 672/672 with 4,320 fixed inputs, no skips
and 692.6 MiB peak aggregate owned RSS under one CPU/2 GiB. Warnings and the
original four failures remain preserved.

## Resolved bounded correction — 2026-11-07

The canonical shared-browser selection passes all three complete Studio,
box-trajectory and moving-state entries in 429.86 seconds. It retains every
operation deadline and the 360/180/180-second entry budgets, with no skips or
pressure interruption. All 4,323 selected inputs stay fixed; thirty owned
processes close with no survivors or cleanup errors. Execution uses four
logical CPUs/400%, 4 GiB and no swap; sampled aggregate owned RSS peaks at
3,337.8 MiB. Source coordinates and all independent scene-geometry assertions
are retained. Canonical Node passes 406/406. The overlapping Python boundary
passes 672/672 on its recorded pre-final-camera source; its Python production
inputs remain unchanged by the later camera/test-only corrections.

See [the receiving record](../moving_capture_renderer_receiving_20261107.json)
for exact earlier scopes, original failures, the secondary diagnostic error
and the check-log reuse incident. Earlier controls receiving keeps its
pre-final-envelope/camera source scope; the final Studio guard receives those
changed camera/popup boundaries. This closes the bounded defect, not parent
A5/#319, hidden/protocol-2 endpoint or actual-Jupyter acceptance. The frontend
still advertises protocol 1 only. Original-plan progress remains 8/46 delivered
and 1/46 finally accepted; Movie #320 and all publication pauses remain.
