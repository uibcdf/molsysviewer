---
summary: Playback advances before pending frame projections can reach a completed draw.
issue: uibcdf/molsysviewer#333
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [trajectory, rendering, synchronization, capture]
guard: molsysviewer/js/tests/e2e/moving-state-capture.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Playback pacing and completed-frame presentation

**Resolved:** bounded correction received; see the final section and shared receipt.


The corrected real fixture sends comm envelopes immediately, delivers their
responses in order and routes diagnostics through that same delivery path.
The native 2-fps/12-second state guard still fails under four logical CPUs,
400% quota and 4 GiB: 31.33 seconds, 4,319 fixed inputs, thirteen owned
processes closed and no pressure interruption. Twenty actual model changes
occur after the capture request while interaction/dynamic projections remain
pending on the sampled draws. Earlier two-CPU, four-CPU quota-only and
transport failures remain separately recorded; neither more CPU nor a larger
capture deadline establishes the correctness contract.

The playback interval advances independently of pending model work and the
first presentation of a frame. Under a slow renderer it can run immediately
after a draw, before replies for that frame can be presented in another draw.
The ordinary one-owner player must allow a bounded presentation opportunity,
retain requested cadence for already-ready scenes, and keep progressing when
data or a visible draw is unavailable. Camera motion continues throughout.

Complete issue inventory: four pages, 331 entries, final page 31. Closed #238
covers source/popup clocks and stopped convergence, #328 dropped shape refresh,
#329 native cells, and #331 late stop feedback. This is a separate A5/#319
prerequisite under #315, without changing the original denominator.

## Working direction and required receiving

Use the existing playback interval, without an extra clock. Do not overlap
model updates. If projections are pending, give a newly presented frame at
most one ordinary frame period before another advance. A canvas without a
fresh draw uses application time, so hidden/unavailable rendering does not
freeze the trajectory. Ignore BehaviorSubject replay; own the draw observer
through restart, stop and disposal. Readiness uses the same unweakened native
projection conditions as capture, independently of capture being requested.

Receive normal-ready cadence, delayed/unavailable projections, pending model
work, hidden-draw fallback, no duplicate clocks and cleanup. Keep the actual
held-reply/two-frame test, source deadline, independent molecular geometry,
state/session restoration and full popup/hidden/legacy receiving. Working code
does not advertise protocol 2 or authorize publication.

The working correction also avoids restarting dynamic queries from unchanged
frame summaries. The complete trajectory-state subscription still updates UI,
but a repeated playback/default summary is not a new molecular frame. Capture
preparation retains its explicit query and all original readiness conditions.
The ordinary controller disposal now releases the player's owned interval,
notification poll and new draw observer; delayed restart/stop continuations
cannot resurrect playback or publish after disposal.

TypeScript and all builds pass. The eight directed trajectory cases pass,
including normal-ready cadence, bounded unavailable/hidden progress, pending
update serialization, intent correlation and disposal. The canonical Node
suite passes 404/404 with no skips, within two logical CPUs/2-GiB limits.
The unchanged native held-reply state case then passes in 22.55 seconds,
including at least two real frame changes while the Python response is held.
The complete canonical entry passes in 36.20 seconds: moving state and session,
the stopped empty frame, independent recovery, both camera projections and
alternate-camera images/picks. All 4,319 selected inputs remain unchanged and
all thirteen owned processes close. The four-CPU/4-GiB/no-swap scope samples
2,276.9 MiB peak aggregate owned RSS, without a pressure interruption.

The preceding resource interruption, transport failures and source timeouts
remain preserved with their original classification. In particular, a child
exit zero after an outer timeout is not a passing result. Applicable legacy
Studio/controls and v2 endpoint receiving remain separate. This correction is
not yet delivered and does not complete A5 or advertise capture protocol 2.

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
