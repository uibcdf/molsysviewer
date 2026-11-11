---
summary: Receive Movie baseline capture after an owned native camera reset.
issue: uibcdf/molsysviewer#361
status: resolved
opened: 2026-11-11
closed: 2026-11-11
severity: medium
verification: measured
area: [tests, movie, camera, capture]
guard: tests/test_movie_baseline.py::test_native_baseline_reset_and_capture
normative:
blocked_by: []
supersedes: []
---

# Movie camera guard precondition — native control received

Profile 451 passes the changed native representation checks and later fails
the unchanged baseline camera assertion: the authored pose is captured rather
than `[3,4,50]` / `[3,4,5]`. The source/trace/resources remain preserved. This
does not identify the exact native reset owner active in that historical run.

The guard writes `canvas.camera.setState()` after frame navigation. Mol* 5.4.1
resolves queued `requestCameraReset` snapshots at scene commit; its camera
manager's `setSnapshot` uses that owner. A direct mutation can therefore precede
an older native reset, without marking the viewpoint intentional. Receive a
real queued-reset/raw-write adverse control and apply the requested pose through
the production snapshot owner and a fresh draw. Keep the camera/frame assertion,
normal deadlines and native popup/session/media coverage. This is guard
qualification, not a speculative product camera change or timeout increase.

## Resolution

The real native adverse control first observes the raw requested pose
`[3,4,50]` / `[3,4,5]` immediately, then the competing baseline pose on the
next fresh draw. Renderer-local writes do not establish authority across
deferred reset and mirrored input. An intermediate attempted control expected
its arbitrary reset pose but received the existing authored baseline; that
failed scope remains retained too. Neither attempt identified the exact
earlier pending owner in the original failure.

The corrected setup declares frame 2 and the requested camera through the
ordinary Python player/snapshot authority before starting capture. The exact
camera/frame, real rendering, popup, session and decoded-media assertions pass,
with unchanged operation deadlines and no product camera change. The fresh-draw
adverse control has its own bounded subscription and releases it. A later
failure of this owned path would remain a separate product diagnosis.

[The shared receipt](../curated_representation_receiving_20261111.json) keeps
451/454 failures and successful 456 source receiving, including the immediate
and completed-draw native poses. This resolves the guard precondition, not an
unproved historical product camera mechanism.
