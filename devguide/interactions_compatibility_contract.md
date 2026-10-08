# Interactions consumer contract — 2026-10-08

This is the bounded consumer contract agreed with the MolSysMT team for the
next installed pair. It supplements [scene contracts](scene_contracts.md) and
[scientific qualification](interactions_qualification.md). Preparing MolSysMT
1.0.0 does not change the experimental classification of `Interactions`,
`InteractionsDict`, `molsysmt.interactions.page@1` or any detection family.
MolSysViewer's Interactions surface remains experimental too. These implemented
engineering commitments do not promise scientific stability or unconditional
compatibility with future provider versions.

## Consuming results and queries

Use public sparse results with variable-size participants and explicit roles.
Keep occurrences separate from relations, including parallel observations.
`occurrence_indices` identify rows within one version of a complete analysis;
queries and persistence preserve them. Replacement, extraction, remapping or a
new analysis version can reassign them. They are not global persistent IDs.
Viewer actions additionally require the current analysis signature, query
revision and structure index; an occurrence index alone cannot authorize an
action after the analysis or filter changes.

Preserve evaluated-empty versus unevaluated coverage, named analyses, measurements
with units, original method/parameters/software and evidence. Atom and structure
queries accept nonconsecutive lists. The public modes are `involving_selection`,
`within_selection`, `across_selection_boundary` and `between_selections`;
constituent atoms of compound participants count in the predicates.

Inspection uses public `to_page` when available. It bounds copied occurrences
and participants **after query construction**. The query can retain positions
and secondary indexes, and metadata can scale with the number of structures.
Neither this codec nor Viewer's reply/render budgets bound total RAM or provide
public file queries without loading the selected H5MSM analysis. Start with named analyses loaded into memory
and visible-frame projection; retain the measured combined coordinate/analysis
residency and explicit limits rather than claiming arbitrary-scale support.

## Preserving geometry, correspondence and coverage

For box vectors stored as rows in nm, participant positions are
`r + image_vector @ box`. Display relative to the first participant uses
`(image_p - image_0) @ box`. A vector shifts a whole participant, not the atoms
inside a split periodic ring. Do not infer missing images, unwrap a split group
or invent a required box. Wire geometry and radius explicitly declare nm and
the renderer converts once to angstroms.

H5MSM 0.5 preserves complete named results alongside a system or independently,
including coverage, source maps and supported extraction/remapping. Independent
import requires an explicit correspondence declaration and ordered maps when
needed. `source_id` and maps preserve provenance; they do not authenticate origin.
Sessions store scientific data once, separately from visual references/history.

Provider public setters invalidate evaluated coverage when molecular data change.
Direct edits to raw arrays require explicit invalidation. Viewer-owned system
edits retain their existing invalidation contract; `interactions_policy="preserve"`
declares that incoming analyses are already valid. No playback, query or edit
automatically recalculates science. Changed parameters require a new named analysis.

## Qualification and ownership

The public 0.24.0 / 0.23.0 pair remains the delivered baseline. The next planned
Viewer artifact is 0.24.1 noarch, containing #149/#177, paired with the
provider's proposed 1.0.0 ABI3 build 0. Source checkpoints are not package
identities. Freeze exact producer commits and obtain immutable file hashes before
dispatching the new installed-pair matrix. Publication needs separate final
maintainer authorization. Final Viewer 1.0 qualification remains independent.

Use existing real-system guards in `tests/test_interactions_api.py`,
`tests/test_interaction_families.py`, `tests/test_interactions_scene.py`,
`tests/test_interactions_public_completion.py` and
`tests/test_interactions_qualification.py`. Check paging/residency with
`tests/test_interactions_projection_batching.py` and
`tests/test_interactions_residency_benchmark.py`, and restore/extraction with the
session and state guards. Run installed tests outside both checkouts, verify
import origins and record exact versions/builds, file digests and platform/Python.
Retain real browser calculation, subpanel, geometry and composite-load checks
against the matching runtime; #149/#177 keep their own regression checks.

Provider authority: [Interactions API](https://github.com/uibcdf/molsysmt/blob/main/devguide/interactions_api.md)
and [query semantics](https://github.com/uibcdf/molsysmt/blob/main/devguide/interactions_query_semantics.md),
with the proposed candidate and its experimental stability inventory owned by
`uibcdf/molsysmt#334`. No additional detector or provider feature is requested
by this agreement. Future changes require an explicit compatibility review and
new consumer evidence rather than extrapolation from the provider package version.
