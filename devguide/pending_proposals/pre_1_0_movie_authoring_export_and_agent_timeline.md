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

## M0 receiving — 2026-11-07

**M0 is partial.** The current inventory includes source inspection and actual
Python model calls on a fresh bundled dialanine View. It does not qualify the
expanded story, encoded video, portable Movie web playback, a new native host
observation or an installed candidate. No Movie production file or media file
was changed or written by this investigation, and no new failing regression is
committed before the reviewed M1 contract.

The two Movie implementation owners are unchanged against
`9a783d500a756210e70e11946552c4afbe5fe936`: the scoped `git diff --exit-code`
returns native exit 0. Other current working-tree files, including #319
integration, are not covered by that no-difference claim.

| Current source owner | SHA-256 |
| --- | --- |
| `molsysviewer/viewer/movie.py` | `6f3a1ac4cb127da3051347ed294cc096e04e01318fd2d51e9026f3ced242e7b2` |
| `molsysviewer/js/src/managers/handlers/movie-handlers.ts` | `6badc91424a6be7401ea21ba217b6b17ed2c5f9018bde792dd6136ac29fe9e73` |

### Implemented foundation and the requested story

| Boundary | Current source support | Remaining mechanism for #320 |
| --- | --- | --- |
| Camera and structures | `MovieManager` constructs camera vectors, orbits, structure sweeps and visibility steps; TS previews with an animation-frame clock and four easing modes. | A complete baseline and independent channel evaluation must make mixed actions, reverse seek, repeated evaluation and simultaneous zoom/rotation deterministic. |
| Pocket and loaded ligand | Existing region/layer APIs already define molecular subsets and explicit representations. | Movie visibility is an untyped tag map; `viewer-controller.ts` sends it with `kind: "shape"`. It cannot reliably address ordinary regions or other domains. Representation, colour and opacity have no timed Movie channel. |
| Calculated interactions | Viewer already stores analyses separately from representations and projects frame-specific interaction content. | The timeline must reference the supplied visual/result owners and preserve evaluated, evaluated-empty and not-evaluated coverage. Playback must not calculate or prepare molecular data implicitly. |
| Labels and overlays | Static annotations are real Mol* geometry and can appear in captured images. | No timed label text, anchor, visibility or overlay channel exists. Camera-follow label refresh is asynchronous; Movie does not await that geometry refresh. DOM legends/plots have no screenshot compositor. |
| Timeline preservation | Version-1 recipe JSON can be saved and loaded separately. | `export_state()` has no Movie record; session writing inherits that omission. No baseline, target resolution/remapping or timeline restoration contract joins scene and recipe. |
| Media | JS exports sequential PNG data URIs after applying camera/frame/visibility and awaiting a draw; Python decodes them and calls ImageIO. | Export needs correlated jobs, bounded storage, error/cancel/disconnect cleanup, atomic destinations, qualified encoders and explicit sampling/duration/final-frame rules. |
| Authoring and web | Python construction/inspection and ordinary static HTML export are reusable foundations. | No Studio Movie authoring panel, arbitrary-time Movie seek API or portable Movie web presentation/player is implemented. A static scene or recipe JSON does not preserve a playable story. |

The schema at `molsysviewer/js/src/messages/viewer-messages.ts` carries only `time_ms`,
camera position/target/up, structure index, layer visibility and easing. The
scene already distinguishes `(domain, tag)` identity; Movie must reuse that
ownership rather than introduce a competing identity registry.

### Reproduced model gaps

The private receiving workspace is
`.pytest_cache/robustness-20261106/M0-movie-inventory-k_z633ph`. It retains
`probe.py`, `run.py`, the exact command, native output, source hashes and the
empty owner diff. The explicit interpreter is
`/home/diego/Myopt/miniconda3/envs/molsyssuite@uibcdf_3.14/bin/python`; the
probe uses the controlled MolSysMT structural-series source and the recorded
PyUnitWizard `02d0015` snapshot. Its native exit is **0**, in **4.88 seconds**:
the exit means the following observations were confirmed, not that Movie
qualification passed.

- `keyframes` returns a new list with shared nested camera dictionaries.
  Changing a returned camera changes the live timeline.
- `to_dict()` and `from_dict()` also retain nested aliases. Editing an exported
  recipe or the input mapping after import changes the live timeline.
- `from_dict()` accepts a keyframe with time `-100 ms`, an unknown easing,
  an invalid camera and structure index `999999`. Its current validation checks
  version, timestamp presence and ordering, without validating the full record.
- `export_state()` omits Movie even when a timeline exists. The probe verifies
  that molecular coordinates remain exactly unchanged; it writes no state,
  session, recipe or media output.

These observations belong to #320. They are retained as a private probe until
M1 defines the replacement/migration contract; they are not added as red
production expectations that encode a design still awaiting review.

### Inspected evaluation, export and availability gaps

`movie-handlers.ts` selects adjacent whole keyframes rather than adjacent keys
of each channel. Inserting a visibility-only keyframe between camera A and B
can interrupt the camera segment and prevent the final camera from applying.
Structure interpolation has the same adjacency premise. Visibility accumulates
prior changes without reconstructing a complete baseline, so loop/reverse-time
results can depend on playback history.

Preview completion and Stop drain camera writes, while structure and visibility
updates are submitted without awaiting their applied state. The trajectory
player retains its own interval clock, and Movie does not arbitrate it or
spin/rock. Export does await each sampled scene, but has no generation/request
token or cancellation owner and does not stop competing playback. Python
collects uncorrelated frames in one View-wide list and accepts an uncorrelated
export-done event. A missing image can become an empty data URI followed by
export-done; those conditions need explicit terminal failure.

Python export retains every PNG/data URI and then every decoded array before
encoding, so useful-size memory qualification is outstanding. `format=` is
documented and digested but is not passed to the writer; codec selection is not
explicit. The no-frontend `MSM_VIEWS_FROM_HTML_FILES=True` branch can return a
10-by-10 black placeholder as successful output. That branch cannot qualify
the accepted useful-video requirement. These findings are from inspection;
this M0 run did not execute export or an encoder.

The reviewed optional runtime floor remains `imageio>=2.16.0`; it does not
establish a codec installation. This development interpreter has ImageIO
2.37.4 and Pillow 12.3.0, but neither the `imageio_ffmpeg` module nor an
`ffmpeg` executable. MP4/WebM availability was therefore not qualified here.
Current public docs advertise H.264/VP9 and format override more strongly than
the inspected implementation/evidence supports. The vision's class/syntax
examples remain unimplemented design ideas; its status notice and
`devguide/README.md` now point to this approved pre-1.0 requirement. Reconcile
the public capability claims with received outputs during M6.

### Existing guards and the first M1 review

The existing registered browser selector is
`molsysviewer/js/tests/e2e/movie-playback.e2e.ts`, built by `build:e2e:all` and
run in `test:e2e:core`. It protects real Mol* camera interpolation, final-draw
completion and interruption. `molsysviewer/js/tests/unit/movie-handler.test.ts` protects three
camera lifecycle cases. `tests/test_movie.py` mostly uses a DummyView and
synthetic PNGs. The separate Qt workbench guard receives three actual
240-by-160 orbit frames, a readable GIF and a responsive Qt loop; the encoder
may coalesce equal viewpoints. None of these
guards receives the whole pocket/ligand/interactions/labels story, portable web,
useful-size encoded video or the new authoring workflow. They were inspected,
not rerun for this M0 inventory.

Review M1 as one versioned, headless model/API contract before extending GUI or
playback. The first slice should include:

1. A detached scene baseline and explicit molecular/scene identity, reusing
   existing state records and remapping tools. Missing, renamed, ambiguous or
   incompatible targets must have a reviewed refusal/remapping rule.
2. Independent channels for camera, structures, appearance, visibility,
   overlays and required lighting, with domain/tag targets. Define sparse-key
   hold/interpolation, simultaneous keys and same-channel conflicts explicitly.
3. Explicit timebase, frame sampling and quantity contracts. Camera position
   and target are lengths; camera up is dimensionless. Use the registered
   PyUnitWizard boundary, with reviewed migration of the fixed-unit v1 format.
4. Detached construction/inspection/editing/import, full validation and
   transactional replacement. A rejected plan/import must preserve the prior
   timeline and scene. Define v1 migration without guessing ambiguous tags.
5. Save/reopen integration and acceptance fixtures that express the complete
   approved story using supplied scientific data. Later preview, seek, video,
   web and agent consumers must use this same model and one execution owner.

Public names, exact signatures, graphical layout and channel representation
remain to be agreed. M1 does not reduce the approved M2–M6 scope, introduce an
LLM dependency, or promise runtime support for channels before receiving it.

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
