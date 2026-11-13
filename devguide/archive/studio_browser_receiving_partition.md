---
summary: Split accumulated Studio browser receiving into bounded layout and live-capture entries.
issue: uibcdf/molsysviewer#377
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: reproduced
area: [tests, capture, studio]
guard: tests/test_e2e_reliability.py::test_studio_core_scopes_preserve_the_complete_direct_guard
normative:
blocked_by: []
supersedes: []
---

# Resolved: bounded Studio browser receiving

The integrated Studio entry exceeds 360 seconds in controlled #372 receiving
`702` (8 CPU/4 GiB, no resource stop, unchanged inputs). Its completed
widget/popup state/session, camera, cancellation and own-verdict assertions
pass. This is an accumulated suite deadline, not a demonstrated failure of an
individual operation. Preserve the original timeout.

Core now explicitly runs the layout/download/card/catalogue/lifetime and
trajectory-shape scope through `studio-usability --layout-only`. A second
mandatory `studio-live-capture` entry invokes the unchanged persistent capture
owner with the same viewport, downloads and private workspace. Both retain
bounded suite execution and every operation deadline. All original assertions,
real Python/native transport and cleanup remain.

The direct historical `node tests/e2e/studio-usability.e2e.js` guard still runs
both scopes by default; it has not silently lost live capture. The new entry
is registered in the same canonical build and core lane, raising the inventory
to 63 entries/60 core. The guard requires the explicit core partition, mandatory
live entry and retained complete historical call. #373's inventory correction
and #372's qualification retain their separate scope.

Partition receiving `704` passes layout/downloads/card/catalogue/lifetime and
trajectory geometry in 156 seconds. The persistent capture scope completes
primary, canvas-popup and detached-Studio state/session roundtrips, own-verdict
and cancellation assertions, then reaches its 360-second aggregate deadline
during the remaining camera-intent controls. No individual deadline or completed
assertion failed. Preserve that result as incomplete. The persistent scope now
has a separate 600-second aggregate budget; every original operation deadline,
assertion and cleanup remains. This is a bounded receiving budget, not a claim
that long interactive saves are acceptable or that the unfinished controls pass.

Receiving `705` passes all eight runner controls and builds all 63 entries.
Canonical live receiving `706`, with no timeout override, completes every
persistent primary/popup/detached state/session, actual-draw camera-intent,
same-ID ownership and cancellation assertion in 365 seconds. Its supervisor
records native exit 0, unchanged inputs, no resource stop and no surviving
owned process or cleanup error. Summed owned-process RSS peaks at 3,019.9 MiB
inside the 8 CPU/4 GiB scope. Together with `704`'s layout result, both partition
entries are source-received. Broader #372 host/platform/installed gates remain
pending; this is not full-core or human acceptance.
