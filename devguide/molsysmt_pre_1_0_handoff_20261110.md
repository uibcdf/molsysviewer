# MolSysViewer feedback for MolSysMT

Consumer review for MolSysViewer #315 and MolSysMT #250, #254, #256, #524
and #615. This review uses Viewer source
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
their order after deduplication. Viewer consumes `involving_selection`,
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
molecular inventory. Viewer reads covalent connectivity from the explicit
reference chemical state for both JSON and array-native projections. A declared
nonzero reference works and an ambiguous reference is rejected. Absent states,
unknown connectivity and known-empty connectivity retain their native meaning.
Operations that require chemistry pass the domain explicitly. The provider
owns atom/structure remapping and associations, and Viewer applies the declared
maps to its scene. The current viewer renders a static reference-state graph.
We found no new incompatibility in the exercised source paths. The original
hosted campaign and its separate Linux recovery are recorded in
[ChemicalStates receiving](chemical_domain_receiving.md).

For #256 we support the first stable H5MSM 1.0 boundary once the public reader,
writer and migration routes pass on the intended pair. Our bounded receiving
should include a complete system with reference chemistry and a named periodic
analysis projected onto nonconsecutive structures, followed by session reopen
and an edit that invalidates only its declared coverage. A partial-file case
should preserve domain absence and maps, and exercise explicit correspondence
when attaching an independent analysis. Reuse the 0.5 and explicit 0.6 evidence
under their original versions. Keep the producer identity and measure units on
recovery. The Viewer projection does not require new mechanics visualization or
a promotion of the experimental scientific profiles.

## Versions for installed qualification

The official GitHub Releases and Anaconda file inventory on 2026-11-10 show
Viewer **0.24.0 noarch build 1** and MolSysMT **0.23.0 ABI3 build 0** as the
newest public releases and `main` artifacts. Their sixteen installed cells
qualify the historical pair. Viewer 0.24.0 lacks the `MolSysView.closed`
lifecycle required by the redesigned MolSysMT tools addon. The old Viewer
0.24.1 builds and the four older MolSysMT 1.0.0 build 0 files remain in staging.
The redesigned addon and current independent-domain integration have **no
qualified public pair**. Keep the existing ordinary Viewer dependency floor
`molsysmt>=0.23.0` in its demonstrated scope. [Installed qualification](installed_artifact_qualification.md)
and [MolSysMT #524](https://github.com/uibcdf/molsysmt/issues/524) record the two directions.

Viewer **0.25.0** is our intended successor for qualifying the host side of
#524. MolSysMT needs to identify the corresponding producer/version that
contains the received native-domain and interaction contracts plus the addon
under test. When candidate work resumes, agree clean source SHAs and supported
capability scopes, then record versions, build strings, channels, dependency
closure and hashes of the original artifacts. Qualify the exact pair outside
both source trees in the sixteen Conda cells, checking actual imports, addon
discovery, lifecycle and the scientific/session routes. Include the supported
minimum and newer dependency routes for the capabilities advertised. Set a
published addon floor only from those results. Qt retains its experimental
host qualification. Candidate preparation and publication remain paused.

## MolSysMT #615 first-canvas evidence

The original Analysis attempt timed out after the existing 30-second wait.
The cell appeared executing and the original 45-second stack timer left an
empty trace. The diagnostic pass with a 15-second timer completed its initial
cell in 3.357631 seconds. Eleven later Jupyter scenarios passed on another
recorded pair. MolSysMT's newer `/api/sessions` observations occurred after the
browser retired and therefore describe that later state. Keep the original
failure and the distinct cold-server case #705. [Owner report](https://github.com/uibcdf/molsysmt/issues/615)
and [Viewer receipt](molsysmt_analysis_receiving_20261106.json) retain the evidence.

We propose one bounded Analysis diagnostic on a recorded source pair when a
targeted run is needed. Reuse `system_panel_jupyter.py` and
`analysis_panel_jupyter.mjs` with the original 1TCD cell and canvas deadline.
Arm a small trace before clicking Run. Record the last observed stage on both
sides of the widget handoff.

| Stage | Evidence before teardown |
| --- | --- |
| Notebook execution | Record Run submission, initial-cell start, boundaries around imports, 1TCD loading and the display hook, and completion or exception. Keep the existing flushed 15-second kernel stack. |
| Kernel and widget transport | Sample the isolated server session state at about 15 seconds and at the canvas timeout while the browser is still connected. Record the display and widget comm acknowledgement or first bootstrap event for this view, when observed. |
| Viewer rendering | Record widget mount, connected canvas and controller identity, expected 3,983-atom scene registration, and the first new native Mol* draw after registration. Record the viewport and any bounded render error when the wait fails. |

Use monotonic elapsed times and a local correlation label. Retain bounded
metadata and keep kernel traces in private custody. The earliest missing
transition narrows the next investigation only when its observer was active.
Capture failure evidence before browser retirement with finite diagnostic
requests. Preserve the existing deadline, assertions, cold imports and kernel
lifecycle. Viewer owns the mount/scene/draw observations. MolSysMT owns the
Analysis runner and the kernel/server observations. A causal repair or an
evidenced environment-specific disposition is still required to close #615.
