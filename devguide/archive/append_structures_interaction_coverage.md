---
summary: Preserve evaluated interaction coverage when appending unchanged structures
issue: uibcdf/molsysviewer#346
status: resolved
opened: 2026-11-09
closed: 2026-11-09
severity: high
verification: reproduced
area: [loading, interactions, scientific-integrity]
guard: tests/test_recovered_interaction_append.py
normative:
blocked_by: []
supersedes: []
---

The D4 recovery/continuation probe at Viewer `6ab82333` and public MolSysMT
`9be08134` isolates a Viewer defect: session recovery, rejected analysed input
and native append retain coverage `[2, 0]`; `View.load` clears it through the
default conservative edit policy. The original failing probe and its layer
checks are retained in the private D scientific receiving packet. An earlier
diagnostic expected sorted coverage incorrectly; its corrected comparison
uses the original ordering and still reproduces the actual empty coverage.

Use the existing preservation policy for native-validated structure append.
Neither coordinates nor identity in the retained prefix change; the provider
extends named analyses with new unevaluated structures. Keep arbitrary edits
conservative, source provenance unchanged, and incompatible/analysed inputs
atomic refusals. No new public flag or implicit molecular observation is needed.

The real pentalanine regression covers explicit and automatic append following
canonical H5MSM session recovery, sparse occurrence identities, coverage and
visual/region ownership, known-prefix source records, continued persistence and
the separate conservative arbitrary-edit path. This receives the correction in
uibcdf/molsysmt#616 without rewriting native chemical inventory.

**Resolved in source:** both real append/auto regressions fail on the original
coverage loss and pass after using `interactions_policy="preserve"` only in the
native-validated append branch. The covering load/interactions/source/edit and
reporting collection passes 559 cases with zero failures/errors/skips. Affected
arbitrary and partial-coordinate edits retain their previous invalidation guards.
Inputs are fixed, peak tracked RSS is 632.7 MiB, and owned cleanup is complete.
Ruff check and format checks pass. Hosted/installed/human receiving remains
separate; no TypeScript or generated runtime change is needed.
