---
summary: Guard public routes, signatures, defaults and explicit stability classifications.
issue: uibcdf/molsysviewer#350
status: resolved
opened: 2026-11-10
closed: 2026-11-10
verification: inspected
area: [public-api, compatibility, validation]
guard: tests/test_public_api_contract.py
normative: docs/content/developer/public_api.md
blocked_by: []
supersedes: []
---

# Reviewed public API contract

**Adopted F1; implemented and received in source.** The principal maintainer
accepted this additional pre-1.0 work on 2026-11-10 under #315. The original
46-item denominator stays unchanged.

## What and why

The existing `devtools/public_api_inventory.py` and its baseline verify
reachability, ArgDigest, explicit `skip_digestion` and argument digesters. Their
baseline intentionally does not preserve full signatures or properties. A
removed keyword, changed default or property/method transition needs a separate
reviewed compatibility guard.

## Implemented contract

Reuse the public reachability inventory and documented manager/handle routes.
Record callable/property kind, ordered parameters and parameter kinds, defaults,
and explicit stable/growing/experimental classification. Keep getters/setters
and constructor/protocol exclusions deliberate. Do not freeze private owner
names or import scientific providers' own APIs into the Viewer promise.

The baseline must be deterministic and reviewable. Unsupported default encodings
must fail visibly rather than capture address-bearing representations. Record
intentional compatible additions separately from incompatible changes requiring
review; a regenerated file alone does not establish approval or scientific
stability. Classification follows the maintained public contract, including
experimental interactions, sessions, native hosts and remote preview boundaries.

## Receiving

Verify the current real surface and use meaningful mutation controls: removed
routes, parameter order/kind/default changes, property/callable transitions and
unreviewed stability changes must be detected. Retain the digestion gate as a
separate check. Reconcile intentional B4 and Movie #320 changes before a future
candidate freeze. This work authorizes no package, tag or publication.

## Resolution — 2026-11-10

The explicit reviewed snapshot records 741 callables, 175 properties and 38 constructors (954 declarations), including parameter order/kind/defaults and async status. Deterministic typed default encoding refuses unsupported objects; inherited builtin constructors are named explicitly. Stability rules retain the documented experimental boundaries. Every drift fails; the report distinguishes additions, compatible optional extensions, incompatible changes and classification review. Both focused inventory/contract guards pass 28 cases; the covering affected headless batch passes 101. Preserve the initial instrumentation-induced determinism failure and its functools.wraps correction. The [receipt](../public_api_contract_receiving_20261110.json) identifies sources, mutation controls and limits. Intentional B4/Movie additions and the final candidate still need their own reviewed snapshot update. This additional adopted F1 result does not change the original 46-item denominator or authorize publication.
