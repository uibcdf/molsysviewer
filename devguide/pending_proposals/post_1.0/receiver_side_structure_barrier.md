---
summary: Move the structure barrier to the receiver.
issue: uibcdf/molsysviewer#53
status: open
opened: 2026-07-31
closed:
verification: inspected
area: [transport]
guard:
normative:
blocked_by: []
supersedes: []
---

# Move the structure barrier to the receiver

**Filed 2026-07-31, out of the defect that produced Contract S8.**

## What is in place

`scene_contracts.md` Contract S8 is enforced on the **Python** side:
`_send_widget_message` holds scene messages while an array-native generation is in
flight and flushes them, in order, when the frontend confirms the structure is
applied. It closed the real defect (a measurement created from Python was never
drawn) and it covers both the host canvas and the popup snapshot.

## Why it is not the final shape

The sender is reasoning about a fact only the receiver knows: *whether there is a
structure to draw on*. Python infers it from `structure_data_complete`, which works
because that ack is emitted after `onComplete` — a coupling that is correct today
and invisible tomorrow. Three consequences:

1. **It is one barrier per transport.** The host widget and the popup endpoint are
   handled because both stream through the same Python chokepoint. A future
   endpoint that receives a generation by another route (a standalone Qt host, a
   worker, a cached generation the frontend already holds) does not get the barrier
   for free.
2. **It serialises more than it needs to.** Panel summaries carry no geometry and
   could be applied against an empty canvas perfectly well, but they wait with
   everything else because distinguishing them would mean classifying ops — the
   allowlist trap S8 deliberately avoids.
3. **The knowledge is in the wrong place.** `index.ts` already owns a serialised
   message queue. It knows exactly when its structure exists, per endpoint, with no
   round-trip and no inference.

## The proposal

A barrier in the frontend's message queue: while a generation is being received,
scene ops wait on a promise that resolves when the structure is applied;
data-plane messages bypass it (they are what resolves it). Python then goes back
to sending freely.

The deadlock hazard is the whole difficulty, and it is why this was **not** done
first: the chunks that complete the generation travel through the same queue that
would be blocked waiting for them, so the bypass has to be exactly right, and a
frontend that never completes needs its own timeout and fallback. Python already
has that machinery, proven and tested (`_check_binary_structure_ack_timeout`,
`_fallback_binary_structure_stream`); the frontend would need an equivalent.

Doing it during a smoke-test cycle would also have meant rebuilding `viewer.js`
underneath the user mid-diagnosis.

## Acceptance

- The Python-side gate is removed, and `tests/test_structure_stream_ordering.py`
  is rewritten against the frontend barrier without weakening a single claim.
- A JS test asserts a scene op issued mid-stream is applied **after** the
  structure, and that a stream which never completes releases its backlog rather
  than stranding it.
- The E2E suite covers the notebook order that started this: build the scene, then
  display the view, then assert the measurement is in the Mol\* render tree.

Related: [[data_plane_architecture]], `scene_contracts.md` Contract S8.
