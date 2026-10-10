# Preparing Viewer 0.25.0 — 2026-10-09

**Version agreed, producer not frozen.** The principal maintainer selects
0.25.0 for the next pre-1.0 stabilization candidate, replacing the prospective
0.24.1 publication. The maintainer explicitly says further changes remain.
Do not freeze a candidate SHA/ref, create a tag, build/upload a staging package
or dispatch an installed pair until that work is completed and reviewed.
Both Viewer and MolSysMT 1.0 publication remain paused.

## Included work

The candidate will include #149/#177 and the experimental Interactions consumer
contract already prepared for 0.24.1, plus the accepted canvas-menu and controls
work under `uibcdf/molsysviewer#179` and `uibcdf/molsysviewer#180`.
Annotation terminology is consistent in target/selection creation. Native
membership is preserved before rendering defaults so unavailable Group/Chain
actions explain their limitation. The public `autohide_scope` configuration
is an additive API change, supporting the minor-version choice.

The authorized Studio round (#181–#188) adds actual PNG dimensions/background,
browser HTML delivery, native keyboard controls, compact navigation and preserved
floating geometry, with clearer Interactions scopes and descriptions. MolSysMT's
former addon is retired while its required native backend remains. Provider
cleanup is tracked by `uibcdf/molsysmt#354`; a separate empty bonded-to selector
failure observed with the hydrogen-free 1TCD demo is `uibcdf/molsysmt#355`.
Review the [Studio contract](studio_interaction_contract.md) and its source
evidence in [the Studio review](studio_review_20261009.md) before freezing a
producer. Both provider issues are fixed in source, without authorizing provider
publication or qualifying new packages. The separate macOS dynamic-region
restoration diagnosis `uibcdf/molsysviewer#189` is corrected in source with a
deterministic budget-fallback guard; all six scientific cells pass in 38038849075
(the separate experimental Qt job fails).

The second Studio refinement (#190–#197/#199) adds corrected visible-structure
shape geometry, correlated creation feedback, nine executable geometry guides, persistent secondary editors and named controls. Reusable local search, marked
batch operations with one Undo step, and native creation/advanced disclosures
complete the authorized optional improvements. The core inventory is now 43
suites. The source-pair PNG guard correction (#198) closes after measured phase
timing and successful Linux core 43/43 on exact source 32565b6d in 38040586601.
This source implementation does not freeze the 0.25.0 producer or supersede
the preserved 0.24.1 bytes.

The final Studio review (#201–#204) adds creation completion for Measures,
Annotations and Layers, atomic initial layer membership, persistent new-region
names, explicit finite annotation coordinates, and confirmed scientific analysis
deletion with history-loss disclosure. Its source and real-browser evidence
belongs to the same [Studio review](studio_review_20261009.md). These corrections
do not freeze the candidate or authorize publication.

The closure follow-up (#206–#208) makes region/selection replacement atomic,
preserves complete saved-selection state in Undo/Redo, completes the remaining
creation/registration feedback and corrects exported Studio backend state.
Its guards and the local Qt limitations are recorded in the same Studio review.
#189 is resolved through its captured budget warning and forced-fallback guard.
#198 is diagnosed and corrected in the guard: the measured software render
exceeds the old 30-second event deadline. Source `32565b6d` waits for managed
render completion within the existing suite budget, then limits file delivery.
Full-quality PNG dimensions/alpha and held-click assertions remain. The scoped
local guard and exact-source Linux core step pass, closing #198 without
claiming that the full still-pending pair is green.
The subsequent core stopped before PNG on keyboard focus transfer (#209). Its
shared-owner correction and expanded Enter/Space/fullscreen/static-scene/popup
guard pass locally; integrated cba156d8 core 38041459348 passes 43/43.
Latest scientific/source-pair campaigns still need review; experimental Qt
failure is separate.

The user guide is [Using the canvas context menu](../docs/content/user/viewer/context_menu.md).
Normative behavior remains in [gestures and menus](interaction_gestures_and_menus.md)
and the [payload contract](../docs/content/developer/protocol_and_payloads.md).

## Qualification sequence after final source review

The public Python API round is tracked in
[the final API review](public_api_review_20261010.md): #210–#216 cover factory
selection, annotation arguments, handle ownership/focus, saved-selection labels,
delegated digestion and immutable identity. #217 completes handle inspection and
editing parity. Its source evidence must be reviewed before freezing a producer;
the existing public and staged packages do not contain these changes.

The additional read-boundary review tracks #218–#222: scoped system queries,
retired read handles, mode history, accurate handle annotations and detached
InteractionSet configuration. Its evidence is maintained in
[the API follow-up](public_api_followup_20261010.md). These changes also precede
freezing the producer; 0.25.0 remains unfrozen and both 1.0 publications paused.

1. Finish the remaining changes and inspect applicable source CI, including
   the complete core browser lane. Keep experimental Qt outcomes separate.
2. Prepare canonical 0.25.0 citation/npm/Conda-route metadata, inspect the diff,
   and freeze a clean producer and fixed `candidate/0.25.0-build0` reference.
   Keep unrelated sandbox work in the development checkout.
3. Build the noarch build 0 into staging; independently verify original producer
   receipts, channel filename, metadata, bytes and SHA-256. No public promotion.
4. Agree the exact MolSysMT counterpart with its owner. Neither the public
   minimum `>=0.23.0` nor the previous 1.0.0 staging file implies the next pair
   is qualified or authorizes a MolSysMT 1.0 publication.
5. Run exact-candidate source/core and native Windows launcher/resource gates.
   Agree one installed-pair dispatch covering four platforms × Python 3.11–3.14
   after both sets of files are available, then inspect all original environment
   archives. Complete installed first-contact review against those exact files.
6. Record evidence and outstanding limits in a new receipt. Public tags,
   Releases, npm/CDN, Conda promotion and Zenodo require separate final approval.

## Preserved prior evidence

[0.24.1 preparation](stabilization_0241_preparation_20261008.md), its two frozen
builds/references and the original files retain their identities and scope.
Do not move a reference, reconstruct historical bytes or reinterpret its
sixteen-cell provider result as qualification of the changed menu. Public
versions remain Viewer 0.24.0 and MolSysMT 0.23.0.

This is a preparation plan, not release clearance or a package receipt.

## Accepted cross-surface coverage round — 2026-10-10

The principal maintainer adds #223–#225 before freezing 0.25.0: tagged annotation
focus including absolute coordinates; truthful Interactions visibility wording;
Studio state JSON/experimental MSV save/restore through the public owners; and
folded workflow examples. Validation and closure evidence belongs to
`studio_coverage_20261010.md`. Equivalent Python code generation from Studio
is deliberately deferred to `uibcdf/molsysviewer#226` (post-1.0).
These changes do not stabilize experimental session/Interactions contracts or
freeze a producer. Both 1.0 publications and public promotion remain paused.

Source `33e73587` completes #223–#225/#227 with six scientific cells and three
Python 3.14 source-pair cells green, hosted core 43/43, JS 327/327 and 25/25
notebooks. The requested fresh real-browser Studio flow check also passes.
Experimental Qt still fails to create WebGL, so the scientific workflow is
not globally green. The coverage receipt preserves the final run/job identities,
local provider source and log digests. This source evidence does not freeze
0.25.0 or qualify its future installed package.

## Integrated scientific/resource closeout — 2026-10-10

Source `f272e384` closes #200/#228–#230 under
[the integrated review](integrated_review_20261010.md). It passes 13 resource,
137 scientific, 241 final policy and 43/43 core-browser checks. The single
complete Python run retains eight experimental Qt context failures after six
bookkeeping repairs. Fresh applicable hosted CI remains pending. Include these
fixes in the future producer after documentation and final installed first
contact; this does not freeze a SHA/ref or authorize staging/publication.
