---
summary: Python player navigation omits public frame-change notifications.
issue: uibcdf/molsysviewer#291
status: resolved
opened: 2026-11-03
closed: 2026-11-03
severity: medium
verification: reproduced
area: [api, trajectory, addons]
guard: tests/test_player_frame_notifications.py
normative: docs/content/developer/public_api.md
blocked_by: []
supersedes: []
---

# Python player navigation omits frame notifications

## What

uibcdf/dockingmt#60 needs its pose explorer to follow public Python navigation through
`on_frame_change`, without polling or replacing player methods. A real
pentalanine view with three nonconsecutive structures reproduces the report:
`go_to_structure(1)` sets `player.index` to 1 but leaves the callback list empty.
The frontend event route dispatches callbacks, while the Python player does not.
The original 21-case regression invocation fails 20 cases and passes one
transport-failure control. Its JUnit is retained in local task evidence.

## Contract and implementation

Retain the existing three-field callback payload. The frame is the index in
the currently loaded MolSys, as already used by the player and frontend; source
maps retain pre-extraction correspondence separately. A successful Python seek
notifies synchronously after summary and visible-box updates. Canvas authority
commands use that same player; periodic playback feedback uses the same private
dispatcher. Neither path certifies a finished GPU draw.

Compare the previous and accepted `(frame, is_playing)` states to suppress
identical feedback and repeated seeks. Keep received playback-state transitions
observable at the same frame. A per-player queue preserves acceptance order
when a callback navigates again. Give each callback an independent dictionary;
one subscriber's exception cannot stop others. Unsubscription is immediate,
and close clears subscribers/queued events and ignores late frame feedback.
Reject nonexistent frame indices before changing state; preserve provider and
transport failures without publishing a successful-navigation event. Navigation
is not a molecular transaction or an asynchronous renderer acknowledgement.

## Verification and limits

The real-demo regression covers all navigation methods, wrapping, loaded/source
indices, current-frame no-ops, canvas authority commands, frontend echoes,
playback state, visible boxes, callback failure/mutation/reentrancy/removal,
view isolation, empty/closed views and provider/transport failures. Controlled
failure injection targets actual boundaries; it does not replace molecular data.
The first extended boundary selection passes 166 cases, including 25 new cases.
The [receiving receipt](../player_frame_notifications_receiving_20261103.json)
retains native result hashes, scope and the original failures.

No scientific addon, coordinate data, TypeScript runtime, dependency floor,
candidate, tag or package publication changes. Source receiving does not qualify
an installed artifact or a live DockingMT/Jupyter canvas.

## Resolution — 2026-11-03

The private player dispatcher now serves direct navigation, play/pause and
frontend feedback, preserving the existing three-field payload. Initial/paused
state transitions are explicit so echo suppression cannot silently remove their
notification. Empty views do not publish nonexistent frames. The real-demo
guard's 30 cases protect the actual missing Python dispatch, duplicates,
indices, failure semantics, subscriptions, reentrancy and lifetime.

After correcting the diagnosed test infrastructure/fixture failures, a fresh
complete core invocation passes 3,393 cases with 21 explained skips and 14 Qt
cases deselected. Following the final play/pause and empty-view polish, every
test module calling the public player and its callback/lifetime boundaries
passes again: 327 cases, including all 30 new guards, zero skips/failures/errors.
These are separate invocations, not a new combined full-suite count. All 3,034
provider Python/native files remain byte-identical. Strict Sphinx and whole-tree
Ruff pass; the documentation callback recipe executes on real pentalanine.
The former dummy measurement system is replaced with a two-frame real-demo
extraction while preserving the independent 1/2-angstrom expectations.

Committed-head CI remains to be received; source resolution is not public
artifact qualification. The independent #269 Linux recovery uses the earlier
runtime and stays open. No tag, package or publication follows from this closure.
