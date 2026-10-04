# Version assessment — 2026-10-03

## Recommendation

The accumulated source warrants **0.24.0**, after the published 0.23.4. It adds
substantial public capabilities: an Interactions domain with explicit calculation
families, scientific storage and Studio controls; a batch/progressive loading
contract with durable source identity; cell assignment; and scene/API hardening.
A patch number would understate this change in functionality and public surface.
This remains pre-1.0; it is not a proposal to declare the final stable contract.

This is a recommendation, not a chosen release identity. No new tag, package,
Release or DOI was created during integration. The source integration is
`0dea171db750c289e6b1f85c2407f91f3ce58f4a`. The latest public GitHub Release and
local canonical version tag are 0.23.4, verified on 2026-10-03.

## Why no tag yet

Published MolSysMT 0.22.4 lacks the new Interactions APIs. The current evidence
uses an experimental installed provider and an independently changing editable
provider. Before publication, agree and distribute a compatible provider version,
then qualify the actual dependency closure. Do not invent a future minimum
version or treat a source SHA as a published package.

Freeze the exact Viewer commit and version; reconcile citation metadata, Python
and JS package versions, then rebuild and validate the runtime in the actual
wheel and other claimed artifacts. The integration runtime build deliberately
did not synchronize JS version metadata. Prior complete installed and 39/39 core
browser results retain their original hashes/inputs and do not qualify this
future release. The internal `[skip ci]` commit is not a release candidate.

Run the required exact-candidate Python/JS/hosted core gates and installed-pair
matrix, including repaired Windows resources (#101). Complete the accepted
scientific-use and first-contact evidence and the final public-documentation
block. Retain the standalone experimental and remote post-1.0 boundaries.

Follow `release_and_citation.md` and the shared release-version policy linked in
`MOLSYSSUITE_GUIDE.md`: new public versions/tags use `X.Y.Z`, without public
prerelease tags. Candidate evaluation uses staging and exact-commit evidence.
Legacy local instructions offering `X.Y.Z-rc.N` have been reconciled with that
policy. A tag triggers npm publication, so it is not an inert development marker.
After publication, separately verify each distribution and Zenodo ingestion.

## Next work

The subsequent [scientific review](scientific_use_review_20261004.md) reproduces
two provider defects (uibcdf/molsysmt#312/#313) and the consumer prevalidation
gap #157. The consumer now rejects unusable candidates before mutation; the two
provider defects remain open. Requalify successful mixed-source loading after
their public fixes before claiming that support in the next version. Other
bounded real workflows pass; this does
not remove the exact-provider/artifact gates below.

Review representative real molecular workflows before freezing the next version:
independent/progressive loading; nonconsecutive trajectory structures and sparse
interaction queries; units/PBC; scientific H5MSM and Viewer session round trips.
Record correctness, practical friction and remaining human visual observations.
The existing exact-provider/artifact gates remain tracked in #114/#140/#101.
