---
summary: State identity can trust different atom associations and stale topology caches
issue: uibcdf/molsysviewer#147
status: partial
opened: 2026-10-03
closed:
severity: high
verification: measured
area: [state, identity, live_edit]
guard: tests/test_design_review_closure.py::test_announced_same_size_edit_invalidates_atom_identity_cache
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# State identity can trust different atom associations and stale topology caches

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

The state fingerprint hashes only ordered atom names, whereas anchor identities include chain/group associations. Both caches use object identity and atom count, so an announced in-place topology edit preserving atom count can reuse stale identity data.

## How

Inspected viewer/state.py _structure_identity/_atom_identities and apply_system_edit. The same atom names with changed chain/group assignments can follow the index fast path incorrectly.

## Why

Avoid restoring plausible labels, measurements and selections onto different atoms. Strengthen the topology fingerprint while preserving frame-independent identity; invalidate caches at declared system edits.

## Acceptance

Real-demo guards for same-name/different-group systems, same-object/same-count metadata edits, frame independence and legacy state handling.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

Fingerprint schema 2 uses available ordered chain/group/atom identities and atom IDs/types. Missing hierarchy is represented explicitly through public has_attribute/get, never synthesized. Atom identity caches use the same missing-field semantics and are invalidated on load/announced edits even when object and size are unchanged. Exported identity dictionaries are detached. Legacy fingerprint records take the conservative re-resolution path. The first full run exposed 38 RDKit cases that lacked optional hierarchy; all 38 pass in the subsequent 90-case correction selection.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).
