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
deterministic budget-fallback guard; its next hosted qualification remains pending.

The second Studio refinement (#190–#197/#199) adds corrected visible-structure
shape geometry, correlated creation feedback, nine executable geometry guides, persistent secondary editors and named controls. Reusable local search, marked
batch operations with one Undo step, and native creation/advanced disclosures
complete the authorized optional improvements. The core inventory is now 43
suites. The historical source-pair PNG timeout (#198) remains a separate partial
report until exact-source hosted evidence is reviewed. This source implementation
does not freeze the 0.25.0 producer or supersede the preserved 0.24.1 bytes.

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
local guard passes; exact-source hosted confirmation is still required for closure.
The subsequent core stopped before PNG on keyboard focus transfer (#209). Its
shared-owner correction and expanded Enter/Space/fullscreen/static-scene/popup
guard pass locally; inspect the next complete core for integration.

The user guide is [Using the canvas context menu](../docs/content/user/viewer/context_menu.md).
Normative behavior remains in [gestures and menus](interaction_gestures_and_menus.md)
and the [payload contract](../docs/content/developer/protocol_and_payloads.md).

## Qualification sequence after final source review

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
