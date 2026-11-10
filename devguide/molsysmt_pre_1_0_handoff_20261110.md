# MolSysViewer feedback for MolSysMT

Consumer review for MolSysViewer #315 and MolSysMT #250, #254, #256, #524
and #615. This review uses MolSysViewer source
`25f482ae0f2145dd4a203287c82ce158beb78a5e` and MolSysMT's coordination
record at `af32a559cc6bac6d0e33ee249b3692319028add3`. Each receiving result
below retains the exact pair on which it ran.

## Interactions and ChemicalStates

We accept the current source contract for our consumer. Sparse relations and
occurrences let us inspect and draw observations for the visible structure.
Compound participants and explicit roles determine the geometry. Parallel
observations require `occurrence_indices` scoped to one version of an analysis.
Filtered queries and persistence preserve those references. Remapping or
replacement may produce new indices. Nonconsecutive structure requests retain
their order after deduplication. MolSysViewer consumes `involving_selection`,
`within_selection`, `across_selection_boundary` and `between_selections` with
the declared selection and coverage semantics. Evaluated-empty coverage applies
only to the evaluated search scope. An unevaluated frame remains distinct.

Keep compact inspection pages with aligned measures, units, evidence,
producer metadata and periodic image vectors. Page bounds apply to occurrence
and participant copies after query construction. We draw relative to the first
participant using the documented row-vector box convention. Missing image data
means the periodic copy is unknown. One vector moves a compound participant
together. Named analyses, declared atom and structure maps, remapping and
structure-specific invalidation let us retain independent results and refuse
stale edits. On importing an independent H5MSM analysis, the user declares
correspondence. Source IDs and maps carry provenance. Raw array writes require
explicit invalidation. We rely on materialized analyses and bounded inspection
for the current workflows. Detector profiles and the page API remain experimental.
The [scale receiving](performance/robustness_scale_receiving_20261110.md)
covers synthetic reuse and churn and a real 62-atom, 5,000-structure Buch case.
The [scientific session receipt](molsysmt_analysis_receiving_20261106.json)
covers exact stored observations and recovered evaluated coverage. MolSysMT
#666 remains the separate exact-cutoff question for geometric contacts.

We accept independent native ChemicalStates for #254. Topology supplies the
molecular inventory. MolSysViewer reads covalent connectivity from the explicit
reference chemical state for both JSON and array-native projections. A declared
nonzero reference works and an ambiguous reference is rejected. Absent states,
unknown connectivity and known-empty connectivity retain their native meaning.
MolSysViewer reads bonds through `molsys.chemical_states.get_bonds(chemical_state="reference")`.
It requests component indices and names via public `molsysmt.get` on MolSys,
which resolves the ChemicalStates-owned component data. Active selection omits
component membership when there is no chemical state. Operations that require
chemistry pass the domain explicitly. The provider owns atom/structure remapping
and associations, and MolSysViewer applies the declared maps to its scene. The current
viewer renders a static reference-state graph.
We found no new incompatibility in the exercised source paths. The original
hosted campaign and its separate Linux recovery are recorded in
[ChemicalStates receiving](chemical_domain_receiving.md).

## H5MSM version and session assumptions

MolSysViewer delegates molecular file loading to the public MolSysMT form APIs. A
MolSysViewer session ZIP has its own manifest version and embeds `structure.h5msm`.
The current writer calls `msm.h5msm.write` without a `format_version` override.
On reopen, sessions with named-analysis signatures use `msm.h5msm.read`.
Other sessions use `msm.convert` to MolSys. The interaction-only routes use
public `read_layers` and `write_layers`, also without a writer override.
Thus the bundled file version follows the provider's default and the input
file's schema is not carried forward as a setting of the View. The legacy
session writer fallback remains relevant only when the public writer is absent.
[Session implementation](../molsysviewer/session.py) and
[interaction file implementation](../molsysviewer/interactions.py).

MolSysViewer's restore checks depend on the ordered molecular binding, the precise
coordinate and reference-state data used by the scene, and the names and
signatures of its analyses. Those signatures require roles, observations,
coverage, units, producer data, maps and periodic images to survive the round
trip. A partial file contributes only a named analysis to an existing View
with `assume_aligned=True` and optional explicit axis remapping. The target
coordinates and system identity are retained. Writer refusal protects a session
when the default schema cannot represent the supplied domains.

The bounded source probe `279` on MolSysViewer `4f05a6c6ea3f7ca78929e9f2592360f0e6ae38fa`
and the MolSysMT review head `66273e4d3ad722726336055b4bf38dc76761e35e`
checks 62 atoms over reordered structures `[4999, 0, 73]`, 36 periodic Buch
occurrences and an empty disulfide analysis with its own evaluated coverage.
Both full 0.5 and explicit experimental 0.6 inputs open. Each saves a session
whose embedded structure has H5MSM version 0.5 and reopens with exact
coordinates, reference bonds, components and both scientific analyses. Each
format's interactions-only input attaches to the existing system and preserves
its coordinates. This fixture carries no mechanics layer. The probe exits
zero in 7.74 s at 1 CPU, with 10,905 unchanged selected inputs.

For #256 we support a first stable H5MSM 1.0 boundary. Repeat those two routes
with the actual stable reader and writer, verify the embedded version, retain
old-session read coverage and add a scoped edit to verify selective analysis
invalidation. Verify declared correspondence, domain absence, units and
producer identity after reopening. If stable 1.0 also carries mechanics, check
that save/reopen preserves those stored data even where MolSysViewer does not draw
them. Keep the prior formats and experimental scientific profiles within
their established scopes.

## Versions for installed qualification

The official GitHub Releases and Anaconda file inventory on 2026-11-10 show
MolSysViewer **0.24.0 noarch build 1** and MolSysMT **0.23.0 ABI3 build 0** as the
newest public releases and `main` artifacts. Their sixteen installed cells
qualify the historical pair. MolSysViewer 0.24.0 lacks the `MolSysView.closed`
lifecycle required by the redesigned MolSysMT tools addon. The old MolSysViewer
0.24.1 builds and the four older MolSysMT 1.0.0 build 0 files remain in staging.
The redesigned addon and current independent-domain integration have **no
qualified public pair**. Keep the existing ordinary MolSysViewer dependency floor
`molsysmt>=0.23.0` in its demonstrated scope. [Installed qualification](installed_artifact_qualification.md)
and [MolSysMT #524](https://github.com/uibcdf/molsysmt/issues/524) record the two directions.

The maintainer confirmed that **MolSysMT 1.0.0 and MolSysViewer 1.0.0 will be
released together**. This is the pair for final installed qualification.
The earlier MolSysViewer 0.25.0 proposal concerns a possible pre-1.0 milestone
and has no qualified public artifact. The minimum version supporting the
redesigned addon remains to be verified under #524.

When candidate work resumes, agree clean source SHAs and supported capability
scopes, then record versions, build strings, channels, dependency closure and
hashes of the original artifacts. Qualify the exact 1.0.0 pair outside both
source trees in the sixteen Conda cells, checking actual imports, addon
discovery, lifecycle and the scientific/session routes. Include supported
minimum and newer dependency routes where applicable. Establish any published
addon floor from clean installed evidence. Qt retains its experimental host
qualification. Candidate preparation and publication remain paused.

## MolSysMT #615 first-canvas evidence

The original Analysis attempt timed out after the existing 30-second wait.
The cell appeared executing and the original 45-second stack timer left an
empty trace. The diagnostic pass with a 15-second timer completed its initial
cell in 3.357631 seconds. Eleven later Jupyter scenarios passed on another
recorded pair. MolSysMT's newer `/api/sessions` observations occurred after the
browser retired and therefore describe that later state. Keep the original
failure and the distinct cold-server case #705. [Owner report](https://github.com/uibcdf/molsysmt/issues/615)
and [MolSysViewer receipt](molsysmt_analysis_receiving_20261106.json) retain the evidence.

We propose one bounded Analysis diagnostic on a recorded source pair when a
targeted run is needed. Reuse `system_panel_jupyter.py` and
`analysis_panel_jupyter.mjs` with the original 1TCD cell and canvas deadline.
Arm a small trace before clicking Run. Record the last observed stage on both
sides of the widget handoff.

| Stage | Evidence before teardown |
| --- | --- |
| Notebook execution | Record Run submission, initial-cell start, boundaries around imports, 1TCD loading and the display hook, and completion or exception. Keep the existing flushed 15-second kernel stack. |
| Kernel and widget transport | Sample the isolated server session state at about 15 seconds and at the canvas timeout while the browser is still connected. Record the display and widget comm acknowledgement or first bootstrap event for this view, when observed. |
| MolSysViewer rendering | Record widget mount, connected canvas and controller identity, expected 3,983-atom scene registration, and the first new native Mol* draw after registration. Record the viewport and any bounded render error when the wait fails. |

Use monotonic elapsed times and a local correlation label. Retain bounded
metadata and keep kernel traces in private custody. The earliest missing
transition narrows the next investigation only when its observer was active.
Capture failure evidence before browser retirement with finite diagnostic
requests. Preserve the existing deadline, assertions, cold imports and kernel
lifecycle. MolSysViewer owns the mount/scene/draw observations. MolSysMT owns the
Analysis runner and the kernel/server observations. A causal repair or an
evidenced environment-specific disposition is still required to close #615.

## MolSysMT #705 server preparation

[Draft PR #706](https://github.com/uibcdf/molsysmt/pull/706) at
`66273e4d3ad722726336055b4bf38dc76761e35e` retains the 20-second default and
accepts a finite explicit `--server-ready-timeout` greater than zero and at
most 300 seconds. The 25 CLI/runtime-file tests in probe `256` pass, with the
readiness implementation retained at the stated PR head. The actual
same-kernel campaign `265` reaches authenticated server readiness in 9.56 s
with a 90-second configured budget. The earlier `248` timeout at 20.04 s
and all scope distinctions are in the
[receiving receipt](prolonged_scientific_session_receiving_20261110.json).
The 30-second first-canvas wait under #615 and the scientific deadlines retain
their own contracts. PR review belongs to MolSysMT.
