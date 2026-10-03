---
summary: Public entry points lack uniform digestion and explicit bypass signatures
issue: uibcdf/molsysviewer#125
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: medium
verification: reproduced
area: [api, digestion]
guard: tests/test_public_entrypoint_contract.py
normative:
blocked_by: []
supersedes: []
---

# Uniform public entry points

## What

The public inventory excluded delegating functions and did not test explicit
`skip_digestion=False` signatures. It reported zero outstanding digesters despite
those omissions. The annotation constructor also exposed both `add` and
`add_annotation`, with only the latter owning a real signature.

## How

Inspection of `devtools/public_api_inventory.py`, signatures and decorated plans
reproduced the gap. The user requested one ordinary public contract: ArgDigest,
explicit bypass parameter and canonical `view.annotations.add`.

## Why

Exemptions allowed an implementation detail to determine the public contract,
and the inventory did not inspect scene objects obtained through all managers.

## Acceptance

All public functions in the supported inventory have ArgDigest and explicit
`skip_digestion=False`. The inventory includes returned scene handles. There is
no `add_annotation` alias. Delegation, provider aliases, physical units and
cold imports remain valid; tests reject invalid inputs through real viewers.

## Resolution

Annotation creation is implemented only as view.annotations.add with the full named signature; add_annotation is removed. Every ordinary public function uses ArgDigest and explicit skip_digestion=False. The inventory now traverses exported classes and real returned scene handles: 699 callable routes are digested, with no exemptions or missing named digesters. Delegating shape constructors expose full named signatures. Public color normalization uses private primitives to avoid recursion. Molecular query request flags use public MolSysMT metadata and scoped public alias tables. Exported class methods and transport callbacks preserve their real contracts, including widget callback removal; raw peer packets retain structured rejection. Newly digested public methods also have SMonitor signals. Figure type checks import lazily to preserve cold imports.

This module asserts the removed alias, canonical signature, invalid units/flags, explicit bypass, warning-free queries, color normalization, full shape delegation, class methods and figure overrides on real demos. tests/test_public_api_inventory.py::test_all_public_functions_have_argdigest_and_an_explicit_bypass mechanically checks every reachable route; removing a public decorator or explicit bypass makes it fail. Cold imports, alias behavior, SMonitor, addon, style/export and remote transport selections pass. No args/kwargs placeholder digesters were added.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
