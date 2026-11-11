---
summary: Digest the advertised curated molecular representation parameters.
issue: uibcdf/molsysviewer#357
status: resolved
opened: 2026-11-11
closed: 2026-11-11
severity: medium
verification: reproduced
area: [public-api, representations, argdigest]
guard: tests/test_representation_parameters.py
normative:
blocked_by: []
supersedes: []
---

# Curated representation parameters — source correction received

Whole and Region advertise `sizeFactor` in their parameter catalogue, but
ordinary `set_representation(..., sizeFactor=0.7)` emits a missing-digester
warning. Existing rendering may succeed: this is an argument-contract gap,
not evidence of broken molecular geometry or a provider defect. The original
observation is retained in #357 and the Movie receiving history.

Use the existing curated parameter catalogue for type/enum/range contracts
and expose its units for physical renderer fields. Register ordinary ArgDigest
parameter owners instead of suppressing unknown-key warnings. Preserve the
advanced Mol* escape route and the unrelated pocket-grid resolution contract.
Receive real Whole/Region calls, rejected values without scene/history writes,
native forwarding, aliases already supported by the representation owner,
schema coverage and session recovery. Keep source and installed receiving
separate; no new dependency floor or published candidate follows.

## Resolution

The catalogue now supplies the existing native controls' finite/scalar,
boolean, enum and minimum contracts, with fixed angstrom metadata for grid
spacing and probe radius. Eleven missing per-argument owners are registered;
existing resolution digestion retains its other callers. Whole and Region
also apply the shared semantic checks before mutation, protecting delegated
Styles and scalar molecular opacity without changing shape batches. Returned
schema enum lists are detached from the validator's authority.

The causal before-fix test fails on both real owners. Final focused receiving
passes 99 cases and 1,649 affected cases pass in the wider source collection.
The native bridge receives `sizeFactor=0.7` in the actual Mol* primary
representation through four reversed samples, existing popup checks, session
reopen and decoded MP4. The two later camera-precondition failures are kept
under #361 rather than attributed to scale handling.

[The receipt](../curated_representation_receiving_20261111.json) retains exact
sources, PyUnitWizard 0.29.4 development origin, guards, native controls and
private custody. Hosted, installed and human acceptance remain separate under
#315; this closure supplies neither a public package nor a universal renderer
parameter domain.
