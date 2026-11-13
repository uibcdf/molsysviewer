---
summary: Reassess Mol* integration against current releases and development before 1.0.
issue: uibcdf/molsysviewer#369
status: active
opened: 2026-11-12
closed:
verification: measured
area: [architecture, frontend, dependencies, rendering]
guard:
normative:
blocked_by: []
supersedes: []
---

# Mol* integration and capability review before 1.0

**Technical assessment delivered; 5.13.1 qualification adopted before 1.0
under [#372](qualify_molstar_5_13_1_pre_1_0.md), still open before the
documentation-review handoff.** The
[dated review](../molstar_integration_review_20261112.md) contains the eight-area
matrix, measured comparisons, dispositions and a concrete migration proposal.
The principal maintainer adopted this requirement on 2026-11-12:
the original implementation review is old enough to warrant a comprehensive
reassessment of how MolSysViewer uses Mol*. Recent focused source investigations
remain useful evidence, but do not establish that the complete integration is
current, efficient or making appropriate use of upstream capabilities.

The owning issue is [#369](https://github.com/uibcdf/molsysviewer/issues/369).
The [1.0 closure route](../path_to_1_0.md#closure-route) and
[robustness programme](pre_1_0_robustness_audit_and_action_plan_20261106.md)
include this additional requirement. It does not alter the original 46-outcome
denominator or count as delivered work merely because this record exists.

## Questions the review must answer

Are we using Mol*'s potential and architecture effectively? Which integration
assumptions or custom mechanisms have become obsolete? Which newer capabilities
would materially improve the user experience, scientific visualization,
correctness or performance before 1.0? Which should be deferred or rejected,
with an explicit reason?

## Baseline and import inventory received — 2026-11-12

The [source-bound inventory](../molstar_integration_review_baselines_20261112.json)
freezes MolSysViewer `864df44dcc057a16c1eaec588c9b868a35b7671d` after the
integrated Movie story. The clean upstream checkout was refreshed with
`git pull --ff-only`; it was already current. No dependency, runtime or
environment was changed. Human sandbox work remains preserved.

| Baseline | Exact identity | Evidence boundary |
| --- | --- | --- |
| Declared/locked/installed | `^5.4.1` / `5.4.1` / `5.4.1`; source `74ff283e00a1254a45b9cd8ac80365b979e0e782` | Fresh registry metadata, original tarball SHA-512 integrity, exact tag/source and selected installed declaration/JS bytes agree. Runtime bundle hash is retained separately. |
| Latest published npm | `5.13.1`; source `a4e9cc79415213263090ee47bf380d2a33e0118e`, tag `v5.13.1` | Fresh npm `latest` metadata independently revalidates the previously preserved original tarball. This is artifact inspection, not MolSysViewer compatibility. |
| Upstream development | `master` at `dabbf29f952880a034a9637e28c9844e3ae73d9f`, committed 2026-11-09 | Clean refreshed checkout and fetched `origin/master` agree. Its v6 ESM/workspace design is a separate migration, not the public 5.13.1 package. |

The TypeScript compiler API scanned all **117** production `.ts` files under
`molsysviewer/js/src`: **220** direct import/export declarations across **30**
files address **77** distinct Mol* module paths. Every resolved declaration
and its JS sibling matches the original 5.4.1 tarball. All **154** paths exist
in 5.13.1; **91** have different bytes. These are inventory facts, not evidence
of compatible signatures, behavior or a safe version bump. Literal dynamic
imports are included; the transitive graph and nonliteral loading require
their separate source review. Build-time compatibility adapters also need
their own assessment rather than being mistaken for installed native bytes.

The first source reading identifies these consequential comparisons to make:

- The renderer/image-pass interception in `plugin/render-presentation.ts`
  must be traced against newer separate marking/render passes. Existing
  capture receiving is for the current runtime; it cannot qualify another one.
- Native cell disposal, font-atlas and component-property caching need review
  against the explicit local lifecycle repairs and #344/#356/#363 controls.
  A newer release number alone does not justify removing them.
- Native camera focus, surface/clipping, labels, picking and parsing have
  received relevant changes since 5.4.1. Determine which affect actual
  MolSysViewer paths, which supply a useful visual improvement, and which are
  bypassed by MolSysMT-owned preparation and data conversion.
- v6 changes package paths, explicit registry composition and the
  `StateTransforms` facade. The current default-plugin/deep-import integration
  therefore needs a migration assessment beyond renaming one dependency.

These were the baseline-stage hypotheses and migration boundaries. The dated
assessment below now addresses them, including the demonstrated #370 build
defect and its source correction. #369 stays open through adopted work; the maintainer has now advanced the
5.13.1 qualification under #372. #115 retains future v6/evolution scope and
the original 46-outcome counter is unchanged.

## Execution plan

The assessment and [receiving](../molstar_integration_review_receiving_20261112.json)
now receive steps 1–5 in their stated scope. They identify and correct #370's
implicit build-source override, reproduce a 5.13.1 renderer signature change,
compare native State disposal and actual font allocation, and distinguish
physical WebGL teardown from stale counters. Source build regression passes
13 cases in its original receiving; the final gate adds #371's ordinary
project type check and library-declaration correction. A new runtime or
installed qualification has not been claimed.
The principal maintainer accepted controlled 5.13.1 qualification before
freeze on 2026-11-12. [#372](qualify_molstar_5_13_1_pre_1_0.md) owns execution
and exact receiving; #115 retains later v6/evolution scope. Step 6 and parent
closure remain pending adopted qualification, not a timing decision.

1. Freeze the exact MolSysViewer source and resolved Mol* dependency/artifact.
   Refresh `~/repos@others/molstar` while preserving local work. Independently
   identify the latest published release at execution time and its tag/source
   commit and npm integrity. Record the development branch/commit/date as a
   separate baseline. A local clone, floating branch or release note is not
   evidence of the running dependency's implementation.
2. Inspect relevant source, migration/release notes, development documentation
   and existing upstream audits. Map the actual imported/extended interfaces,
   their native owners, stability and lifecycle assumptions. Read TypeScript
   sources; generated runtime bundles are not review sources.
3. Produce the capability/ownership matrix below. Identify existing useful
   functionality, unnecessarily duplicated machinery, missing improvements and
   consequential differences in the latest release/development source.
4. Evaluate each actionable item by user scenario, benefit, scientific meaning,
   effort, migration risk, performance/resource cost and applicable acceptance.
   Record one disposition: required pre-1.0 correction, adopted pre-1.0
   improvement, deferred post-1.0, or not adopted. Open/link owned follow-ups;
   unsupported impressions are not findings of fact.
5. Execute bounded, informative comparisons for consequential hypotheses.
   Reuse real molecular/browser guards and the scientific/scene owners.
   Distinguish inspected code, executed source receiving, installed artifact
   qualification and human observations. Apply the shared resource policy.
6. Integrate and qualify adopted pre-1.0 work, or obtain an explicit evidenced
   disposition. Reconcile the dependency decision, contracts, API/UI parity,
   documentation and current readiness record before the handoff.

## Capability/ownership matrix to produce

Each row must name the installed/released/development mechanisms and exact
sources, MolSysViewer's current owner/adapter, gaps or unnecessary duplication,
concrete user benefit, scientific/compatibility constraints, evidence, decision
and follow-up issue. The following is the review scope, not a finding that all
these capabilities should be added.

| Area | Required assessment |
| --- | --- |
| Molecular inputs and identity | Formats, assemblies/symmetry, atom/group/source maps, reordered or partial systems and chemical metadata |
| Representations and appearance | Representation catalogue, materials, colour themes, lighting/postprocessing, clipping, surfaces and volumes where useful |
| Molecular exploration | Selection, picking, granularity, highlighting, focus and coordinate/periodic conventions |
| Scientific visual content | Shapes, measurements, annotations/MolViewSpec and interaction visuals; scientific ownership and result/representation separation |
| Structures and motion | Trajectory/data transfer, binary/lazy paths, camera, animation, scheduling and completed-draw semantics |
| Preservation and output | Scene/session reconstruction, PNG, Movie/video, portable web, native assets and provenance |
| Lifetimes and resources | Async tasks/cancellation, caches, CPU/GPU ownership, disposal, memory/performance and context restoration |
| Hosts and API integration | Python-first composability, notebook and both popup paths, experimental Qt and relevant consumer embedding needs |

Preserve [the core/add-on boundary](../core_and_addon_boundary.md): MolSysMT
owns molecular science and preparation; MolSysViewer owns visualization and
exploration. A native Mol* facility must not silently change units, indices,
periodic geometry, interaction meaning or a scientific method. Adopting a visual
feature must not weaken the Python API, persistence or scene ownership to make
one GUI flow easier.

## Existing decisions and evidence

- The maintainer explicitly advanced public 5.13.1 qualification before 1.0
  on 2026-11-12; [#372](qualify_molstar_5_13_1_pre_1_0.md) owns that migration.
  [#115](post_1.0/update_molstar_dependency.md) retains future v6/evolution
  scope. Acceptance of timing is separate from passing migration gates.
- [#363](molstar_component_cache_upstream_followup.md) tracks the published
  component-cache correction and eventual local-repair retirement; #356 keeps
  its consumer lifetime requirements. #344 and the font/capture investigations
  keep their original exact-source and receiving scopes.
- [#44](post_1.0/annotations_mvs_machinery.md) retains the advanced MolViewSpec
  proposal. Reassess its value without claiming it is already implemented or
  automatically changing its scope.
- #320 Movie/export and #264 scientific/add-on integration are consumers of
  the reviewed architecture. The review can proceed alongside that work and
  must finish early enough to influence the architecture/candidate freeze.

## Required closeout

The dated review must identify all three baselines, provide the completed
matrix and supported conclusions, preserve uncertainty and classify every
actionable finding. Adopted pre-1.0 follow-ups need their appropriate executed
acceptance or an explicit scoped disposition. A report alone cannot clear
unresolved required work. Update the 1.0 plan and API/user/developer claims to
match the decisions. Do not treat build success, source inspection or a newer
version number as installed compatibility or scientific qualification.

Opening this issue changes no dependency, runtime, scientific API or release
authorization. Tags, packages, promotions and both 1.0 publications remain
subject to their existing pauses and separate approval.
