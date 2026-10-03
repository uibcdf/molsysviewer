# Accumulated-change integration review — 2026-10-03

The principal maintainer authorized review and direct integration into `main`,
followed by developer-guide reconciliation, version assessment and a real
scientific-use review. No release or new support certification is declared here.

## Reviewed scope

The cumulative candidate covers the native Interactions API and Studio subpanel,
nine explicit interaction families, sparse observation inspection and scientific
H5MSM storage; public argument digestion; scene ownership, transfer and lifecycle;
annotations, styles and numeric trajectory plots; one-MolSys batch/progressive
loading, durable source records, Whole-only source visibility and controlled cell
assignment. Python, TypeScript, scientific-provider and local Mol* owners were
reviewed together with their guards and retained qualification evidence.

The base is `924da3a32111d8994639e8a72cb901ebeb8f870a`. A fresh remote fetch
found no divergence. All 409 initial dirty/untracked paths were recorded and
backed up in `/tmp/msv-review-backup-20261003.tar.gz`, with a hash manifest beside
it. The pre-existing ACKREDIT stash and the three sandbox panel mockups remain
preserved separately. Generated runtime files are rebuilt through the official
runtime build; they are never manually read or edited.

## Additional finding and correction

`uibcdf/molsysviewer#156` reproduced a repeated-structure extraction defect:
scientific occurrences survived, but a display filter lost the first copy.
Canonical scene transfer now retains every matching destination and selects the
first copy for the scalar current frame. The new guard checks scientific
coverage, both projected copies, excluded frames, source correspondence and
session restoration. The owning report records the reproduction and validation.

## Qualification boundaries

The development environment is explicitly `molsyssuite@uibcdf_3.14`, Python
3.14.7. Ruff and TypeScript checks pass. The seven scene-transfer guards pass.
The final once-run source regression and runtime build are recorded in
`integration_review_20261003.json`.

Before the extraction correction, all 614 product Python sources matched the
latest box-verified wheel recorded in `integration_completion_20261003.json`.
That record also retains the 39/39 core browser result under the normal deadline,
the complete earlier installed run and the later installed cell guards. These
are bounded observations of their original inputs. The new Python transfer
correction is covered by its source guard and full source regression; no new
complete installed or hosted-candidate result is inferred.

The editable MolSysMT workspace is experimental and independently changing.
Published MolSysMT 0.22.4 lacks Interactions and cannot initialize the tested cell
through this route. The existing ordinary CI dependency selection therefore
cannot qualify the new scientific feature. This internal integration uses the
existing `[skip ci]` deferred route, retains CI debt and does not relax required
tests or change release workflows. The earlier green hosted results retain their
original commits; none certifies this integration commit. Issues #114, #140,
#101 and the relevant partial reports retain their artifact/provider gates.

## Follow-up

Reconcile current developer-guide summaries without rewriting dated failures or
older artifact records. Assess a new minor version because this change adds
public scientific and loading capabilities; freeze no tag until the required
compatible provider and exact-candidate checks exist. Then review representative
scientific use, preserving the distinction between automated observations and
human visual/first-contact validation. Public documentation remains the last
functional-closure step under the maintainer's accepted order.
