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

## Open decisions

Each is a decision, not work waiting for a decision already made.

1. **Does `save_state` grow, or does `save_session` appear?** Growing it changes what
   existing files mean; adding one keeps today's document exactly as portable as it is.
2. **What does the camera do** — request-and-wait, mirror-and-mark, or stay with
   `FigureSpec`?
3. **Is a state document bound to a structure?** Even a checksum turns a confusing late
   failure into a refusal at load. This is the cheapest item here and the highest value.
4. **Is version 2 a format users may keep?** If yes, migrations become a release gate.
5. **Do the omissions in row 2 belong in the semantic document at all,** or are they
   session state that only a portable session should carry? The current structure index is
   the interesting case: it is arguably scientific rather than visual.

## What can be claimed today

Precisely this, and it is worth stating rather than softening:

> A saved state restores the semantic content of a scene — regions with the selections that
> produced them, overlays, measurements, colours and representations — onto any compatible
> structure. It does not restore the camera, the current structure, or global visual
> configuration, and it does not carry the molecular system.

Not "complete session reproducibility", and not "pixel-perfect". Neither phrase appears
anywhere in the repository today; the point is to keep it that way.

## Related

- `viewer/state.py` — `export_state`, `import_state`, `save_state`, `load_state`.
- Gate 6 of [`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md),
  which shipped the file helpers and states the same exclusions.
- `figures.py` — `FigureSpec.camera_snapshot`, the existing home for saved framing.
