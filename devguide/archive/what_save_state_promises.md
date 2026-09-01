---
summary: State what a saved state restores, and separate scene state from visual state.
issue: uibcdf/molsysviewer#38
status: resolved
opened: 2026-08-12
closed: 2026-09-01
verification: measured
area: [state, export]
guard: tests/test_session_bundle.py::test_a_session_reopens_with_nothing_loaded_first
normative: devguide/session_reproducibility.md, devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# What `save_state()` promises

**Status:** open. **Raised:** 2026-08-12, from outside the project, to make the paper's
reproducibility claim precise rather than generous.

The request is to say exactly what a saved state restores, and to separate *semantic scene
state*, *visual state*, *molecular data* and a *portable session* instead of letting one
function stand for all four.

The premise is right, and the exclusions are already deliberate — `save_state`'s docstring
names three of them. What is missing is a stated boundary, and one obstacle the request
does not anticipate.

## What it holds today, measured

`export_state()` emits a version-2 document with fourteen keys:

```
active_selection  annotations  layers  measurement_settings  measurements
order_high_water_mark  regions  sections  selections  shapes
tag_high_water_marks  uid_high_water_mark  version  whole
```

Regions carry their full recipe, so a region survives as *the rule that produced it*, not
as a frozen index list. That is the strongest thing in the document and the reason
"semantic scene state" is the right name for it.

## What it does not hold, and why

| Excluded | Decision or omission? |
| --- | --- |
| the molecular system | **decision.** The document restores onto a structure you load first; that is what makes it small and shareable |
| undo/redo history | **decision**, and the request agrees |
| transient regions (`focus`, `orientation`, `plane`) | **decision.** They are overlays, and must not come back as permanent regions |
| camera | **blocked** — see below |
| current structure index and playback | **omission.** `view.player` exposes `index`, `fps`, `step_size`, `mode`, `direction`; nothing reads them into the document |
| global visual configuration | **omission.** Scene style, background, lighting, fog, clipping defaults |
| which structure the document belongs to | **omission**, and the sharpest one: loading a state onto the wrong system fails late, confusingly, or not at all |

## The obstacle: the camera is not Python's to save

Everything above is Python-side truth and can be serialised by reading an attribute. The
camera cannot:

```python
# viewer/camera.py:242
def get_snapshot(...):
    """Return the last camera snapshot received from the frontend."""
    return self._view._last_camera_snapshot
```

It is **the frontend's state, mirrored back**. On a viewer that has never rendered, or one
the user has never moved, it is `None` — verified. So `save_state()` cannot simply grow a
`camera` key: it would sometimes hold a view and sometimes hold nothing, with no way for
the reader to tell "the camera was here" from "nobody asked the browser".

This is the one piece of visual state that breaks the project's own rule that Python is
the only authority for reproducible scene state. Any design has to answer it explicitly —
request-and-wait before writing, write what is mirrored and mark its absence, or leave the
camera to `FigureSpec`, which already carries a `camera_snapshot` for exactly the case
where framing matters.

## Schema versions: today it refuses rather than migrates

`STATE_VERSION = 2`, and `import_state` rejects anything else — *"version 1 documents are
no longer supported."* There is no migration path and no deprecation window. That is
defensible for a pre-1.0 format nobody has archived yet, and it stops being defensible the
moment a saved state outlives the version that wrote it. **The 1.0 decision is not which
migrations to write; it is whether the format is one users may keep.**

## The four things, named

The request asks for this distinction, and the boundary falls between the second and third
rows rather than at the end:

1. **Semantic scene state** — what `export_state`/`save_state` hold today. Recipes, not
   pixels: regions, overlays, colours, the whole's representation. Portable across any
   compatible structure.
2. **Visual state** — camera, current structure, playback, scene style, background,
   lighting. Some Python-side and merely unimplemented; the camera is not.
3. **Molecular data** — deliberately out. Restoring needs the structure loaded first.
4. **Portable session** — 1 + 2 + 3, or 1 + 2 plus a *reference* to 3. Does not exist,
   and is not implied by anything shipped. If it is ever built it is a new entry point
   (`save_session`), not a wider `save_state`.

## Open decisions — **all five answered 2026-09-01**

Each was a decision, not work waiting for a decision already made. Kept as written, with
what was decided under each.

1. **Does `save_state` grow, or does `save_session` appear?** Growing it changes what
   existing files mean; adding one keeps today's document exactly as portable as it is.

   > **Both.** The question assumed an exclusive choice and the answer was not one.
   > `save_state` grew by what belongs to a scene — the vantage point and the identity of
   > the structure it was written from — and `save_session` appeared for what belongs to a
   > session, which is the molecular system. Growing it was safe because nobody holds a v2
   > document yet.
2. **What does the camera do** — request-and-wait, mirror-and-mark, or stay with
   `FigureSpec`?

   > **Both, split by caller.** The frontend already mirrors the camera to Python every
   > 300 ms, so `export_state` reads what it holds and never asks: it runs on every
   > undoable operation and could not afford a round trip. `save_state` requests and
   > waits, because a save is a deliberate act and a save inside the debounce window
   > would otherwise record the previous view.
3. **Is a state document bound to a structure?** Even a checksum turns a confusing late
   failure into a refusal at load. This is the cheapest item here and the highest value.

   > **Bound, but not refused — re-resolved.** The checksum is there (atom count plus a
   > topological fingerprint), and refusal on mismatch was implemented and then withdrawn:
   > too strict, since loading onto a related structure is a capability Contract S7 tests,
   > and too weak, since it never fires on a system of the same size whose indices mean
   > other atoms. The fingerprint became a trigger instead: on a mismatch, objects are
   > re-resolved by recipe or by atom identity, and what cannot be resolved is marked
   > broken (uibcdf/molsysviewer#66).
4. **Is version 2 a format users may keep?** If yes, migrations become a release gate.

   > **Yes, from v2 onward.** v1 is not read and never will be — nobody holds one. The
   > policy is that a document from an older v2 build loads, with limitations and a
   > warning, rather than failing; additive keys (Contract S5) are what makes that
   > possible, and `structure`, `view` and `focus` were all added that way.
5. **Do the omissions in row 2 belong in the semantic document at all,** or are they
   session state that only a portable session should carry? The current structure index is
   the interesting case: it is arguably scientific rather than visual.

   > **In the document, under `view`.** The structure index settled it: for a trajectory
   > it is a claim about which structure was being looked at, not a preference. The
   > boundary that turned out to matter was a different one — the undo checkpoint, which
   > takes the same projection and must *not* carry the vantage point, or undoing an
   > annotation would move the camera.

## What can be claimed today

*Rewritten 2026-09-01. The paragraph this replaces is kept below, because the difference
between the two is the work.*

> A saved **state** restores the semantic content of a scene — regions with the selections
> that produced them, overlays, measurements, colours and representations — together with
> the vantage point it was saved from: the camera, the structure index and the playback
> settings. It restores onto any compatible structure, and onto a *different* structure it
> re-resolves what it can and marks the rest broken rather than placing it somewhere
> plausible. It does not carry the molecular system.
>
> A saved **session** carries the molecular system as well, and reopens with nothing
> loaded first.

Still not "pixel-perfect": global visual configuration — scene style, background,
lighting — remains outside both. Neither phrase appears in the repository, and the point
is still to keep it that way.

The claim this replaces, for the record:

> *A saved state restores the semantic content of a scene — regions with the selections
> that produced them, overlays, measurements, colours and representations — onto any
> compatible structure. It does not restore the camera, the current structure, or global
> visual configuration, and it does not carry the molecular system.*

## Resolution

Delivered across four commits, one per row of "the four things":

| | commit | what landed |
| --- | --- | --- |
| structure binding | `4ac9c612` | identity, and re-resolution onto a different system (#66) |
| visual state | `17ce154b` | the `view` key; `792ce2c9` kept it out of undo checkpoints |
| focus as state | `739ef94c` | a focus overlay is saved and comes back a focus (#67) |
| portable session | `c065d3a2` | `save_session` / `load_session`, a `.msv` bundle |

Two defects were found underneath the proposal rather than by it — #66, a region recipe
the document carried and import ignored, and #67, a focus overlay that survived a save
only if the user had named it. Both are archived separately.

The durable rules went to `session_reproducibility.md` (the session file, and the size
question still open) and to `scene_contracts.md` (§A.5, §C.2).

**Not done, and deliberately:** a session has no size budget. It is as large as its
trajectory, and `scale_budget.py` already holds the machinery for the equivalent question
on load — but the threshold is policy, so it is recorded rather than guessed.

## Related

- `viewer/state.py` — `export_state`, `import_state`, `save_state`, `load_state`.
- Gate 6 of [`pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md),
  which shipped the file helpers and states the same exclusions.
- `figures.py` — `FigureSpec.camera_snapshot`, the existing home for saved framing.
