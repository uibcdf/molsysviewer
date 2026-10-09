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
