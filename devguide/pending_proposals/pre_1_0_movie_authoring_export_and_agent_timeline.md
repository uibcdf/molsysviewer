---
summary: Complete movie authoring and useful export before 1.0, with a timeline future agents can consume.
issue: uibcdf/molsysviewer#320
status: open
opened: 2026-11-06
closed:
verification: inspected
area: [movie, animation, export, studio, public-api]
guard:
normative:
blocked_by: []
supersedes: []
---

# Movie authoring, export and future agent planning

**Approved product requirement; detailed design and expanded implementation
pending.** The principal maintainer explicitly requires useful movie authoring
and export before 1.0. [#320](https://github.com/uibcdf/molsysviewer/issues/320)
records the accepted scope and example story. Natural-language planning through
future MolSys-Agent/MolSys-AI integration follows after 1.0; the shared movie
model and execution surface must be suitable for that later consumer now.
No movie production code changes accompany this record.

## Current evidence and ownership

The complete duplicate review contains four pages and 318 issue/PR records,
including closed #36/#172/#177/#273. Those repairs protect distinct camera,
draw, interruption and native-host boundaries; they do not receive this whole
workflow. Inspected source is Viewer `a7f1c1c7`, unchanged Movie code in the
current #319 working tree. Existing `MovieManager` handles camera keyframes,
structure sweeps, layer visibility, JSON recipes, preview/stop and a video/GIF
export path. It is the foundation to assess and extend, not a blank project.

The inspected keyframe schema does not offer the full requested timed scene
actions, no Movie authoring surface was found in Studio's panels, and
`StateMixin.export_state` does not retain a Movie timeline. A recipe is not a
working web presentation. Format documentation and an archived implementation
plan are not installed/runtime qualification. The
[current vision](../molsysmovie_vision.md) and
[user reference](../../docs/content/user/movie/index.md) need reconciliation
with the accepted scope, not silent reinterpretation as completed work.

Viewer owns visual composition, scheduling, playback and export. Scientific
libraries/add-ons own preparation and calculation. Agent components own later
language interpretation and planning. Keep [the product boundary](../core_and_addon_boundary.md),
Python composability, explicit scientific parameters and the existing
experimental interactions contract. No LLM dependency is required in core.

## Execution route

| Phase | Deliverable to review | Evidence before calling it complete |
| --- | --- | --- |
| M0 — reconcile | Capability/format/host inventory, current Movie guards, source versus published dependencies, and concrete gaps against #320 | Actual calls and independently inspected outputs; classify inspected versus reproduced findings and retain related closed issues |
| M1 — model | Versioned timeline, scene baseline, target identity, time/units and channels for camera, structures, appearance, visibility, overlays and needed lighting; conflict and migration rules | Pure Python validation, detached recipes, stable references, save/reopen/remap and unchanged work on rejection |
| M2 — author | Strong Python construction/inspection plus a calm graphical authoring workflow using the same model | Review the proposed API and Studio layout before implementation; verify real input, drafts, targets, timing and useful preview without GUI-only operations |
| M3 — evaluate | Deterministic arbitrary-time evaluation, reverse seek, repeat, completion and interruption, coordinated with the player and camera motion | Same scene at the same movie time; one clock; actual draw/geometry/overlay checks in notebook and popup paths; native-host scope separate |
| M4 — preserve/export | Useful encoded video, other qualified output such as GIF/lossless frames, and a playable portable web presentation with explicit data/runtime assets | Actual readable media, resolution/rate/duration and first/final contents; session/recipe recovery; useful-size memory measurements; truthful failure/cancellation and atomic destination behavior |
| M5 — integrated receive | The pocket/ligand/interactions/labels story from #320, using explicitly supplied molecular/scientific data | Preview, seek, save/reopen, video and web playback agree; cover evaluated/empty/not-evaluated interaction frames and no hidden molecular preparation |
| M6 — claims/docs | Reconciled capabilities, tutorials, availability/dependencies and migration guidance | Source, installed candidates, web assets and applicable native observations retain their own evidence; no unavailable codec or placeholder counts as a delivered movie |

The exact public API names, channel representation, graphical layout and
codec/asset implementation are not decided by this planning record. Derive
bounded owner issues after M0/M1 instead of encoding a broad vision as already
implemented API. Existing #319 work is relevant reusable capture infrastructure;
it does not itself qualify movie export or solve all animation scheduling.

## Scope and progress

The pre-1.0 result must let a user approach a known pocket, reveal a loaded
ligand with an explicit representation, show calculated interactions and labels
at chosen times, zoom out while rotating, and preserve/export the same story.
Generating a pose or new interaction analysis is a separate explicit scientific
operation, not an implicit side effect of playback.

Post-1.0 agent planning translates instructions into this same inspectable,
validated and editable plan, with preview and export through the same owner.
It must not create another playback engine or require direct DOM manipulation.
VR/360 and audio from the older vision are not silently required here.

This is an additional explicitly requested pre-1.0 stream alongside the
[46-item robustness audit](pre_1_0_robustness_audit_and_action_plan_20261106.md).
That audit's 1/46 (2.2%) remains its original acceptance metric, not total 1.0
readiness. Do not hide this requirement by leaving it outside that denominator;
track its inventory and adopted deliverables here until a reviewed consolidated
work breakdown is adopted. Tags, candidates, packages and both 1.0 publications
remain paused. Human smoke review is still postponed.
