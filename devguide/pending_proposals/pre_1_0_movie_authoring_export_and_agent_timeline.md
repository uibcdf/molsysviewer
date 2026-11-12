---
summary: Complete movie authoring and useful export before 1.0, with a timeline future agents can consume.
issue: uibcdf/molsysviewer#320
status: active
opened: 2026-11-06
closed:
verification: measured
area: [movie, animation, export, studio, public-api]
guard:
normative:
blocked_by: []
supersedes: []
---

# Movie authoring, export and future agent planning

**Active requirement; independent tracks, bounded appearance, preview and initial
media export are source-delivered. The complete workflow remains pending.**
The principal maintainer explicitly requires useful movie authoring
and export before 1.0. [#320](https://github.com/uibcdf/molsysviewer/issues/320)
records the accepted scope and example story. Natural-language planning through
future MolSys-Agent/MolSys-AI integration follows after 1.0; the shared movie
model and execution surface must be suitable for that later consumer now.
The dated M0 inventory below retains its original inspected scope; current
implementation and receiving are recorded under Scope and progress.

## Initial inventory and ownership — 2026-11-06

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

The [v1 value isolation correction](../archive/movie_recipe_value_isolation.md)
resolves the first two observations through #355 without changing the format
or signatures. The remaining validation and state gaps belong to #320; M1
defines the replacement/migration contract before new public behavior is
claimed. The original private probe remains preserved.

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

The [M1 model](../movie_timeline_design.md) has its first experimental Python
implementation for camera, structure, visibility and the bounded appearance
catalogue. The design also covers
constant-rate endpoint sampling, migration, one execution owner and bounded
exports. The progress section distinguishes implemented slices from remaining work.

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

**Current source scope:** reviewed version-2 target/frame imports are received
in [the import receipt](../movie_import_receiving_20261111.json), including
explicit scientific associations, region-definition checks, private-ticket
acceptance and retained session/media provenance. The
[timeline contract](../movie_timeline_design.md#reviewed-version-2-imports)
owns those rules. The admitted legacy profile below is now source-received.
Studio has its first experimental Timeline/Preview/Export editor over the
same Python Movie owner, including canvas-owned popup capture and detached
Studio preview/export. Richer renderer channels, complete authoring acceptance,
portable web playback and the complete integrated story remain open. The
receiving entries below retain their original source/date scope; earlier
remapping/appearance gaps are not a claim about current implementation.

The [Cartesian camera receiving](../movie_cartesian_receiving_20261112.json)
adds the explicit `cartesian-constant-up@1` profile to version-2 recipes,
without changing default quaternion motion. Both evaluators admit complete
safe segments before publication. Forty-two independent affine position/target
samples, transactional edit/import checks and native primary/popup seek,
preview and session recovery are received. This supplies a prerequisite for
legacy migration; it does not migrate a version-1 recipe or complete #320.
The original native run `540` times out waiting for three default-preview
samples before reaching the new mode. Its state/cause was not captured and
it remains an unresolved receiving observation here. Diagnostic `542` proceeds
beyond that phase but exposes a synchronous-initial-emission bug in the newly
added draw observer. The corrected observer receives `544`; neither later
result retroactively explains `540`.

The [legacy migration receipt](../movie_legacy_receiving_20261112.json)
receives complete safe Cartesian channels, binary64 rounded-step compilation,
explicit legacy-domain target maps and unknown source-binding provenance.
The original reader/playback remain; unsupported profiles are explicit
conflicts. Headless receiving passes 828 cases with five explicit skips;
the canonical JS entry passes 457. Seven selected native browser suites receive
Movie seek/preview, migrated steps, materials, popup/session symmetry, readable
720p video, cancellation, widget transport and actual renderer lifetimes.
These scopes are not the complete core lane, installed packages or actual
Jupyter/Qt acceptance, and do not close #320.

The test transport now delivers scheduled Python comms spontaneously and
keeps Python alive when the browser closes. The original transport fails the
new isolated scheduled-send control; the corrected route passes. Module
origins and frozen copied support distinguish the current receiving from the
earlier live-owner route. A rejected incoherent draw keeps another native draw
requested without a new clock or a capture-specific pause. Isolated moving
receiving `564` passes the full scenario; `566` still fails the sixth moving
Studio save. Retain both complete outcomes under #344; no successful prefixes
are combined into acceptance. Earlier typing/test-setup failures, resource
interruptions, `554`'s failed aggregate input integrity and the historical
`540` observation remain in the receipt/custody.

The first M1 tranche is source-delivered. `tests/test_movie_timeline.py` exercises
arbitrary seeks and independent channels on a bundled trajectory, detached
inspection, rejection of incompatible inputs and exact session recovery.
The scoped local gate `297` passes 763 tests across Movie, session integrity,
public API and devguide reporting. Its one skip is the missing-`imageio` error
branch because `imageio` is installed. All 10,949 selected inputs stay unchanged
under 2 CPUs / 4 GiB with no resource stop. F1 records seven new experimental
methods and preserves all existing signatures.

The JavaScript runtime now compiles and evaluates the same version-2 recipe.
The shared regression checks 16 samples against Python, including reversed
seeks and a generic half turn. A separate 50-case half-turn differential had
13 disagreements before the common tie rule and zero after it. Appearance and
lighting tracks and remapping/migration remain open.

Scoped receiving passes four JavaScript cases, 62 Python tests (one expected
missing-`imageio` branch skipped), strict checking of the new TypeScript module,
and the rebuilt runtime's 15 shared timeline samples. The complete JS unit run
stopped during bundling at the launch scope's thread cap. Its retry was
deferred by resource review while swap was full.

The first application route, `await view.movie.seek_async(time_ms)`, uses the
existing scene owners and a version-2 primary draw acknowledgment. The new
`movie-seek` core browser case loads a real three-structure system, starts
trajectory playback and spin, then seeks forward and backward. It inspects
the applied camera and frame, verifies that both clocks stop, and observes
the actual Mol* region and same-tag shape nodes. The case passes in profile
`301` in 18.91 s with 2 CPUs / 4 GiB and all 13 owned processes retired.
The scoped Movie, capture, session, public API and reporting gate `304`
passes 844 Python cases, with the expected missing-`imageio` branch skipped.
The browser case uses the widget runtime with an adapted transport. The same route
retains separate installed-host receiving. Studio authoring and portable web
export of version-2 tracks remain open; the first media route is described below.
The existing coherent-capture guard for browser-only visibility changes from
version-1 playback also applies to seeks that reuse that capture service.

Version-2 preview now uses a bounded renderer-clock/authority loop. The
primary renderer proposes the next sample after a completed draw. Python
validates the proposal and applies differences through the scene owners.
One draw is outstanding at a time. `play_async()` completes at the endpoint
or after pause, `pause_async()` drains the current draw, and `seek_async()`
drains playback before switching to its own request. The renderer gets a
compact recipe once and releases its clock on termination. Python checks
revisions between samples and does not copy the molecular trajectory.

The expanded `movie-seek` browser guard passes preview, pause, backward seek,
terminal draw, popup convergence and live session save/reopen. Profile `306`
finishes in 36.40 s at 2 CPUs / 4 GiB, with all 13 owned processes retired.
Scoped receiving also passes 22 JavaScript cases and 848 Python cases, with
one expected missing-`imageio` branch skipped. Profile `308` preserves all
10,962 selected inputs. Actual JupyterLab profile `309` passes playback, pause,
live session save/reopen, rewind and terminal draw through production comms.
It uses one kernel and three bundled structures, finishes in 37.61 s under
2 CPUs / 4 GiB, and retires all 19 owned processes. Its final clock is retired.
Native Qt and installed artifacts keep separate gates.
The final Ruff-only formatting preserves the Python AST, with 65 targeted
Movie cases passing again and the same expected dependency branch skipped.

The first M4 tranche adds `await view.movie.export_async(...)` for the existing
version-2 tracks: MP4/H.264, WebM/VP9 and a lossless PNG/manifest ZIP. A
correlated job samples an exact rational constant rate, awaits a current
primary draw, captures one image, and encodes it before requesting another.
It has bounded waits, synchronous progress callbacks, cooperative owned-task
cancellation and atomic destination publication. Existing public signatures
are preserved; the new method is experimental.

The [export receiving record](../movie_export_receiving_20261110.json) retains
real encoder and molecular-browser evidence, runtime/source identities, resource
limits and diagnostic failures. Native annotations are captured. Visible DOM
plots/legends require explicit exclusion or cause refusal. This does not yet
receive composited overlays, all appearance/lighting channels, full static
baseline/rebase enforcement, target remapping/v1 migration, Studio authoring,
portable interactive web playback or the complete M5 story. Native Qt,
installed packages, other platforms and human observations remain separate.

The pre-1.0 result must let a user approach a known pocket, reveal a loaded
ligand with an explicit representation, show calculated interactions and labels
at chosen times, zoom out while rotating, and preserve/export the same story.
Generating a pose or new interaction analysis is a separate explicit scientific
operation, not an implicit side effect of playback.

The [first appearance tranche](../movie_appearance_receiving_20261110.json)
adds uniform colour/alpha, canonical simple representations, annotation text,
explicit RGB background and ambient/diffuse lighting to the same evaluator,
preview and export routes. It preserves region order and boundary bonds while
updating simple native representation nodes in place. The recipe records its
colour interpolation rule; Python/TypeScript numerical receiving and actual molecular browser/popup,
session and 720p video receiving have distinct scopes. Declared viewport
environment now travels in state/session files without making object Undo
restore earlier camera/environment settings. Broader renderer/style catalogues,
Studio, web and integrated M5 acceptance remain
open; this does not complete #320.

The [baseline tranche](../movie_baseline_receiving_20261111.json) adds
acknowledged live capture of a new empty plan and explicit recorded-scene reset
before time-zero keys. It preserves the scientific system/analyses and groups
restored object changes into one Undo step. Reset restores the state catalogue,
not arbitrary Mol* settings; unrecorded viewport/export preferences retain
state-import semantics. Its native receiving exposed #358's pre-existing
region-priority replay mismatch; restoration now declares saved priority
before creation/style, without a transient promotion. Broader renderer
catalogues, target mapping and M2/M4/M5 work stay open; the supported live
environment/rebase tranche is described below.

The [rebase tranche](../movie_rebase_receiving_20261111.json) adds a detached
change/conflict/candidate report and explicit acceptance with stale/edited
review rejection. It preserves keys and supplied scientific analyses. Live
application checks untracked serialized definitions while ignoring declared
navigation/editor/derived fields. #359 receives deterministic Movie layer
gating with baseline member intent and explicit member tracks, without
changing ordinary layer actions or issuing show-then-hide corrections.
This is source support for the recorded catalogue; it does not qualify all
arbitrary native defaults, Studio authoring or portable web playback.

The [observation tranche](../movie_observation_receiving_20261111.json) receives
the supported RGB background and ambient/primary-light intensities at the same
completed draw as camera/frame. It keeps declared intent separately, replays
observed constants alongside property tracks and preserves metadata in sessions.
`review_rebase_async()` adds explicit acceptance of the observed moment, with
one private per-view ticket, stale/edited rejection, no late publication after
cancellation and molecular/close disposal. #360 routes the screenshot through
the native task manager's declared isolated-context API. Richer renderer
catalogues, target mapping/migration and M2/M4/M5 work remain open.

### Studio authoring tranche — 2026-11-12

The [M2 design](../movie_timeline_design.md#studio-authoring-first-m2-slice)
has its first [source receiving](../movie_studio_receiving_20261112.json).
Local drafts, explicit typed keys,
bounded editor pages, revision checks, per-canvas live jobs, pause/cancel and
confirmed replacement/reset reuse the existing Movie API. The primary Python
API remains headless and composable; ordinary live Python calls still address
the primary canvas. The graphical adapter is private.

Real Chromium/Mol* with the persistent Python authority receives baseline
capture, typed structure/region keys, draft preservation, arbitrary-time seek,
canvas-popup camera capture and nested detached-Studio preview/pause/PNG export.
A genuine Python edit gates the kept draft until explicit review. The final
UI build passes 466 JS cases; the broader Python run passes 496 controls with
five explicit skips, followed by the final adapter's targeted regressions.
Five existing native Movie suites pass, including decoded 720p MP4 and sessions;
their unchanged Python owners and pre-final-UI byte scope remain in the receipt.
That bridge adapts widget transport; it is not an actual Jupyter kernel or
native Qt acceptance. Full authoring/accessibility review, the live Qt loop,
portable web playback, overlay composition and integrated scientific story
remain open. Do not mark M2 or
#320 complete from this slice. Human review and publication remain paused.

The [separate actual-Jupyter receipt](../movie_jupyter_receiving_20261112.json)
extends this slice through the real kernel/comm boundary and both Python/Studio
pause directions. #365 tracks transient scene admission and #366 loop-bound
completion/runtime projection. Their original failures and deterministic
controls remain; kernel/source/binary origins, native drawing, independent
session recovery, media and late-reply retirement are separately checked.
The admitted browser/actual-notebook source scope does not close the remaining
M2/M4/M5 or exact installed, hosted, Qt and human acceptance.

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
