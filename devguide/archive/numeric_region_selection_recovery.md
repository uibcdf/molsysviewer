---
summary: Preserve numeric region selectors through same-system scene and session recovery.
issue: uibcdf/molsysviewer#307
status: resolved
opened: 2026-11-06
closed: 2026-11-06
severity: medium
verification: reproduced
area: [state, regions, persistence]
guard: tests/test_extract_numeric_region_recipes.py::test_same_system_recovery_retains_numeric_selection_and_serialized_recipe
normative:
blocked_by: []
supersedes: []
---

# Numeric region selection recovery

## What

A same-system state/session round trip retained a numeric region's atoms and
provenance but replaced its public `selection` with `"all"`. Subsequent exports
then advertised a whole-system query for a subset. Direct `import_state()` with
the bundled dialanine view reproduces `[0, 2] -> "all"`, while actual membership
remains `(0, 2)`. This is metadata fidelity, not an observed expansion of atoms.

## How

`export_state()` puts a non-string query in `provenance.expression` and emits
`selection: null`. `_restore_region_v2()` previously replaced every non-string
serialized selection with `"all"`, overlooking the retained query. The failure
was observed on e920faf9 with native MolSysMT ed09f6453 and contribution
8f8c442e, under Linux/Python 3.14 and the recorded PyUnitWizard source profile.

The full paginated board inventory (277 issues, four pages) was reviewed.
Closed #296 concerns extraction across changed atom universes; #119 concerns
lost scene objects and #66 textual-query reevaluation on another system.

## Why

Restored public objects and repeat exports must describe their actual recipe.
The molecular-session receiving under #264 exposed the discrepancy when an
edited ensemble with numeric regions was saved and reopened.

## Resolution

Restore an available query expression by independent copy when the serialized
selection is not a string. Preserve textual selectors and existing fallback
behavior for transferred/non-query recipes. This does not replay changed-
universe source indices or add a scientific selection interpreter.

The new guard fails all 16 cases before the correction: list, tuple, NumPy
integer-array and scalar selectors, static/dynamic modes, and state/session
routes. It now verifies selector, membership, mode, colors, provenance, repeat
exports and independence from the incoming payload. The complete numeric-
recipe module passes 31 cases; broader state, identity, session rejection and
transfer receiving passes 102 cases in 26.50 s. Legacy-format warnings and the
intentional different-system warning remain visible. No TypeScript/runtime
bundle, public signature or molecular scientific algorithm changes.
