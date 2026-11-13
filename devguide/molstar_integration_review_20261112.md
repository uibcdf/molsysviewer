# Mol* integration review — 2026-11-12

**Technical assessment delivered; dependency decision and complete qualification
remain open under [#369](https://github.com/uibcdf/molsysviewer/issues/369).**
The current integration makes substantial, appropriate use of Mol* rather than
reimplementing a renderer. Python-owned molecular meaning and scene state
justify most of the adapters. Two demonstrated build/type-check defects,
[#370](https://github.com/uibcdf/molsysviewer/issues/370) and
[#371](https://github.com/uibcdf/molsysviewer/issues/371), have scoped source
corrections and regressions. A general replacement of the API, Studio, context
menu or Movie architecture is not supported by this review.

There are useful improvements in published 5.13.1 and significant architectural
changes in v6 development. They are different migration choices. The
recommendation is to **qualify a controlled 5.13.1 migration before freezing
MolSysViewer 1.0**, subject to an explicit change of #115's existing deferral.
This is a recommendation to test and receive a concrete migration, not a claim
that 5.13.1 is already compatible or that v6 should enter the same release.
No dependency has been changed by this assessment.

## Sources and evidence

The [baseline inventory](molstar_integration_review_baselines_20261112.json)
records MolSysViewer `864df44dcc057a16c1eaec588c9b868a35b7671d`, installed
Mol* **5.4.1** / `74ff283e00a1254a45b9cd8ac80365b979e0e782`, published npm
**5.13.1** / `a4e9cc79415213263090ee47bf380d2a33e0118e`, and clean upstream
`master` / `dabbf29f952880a034a9637e28c9844e3ae73d9f` on the v6 development
line. The clone was refreshed again during this assessment and remained at
that commit. Original npm tarballs were independently checked against registry
integrity; inspecting them did not install another dependency.

The direct-import inventory covers all 117 production TypeScript files,
including 220 import/export declarations in 30 files and 77 native module
paths. It is not an exhaustive transitive graph. The runtime/TypeScript owners
are unchanged from that baseline; #370 changes build resolution and its tests.
The assessment starts from main `56b39d045bb773a252fbc93a44c5393bc99d5cc2`
and records its working changes separately in the
[receiving receipt](molstar_integration_review_receiving_20261112.json).

Upstream source, rather than a design's progress heading, determines what is
implemented. For example, the v6 plugin-composition design retains an old
"not implemented" introduction, while the current context, registries,
default-spec and migration map implement the changed composition. Neither
statement establishes published-package or MolSysViewer acceptance.

## Capability and ownership matrix

The following rows name actual consumer owners and assessed native mechanisms.
Benefits not measured below are opportunities, not performance claims.

| Area | Current MolSysViewer/native use | Published 5.13.1 and v6 differences | Disposition and acceptance owner |
| --- | --- | --- | --- |
| Molecular inputs and identity | `loaders/array_native_molsys.py`, `loaders/json_molsys.py`, `plugin/structure.ts` and `plugin/atom-indices.ts` build native `BasicSchema`, `Topology`, `Coordinates` and `Model` objects. Explicit source atom/group/chain indices survive native ordering. JSON and planar typed-array paths share reference-state bonds from `ChemicalStates`. | 5.13.1 includes CIF field/case, PDB caps/altloc and other parser corrections. Those matter to native string/URL routes; normal Python loads use MolSysMT conversion and explicit payloads. v6 relocates formats and adds explicit periodic models/boxes. | Retain MolSysMT conversion and correspondence owners. #269's received reference-state projection is not a promise of changing bond topology for every structure. Parser fixes do not justify replacing the molecular backend. Source identity, reordered/unassigned hierarchy and real format controls remain mandatory in #115's migration. |
| Representations and appearance | `state-handlers.ts` uses native registry providers, presets, themes, transparency and structure components. Python curates twelve molecular representation names, with advanced native parameter/theme escape hatches. `scene-handlers.ts` uses native lighting, fog, clipping and trackball settings. | 5.13.1 adds or improves coordination polyhedra, blob surfaces, surface interiors, marking composition and rendering paths. v6 adds explicit provider registration and a different graphics/backend architecture. | Preserve existing API/Studio choices and renderer reuse. A native name is not automatically a new portable public preset. New presets need scientific meaning, parameter validation, selection/state recovery and UI parity. No new preset is required to repair an already-promised 1.0 operation in the inspected scope. Keep opportunities with #115. |
| Molecular exploration | `active-selection.ts`, measurement tools and the controller consume native `Loci`, `OrderedSet`, picking and focus/reset operations. Source mappings and group terminology bridge Python to native groups. Camera authority and completed-draw handling belong to MolSysViewer. | 5.13.1 improves picking, marking, camera events, easing and optional less-obstructed focus/zoom-out. v6 changes selection/annotation facilities and UI composition. | Native focus improvements are useful migration candidates. They cannot replace authority revisions, completed-draw barriers or source identity with a pose-change notification. Preserve transparent-shape picking and zero-opacity ownership masks. Receive current selection/context-menu/popup controls under the selected engine. |
| Scientific visual content | Shapes use native `MeshBuilder`, `Lines`, text geometry, representations and state transformers. Centroid measurements use native distance/angle/dihedral renderers with explicit geometric endpoints. Interactions use native cylinder/shape geometry over MolSysMT occurrence records and periodic endpoints. | Native `CustomInteractions`/`InteractionsShape` already exist in 5.4.1. Their finite kinds and two endpoint schemas are not the complete sparse analysis/coverage/participant/provenance contract. 5.13.1 also has native water-bridge detection; v6 expands labels/MVS. | Keep scientific results and detectors in their scientific owner. Do not replace Buch or another MolSysMT method implicitly. The current interaction adapter is justified; it preserves parallel occurrences, roles, centroid-guide labels and evaluated-empty/unevaluated coverage. MVS table-driven labels/colours/tooltips remain a valuable separately scoped #44 opportunity, not a required rewrite of current callouts. |
| Structures and motion | `trajectory-handlers.ts` uses native trajectory transforms and models; planar axes are subarray views. It owns the qualified cadence, serialization and dependent geometry convergence. `movie-timeline.ts` reuses native vector/quaternion math for the shared, independently evaluable Python/TS story model. | 5.13.1 improves model-property reuse and offers additional native animation controls. v6 introduces periodic frame transforms, no-jump/whole modes and bounded caches. Procedural wiggle/tumble is illustrative motion, not molecular dynamics. | Preserve the typed transfer, frame-query and Movie owners. The current path materializes the transferred trajectory; it is not public out-of-core loading. v6 whole/periodic defaults must not change supplied coordinates or the frame for scientific queries implicitly. Lazy/periodic visualization needs an explicit contract and corresponding index/image tests under #115. |
| Preservation and output | Python owns scene/selection/source identities, named analyses and H5MSM session persistence. Native image passes render PNG/Movie frames; the common projector builds popup/static scenes. The Movie evaluator and overlay compositor preserve scientific context through PNG/MP4/WebM/offline HTML. | 5.13.1 changes rendering/marking passes and has headless-rendering fixes. v6 changes image/backend interfaces and supplies additional native/MVS story facilities. Native snapshots do not contain MolSysViewer's complete Python/scientific unit. | Keep native image rendering, without substituting a Mol* snapshot for a MolSysViewer session. #320's integrated story remains applicable only to its recorded current-source scope. A migration must requalify appearance, measurements, overlays, camera-facing text, codecs, offline playback and session recovery; availability of native MP4/MVS export is not equivalent acceptance. |
| Lifetimes and resources | Native tasks, transforms, representation/GPU resource owners and context disposal are reused. Local seams address component-cache key lifetime (#356/#363), unchanged font uploads (#344) and per-render camera-facing presentation. | The executed native `State` control distinguishes 5.4.1 callback omission from 5.13.1 cleanup. The original default font pixel array is about four times larger in 5.13.1. v6 adds shared font textures/dirty rows, a bounded atlas cache and major graphics changes; the inspected component-name memoization still needs follow-up. | Retain byte/version guards and actual GPU/CPU lifetime tests. Do not remove repairs because a newer version exists or treat stale resource counters as physical liveness. #115/#363 own replacement qualification; #315/E2 and MolSysMT #723 retain their broader metrology/prolonged-use scope. |
| Hosts and Python integration | One controller/runtime supports notebook, canvas popup and detached Studio. Python owns the molecular authority; different canvases deliberately have separate native contexts and correlate camera/scene intentions. Qt is an experimental host of the same scene/runtime. | v6 Prism, command/AI facilities and headless/backend composition offer future integration ideas, but are a different application and package architecture. A new native camera event does not provide cross-window ownership or Python authority. | Retain the shared MolSysViewer shell and Python API. No UI/framework/agent replacement is adopted. Select useful native engine facilities behind existing owners. Qt, actual notebook, popup, installed and human observations keep their distinct acceptance; source inspection does not qualify those hosts. |

## Executed comparisons and consequential findings

Native `CustomInteractions` could be evaluated as a rendering adapter without
replacing the scientific store. It is not a drop-in replacement here: its
inputs address structure-selection endpoints, whereas the current shared
network renderer also accepts explicit periodic-image coordinate pairs and
participant-centroid guides with occurrence metadata. The existing path already
uses native mesh/cylinder primitives. A replacement would need a concrete
reduction in adapter complexity while preserving those meanings, selection and
frame/lifecycle behavior; the mere presence of a native interaction extension
does not establish that benefit.

### R1 — build provenance: required pre-1.0 correction

The old `tsconfig.json` maps `molstar/lib/*` to a sibling `src_molstar` tree.
Without that tree, builds use installed 5.4.1. With a controlled stale source
module, the same runtime, unit and harness scripts succeed with the alternate
source and omit the qualified native cache repair. Run `670` reproduces all
three routes; the new regression in `671` fails all three before the fix.

[#370](archive/molstar_implicit_source_override.md) removes that implicit
override and corrects the local inspection/build instruction. The original
dependency stays installed. The complete build/version test module passes
13 cases in `672`. The regression uses the real configuration and scripts,
the installed native package and a deliberate source-origin fault; it does
not merely assert that a JSON key is absent. The current runtime bundle has
not been regenerated or changed by this config-only correction.

### R2 — published-v5 migration: a concrete renderer contract change

The same TypeScript compiler checks all 117 production files against actual
native declarations. Installed 5.4.1 has zero diagnostics. With original
5.13.1 declarations substituted in an isolated lookup root, it reports
`TS2554` at `plugin/render-presentation.ts`: native `Renderer.update` now
requires `(camera, scene, frame)`, while the current wrapper forwards two
arguments. Child exits **0** and **2** are retained separately in `669`;
the comparison driver's successful completion is not a compatibility pass.
The initial `668` fails because the exploratory script has an incorrect
TypeScript module path; that original is retained and is not a product defect.

An upgrade must forward the complete native argument tuple and preserve the
receiver and presentation-before-render ordering. A type-only pass after
that change would still not prove image, picking or native-frame correctness.
The probe retains the canonical `skipLibCheck` profile and existing external
dependency closure; zero or one diagnostic is not an exhaustive list of runtime
migration requirements. The build's cache repair intentionally rejects
unreviewed Mol* versions too.
These are concrete #115 migration tasks, not reasons to weaken those guards or
change the currently received runtime speculatively.

### R3 — lifecycle: real native difference, bounded consumer control

Run `673` builds original native `State`/`StateTransformer` code. Two live
child objects receive **zero** dispose callbacks from 5.4.1 `State.dispose()`
and **two** from 5.13.1. Explicitly removing those children before disposing
invokes both callbacks in both versions. This receives the native behavior
change documented upstream. It does not prove a MolSysViewer memory leak or
measure an improvement in process RSS.

The actual pentalanine control additionally loads a molecular representation,
sphere, label and measurement through the canonical Python projection and
current controller. After a completed native draw, `675` observes **527** live
WebGL objects; controller disposal leaves **zero**, with context loss and no
page errors. It observes real `create*` results and native `isBuffer`,
`isTexture`, etc., preserving their original execution. It is a bounded
Chromium/WebGL receiving, not actual Jupyter/Qt or universal resource release.

The original `674` incorrectly required `stats.resourceCounts` to reach zero.
Native global resource destruction calls the raw resource destructors rather
than the wrapping count decrements; nonzero counters survive even when the
actual objects are dead. The original failure and the physical diagnostic
remain. No leak is closed or newly alleged from that counter alone. Broader
CPU/backing-buffer and prolonged-host acceptance remains with #315/E2 and the
existing lifetime work.

### R4 — label quality has a measured allocation cost

Run `676` constructs the actual default `FontAtlas` in real Chromium Canvas2D
using each original public package, requests a glyph and observes its native
pixel array. Both use the named quality **3**:

| Native package | Width × height | Pixel-array bytes |
| --- | --- | ---: |
| 5.4.1 | 3,287 × 3,286 | 10,801,082 |
| 5.13.1 | 6,565 × 6,564 | 43,092,660 |

The source doubles the base font size from `32 * (quality + 1)` to
`64 * (quality + 1)`. This measured array is approximately four times larger.
It is not a whole-process peak, an allocation for every label, a GPU-byte
measurement or a comparison of perceived image quality. A migration needs an
explicit font-quality/resource decision and tests of existing/default/user
styles. Do not promise lower memory from an upstream performance changelog.
The newer public source still does not justify dropping #344's upload seam;
v6 shared/dirty-row uploads retain their separate published-artifact follow-up.

### R5 — v6 is a separate architectural/scientific migration

The current source and migration map relocate the 5.x module families into
layered ESM packages; the old `StateTransforms` facade maps to `null` and
individual transforms move to their defining modules. `PluginContext` builds
explicit registries and registers the supplied entries. `DefaultPluginSpec`
is a distinct default-composition entrypoint. Import renaming alone is
insufficient: missing providers may normalize to defaults and produce a
plausible but different picture.

The inspected hierarchy also applies periodic model/frame helpers, with
whole/box/no-jump facilities that can move displayed atoms. These may be
useful, but require explicit coordinate/image semantics, query applicability,
pick/measurement correspondence and session recovery in MolSysViewer.
The current raw row-vector box owner must not be replaced with an inference
from cell lengths/angles or an unannounced periodic transform. v6 graphics,
text caching, WebGPU and Prism features are development mechanisms, not a
qualified replacement engine for this release.

### R6 — standard project library declarations

The final ordinary project check also exposes a separate pre-existing
configuration discrepancy: `Object.hasOwn` in Movie requires ES2022 library
types, while the checked-in project implicitly used ES2019 libraries. Earlier
strict commands explicitly selected ES2022. Original `677` retains that native
TS2550 failure. [#371](archive/typescript_project_standard_libraries.md)
declares the actual standard and DOM libraries, keeping the ES2019 emission
target. Its regression compiles the real project with no target/lib override.
This changes neither runtime source nor browser/polyfill availability.

## Disposition ledger

| ID | Decision/status | Owning follow-up |
| --- | --- | --- |
| R1 | Required pre-1.0; source correction and real-build regression received. | #370; this review's receipt and applicable hosted/candidate gates remain separately scoped. |
| R2 | A controlled 5.13.1 qualification before freeze is recommended; changing the existing migration timing is pending the maintainer's decision. No dependency change yet. | #369 decision; #115 migration scope/lifecycle. |
| R3 | Include native callback/lifetime behavior in that qualification. Current physical WebGL control passes; broader acceptance stays open. No universal leak/performance claim. | #115, #315/E2, #356. |
| R4 | Measure and decide default/explicit font quality during migration; retain native glyph/upload/context-restoration controls. | #115 and #344's qualified adapter/retirement contract. |
| R5 | Defer v6 engine, explicit-registry/backend and periodic-transform migration. Do not bundle it into a v5 dependency change. | #115's separately scoped future evolution; #363 owns cache-fix monitoring. |
| R6 | Required pre-1.0; align ordinary project library declarations and protect the real project check. | #371; final validation in the review receipt. |
| O1 | Keep the current native-backed shape, measurement, occurrence and scene owners; no wholesale replacement is justified. | Existing scene/interaction contracts, #320 and #264. |
| O2 | Table-driven MVS labels/colours/tooltips remain useful future interoperability, without replacing present callouts. | #44 retains its explicit post-1.0 scope. |
| O3 | New native presets, volumes, procedural motion and optional focus profiles need an explicit user-facing contract before adoption; none is silently advertised by this review. | #115 capability review; science/preparation remain with the owning library/add-on. |
| O4 | Keep Python-first host integration and MolSysViewer's shared UI; no Prism/framework/AI dependency is adopted. | Core/add-on boundary and existing host contracts; remote preview remains #100. |

## Concrete migration proposal for the maintainer

The existing #115 decision is **"The migration stays post-1.0."** The new
evidence supports reviewing that timing, rather than changing it implicitly.
Choose between qualifying public **5.13.1 before 1.0** and retaining qualified
**5.4.1 for 1.0** with the existing later migration. v6 is not part of either
immediate option. The recommended first option has this reviewable scope:

1. Record the timing decision and its issue lifecycle; preserve the current
   source/package identities and an explicit recovery route.
2. Select the already inspected public 5.13.1 artifact. Align package/lock and
   actual Node build requirements (`>=22` upstream); do not infer an engine
   upgrade from a pull in the external clone.
3. Forward the native renderer argument tuple. Review rendering/marking/image
   ordering, version/byte-checked component repair and font upload adaptation.
   Preserve required repairs until their native replacements are received.
4. Decide font quality from actual legibility and resource measurements,
   preserving explicit user choices. Compare surfaces, clipping, transparent
   images, picking and label geometry by their scientific/visual contracts.
5. Receive the unchanged public Python scene, source/structure indices,
   reference-state bonds, native measurement/interactions, popup synchronization,
   camera authority, session/H5MSM recovery and complete Movie story.
6. Complete the applicable JS/core browser, actual-host/lifecycle/prolonged,
   exact-source/platform and installed-candidate gates. Preserve failures and
   diagnose them; do not relax assertions to accept a changed result.
7. Reconcile documentation and native-parameter compatibility claims before
   candidate freeze. Public tags/packages/both 1.0 releases retain their
   separate authorization.

Benefits are concrete native cleanup and visual/parsing corrections, with
additional useful renderer capabilities. Costs are cross-cutting rendering
qualification, retained compatibility seams, different default font allocation
and potential visible changes. No measured frame-rate gain or smaller RAM
footprint is claimed. Keeping 5.4.1 is technically possible with the existing
repairs and acceptance route; the review does not manufacture an urgent failure
to force an upgrade.

## Source references and scope limits

- [5.13.1 changelog](https://github.com/molstar/molstar/blob/a4e9cc79415213263090ee47bf380d2a33e0118e/CHANGELOG.md)
  supplies versioned evolution; the actual renderer/State/font probes above
  separately receive consequential mechanisms.
- [5.13.1 renderer](https://github.com/molstar/molstar/blob/a4e9cc79415213263090ee47bf380d2a33e0118e/src/mol-gl/renderer.ts),
  [State](https://github.com/molstar/molstar/blob/a4e9cc79415213263090ee47bf380d2a33e0118e/src/mol-state/state.ts)
  and [font atlas](https://github.com/molstar/molstar/blob/a4e9cc79415213263090ee47bf380d2a33e0118e/src/mol-geo/geometry/text/font-atlas.ts)
  are the inspected source contracts.
- [v6 migration map](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/.v6/plans/migration-map.json),
  [context](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/packages/plugin/core/src/context.ts),
  [periodic hierarchy](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/packages/plugin/core/src/state/transforms/structure/hierarchy.ts)
  and [font atlas](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/packages/graphics/src/geo/geometry/text/font-atlas.ts)
  support the development assessment, not a v6 compatibility claim.

The receipt retains raw results, source hashes, original failed controls,
resource limits and private evidence custody. Reused current Movie and
capture/lifetime receiving keeps its original commit/byte scope; it is not
relabeled as 5.13.1 qualification. Covering CI, installed artifacts, postponed
human observations and the remaining 1.0 programme are not cleared by this
technical assessment. The original audit counters remain unchanged.
