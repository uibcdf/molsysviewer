# Final design closure — implemented locally; candidate qualification pending

The principal maintainer accepted the final design review on 2026-10-03. Public
documentation remains last. Issues #146–#150 own the five corrections; #151 owns
the additional loading discussion. Existing unrelated working-tree changes were
preserved before implementation in `/tmp/msv-design-closure-before-20261003.tar.gz`.

## Current implementation

| Issue | Surface | Outcome in the working tree |
| --- | --- | --- |
| #146 | Annotations | Coordinate/atom anchors, physical units, editing/history/state/session/transfer, real world/camera callouts and solid/dashed/dotted leaders |
| #147 | System identity | Available chain/group/atom identities plus atom IDs/types; missing hierarchy is explicit; announced same-size edits invalidate caches |
| #148 | Loading/editing | Conversion and source mappings precede replacement reset; append accounting is checked before system/analysis/scene mutations |
| #149 | Styles | Nested input recipes, registry values and scene/focus builtin values are detached at ownership boundaries |
| #150 | Trajectory plots | Numeric x positions agree across series/events/playhead/seeking; repeated positions have deterministic ties; nonfinite data is refused before mutation |

The reports remain partial until this source is integrated into a reviewed,
committed candidate and qualified with its supported dependency artifacts. This
does not change the compatible-published-provider gate on #114. The fixes do not
authenticate independent scientific files or undo external molecular edits.

The integrated wheel and official-environment follow-up are recorded in
`integration_qualification_20261003.json` and
[the maintained artifact qualification](installed_artifact_qualification.md#integrated-design-candidate--2026-10-03).
Development uses `molsyssuite@uibcdf_3.14` explicitly. The failed full installed
attempt, scoped recovery and browser time budget remain separate evidence;
the original implementation record below is not replaced by a claim of a
passing complete candidate.

## Loading discussion required before freezing the API

[Issue #151](https://github.com/uibcdf/molsysviewer/issues/151) must decide the
public contract for four PDB files, four PDB IDs, mixed compatible molecular
forms, and one load followed by further loads. Batch and progressive loading
must express the same intention. A list of complementary forms describing one
system cannot silently acquire the meaning of four independent systems.

The current explicit progressive route is `view.load(source, mode="add",
label=...)`. It combines systems in one MolSys and maintains load blocks/regions.
`mode="append_structures"` addresses additional structures of the current
topology. `auto` is a heuristic, so it cannot decide whether two equal-topology
inputs represent independent copies or successive conformations on the user's
behalf in the new contract.

Discuss three intentions separately: combine independent systems in one scene;
append conformations after explicit atom correspondence; or construct one system
from complementary topology/coordinate forms. The maintainer accepted one
`view.load()` entry with `multiple=True` for independent sources and
`multiple=False` by default for the current one-system semantics. No `load_many`
is introduced. The authorized first implementation now prepares independent
sources and a composed candidate, with compact source records and explicit
multi-frame pairing/time validation. The maintained implementation and remaining
scope are in `pending_proposals/multiple_system_loading_contract.md`.

Its detailed bounded contract candidate now covers shared/per-source selectors,
explicit ordinal pairing, time checks, compact durable source maps, source-region
independence and batch preparation. A demo-derived native-provider probe verifies
box/order preservation and rejection of mismatched frame counts, while confirming
that time compatibility needs an explicit Viewer loading contract. The loading
slice now enforces that check. Source persistence through sessions/copy/extraction,
history, explicit atom edits and merge is implemented locally with scoped guards.
Controlled box assignment is implemented locally through `view.set_box`:
unit-bearing quantities or a declared provider-supported source, complete-series
initialization/removal, explicit multi-frame source pairing and selected-frame
interaction invalidation. Current boxes persist across later source additions.
Scientific cell and edge display refresh are guarded in Python and real Mol*.
Studio now expresses the same intentions in its System subpanel and delegates
to public loading; see the Studio loading contract in `architecture.md`.
The editable provider has repaired partial extraction and complementary H5MSM
composition (uibcdf/molsysmt#307 and uibcdf/molsysmt#309); six positive atom/frame
combinations now pass through Python loading. Compatible published-provider
qualification remains separate. The default-budget core passes all 39 suites;
Interactions retains lifecycle, geometry and all calculation forms in three
mandatory scenarios. Box edits now verify the provider's actual result (#155),
including an explicit error on the real published provider's ignored cell
initialization. Exact artifact and regression boundaries are in the checkpoint
and dated integration-completion record.

Acceptance must cover stable source/load identifiers, labels and provenance,
local-to-global atom maps, independent selection/visibility, repeated chain and
residue IDs, different atom order/topology, structure-count/time/cell compatibility,
explicit coordinate alignment and broadcasting, analysis-name conflicts and
intra/inter-system interaction scope. Define whether a failed batch is atomic or
can return declared partial success. Consider acquisition errors for PDB IDs,
selections per source, memory budgets and parity with Studio. Never silently
truncate, align, broadcast, concatenate trajectory axes or overwrite analyses.

## Next execution order

1. Integrate and qualify #146–#150 with the preserved public workflow work.
2. Discuss #151 and settle its minimum; record any larger architecture as post-1.0.
3. Evaluate the bounded atom/group canvas picking slice of #45. It requires both
   Mol* granularity and Viewer selection semantics; changing only Mol* props is
   insufficient. Chain/entity picking remains conditional on separate evidence.
4. Consider interaction count series from #48/#56 only after a public provider
   reduction defines occurrence/relation counts and coverage for empty,
   unevaluated and excluded structures. No Viewer-only scientific reduction is
   introduced here.
5. Freeze the agreed API, update public documentation, then qualify the exact
   artifact candidate and publication routes.

Full MVS annotations, structure/file windowing, large transport/performance
refactors, multiple viewports, richer rendering, Mol* upgrade, supported remotes
and standalone certification retain their post-1.0 scope. Already implemented
interaction families, focus styles, rings and retained plots are not new future
features. Implementation evidence is in
`final_design_closure_20261003.json`; the current checkpoint links this plan.
