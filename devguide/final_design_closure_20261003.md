# Final design closure — source integrated; release qualification pending

The principal maintainer accepted the final design review on 2026-10-03. Public
documentation remains last. Issues #146–#150 own the five corrections; #151 owns
the accepted additional loading contract. Existing unrelated working-tree changes were
preserved before implementation in `/tmp/msv-design-closure-before-20261003.tar.gz`.

## Current implementation

| Issue | Surface | Outcome in the integrated source |
| --- | --- | --- |
| #146 | Annotations | Coordinate/atom anchors, physical units, editing/history/state/session/transfer, real world/camera callouts and solid/dashed/dotted leaders |
| #147 | System identity | Available chain/group/atom identities plus atom IDs/types; missing hierarchy is explicit; announced same-size edits invalidate caches |
| #148 | Loading/editing | Conversion and source mappings precede replacement reset; append accounting is checked before system/analysis/scene mutations |
| #149 | Styles | Nested input recipes, registry values and scene/focus builtin values are detached at ownership boundaries |
| #150 | Trajectory plots | Numeric x positions agree across series/events/playhead/seeking; repeated positions have deterministic ties; nonfinite data is refused before mutation |

The source is reviewed, committed and pushed at `0dea171d`. The reports remain
partial until an exact candidate is qualified with its supported dependency
artifacts. This
does not change the compatible-published-provider gate on #114. The fixes do not
authenticate independent scientific files or undo external molecular edits.

The integrated wheel and official-environment follow-up are recorded in
`integration_qualification_20261003.json` and
[the maintained artifact qualification](installed_artifact_qualification.md#integrated-design-candidate--2026-10-03).
Development uses `molsyssuite@uibcdf_3.14` explicitly. The failed full installed
attempt, scoped recovery and browser time budget remain separate evidence;
the original implementation record below is not replaced by a claim of a
passing complete candidate.

## Accepted loading contract — implemented in the integrated source

[Issue #151](https://github.com/uibcdf/molsysviewer/issues/151) records the accepted
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

The contract expresses three intentions separately: combine independent systems in one scene;
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

The accepted bounded contract covers stable source/load identifiers, labels and provenance,
local-to-global atom maps, independent selection/visibility, repeated chain and
residue IDs, different atom order/topology, structure-count/time/cell compatibility,
analysis-name conflicts and intra/inter-system interaction scope. Preparation
failure is atomic; implicit coordinate alignment and trajectory broadcasting are
excluded from the minimum. Acquisition errors, source selectors, compact-map
memory budgets and Studio parity are guarded. Never silently
truncate, align, broadcast, concatenate trajectory axes or overwrite analyses.

## Next execution order

1. Source integration is complete. Reconcile developer-guide summaries and
   reports with `integration_review_20261003.md`, without rewriting older evidence.
2. Assess a minor version for the accumulated public features. Freeze no tag
   until compatible dependencies and exact-candidate release gates pass.
3. Review real scientific use of the accepted loading and Interactions contracts.
   Preserve automated correctness evidence and human usability observations
   separately. #151 is implemented, with artifact qualification still pending.
4. Qualify the compatible published provider and exact installed/hosted candidate,
   finish public documentation, then complete the release evidence.

Atom/group canvas picking (#45) and interaction count series (#48/#56) remain
optional follow-up discussions. Picking requires Viewer selection semantics as
well as Mol* granularity. Scientific reductions require a public provider contract
for occurrence/relation counts and empty/unevaluated/excluded coverage. Neither
is newly admitted as a prerequisite for this integrated source or for 1.0.

Full MVS annotations, structure/file windowing, large transport/performance
refactors, multiple viewports, richer rendering, Mol* upgrade, supported remotes
and standalone certification retain their post-1.0 scope. Already implemented
interaction families, focus styles, rings and retained plots are not new future
features. Implementation evidence is in
`final_design_closure_20261003.json`; the current checkpoint links this plan.
