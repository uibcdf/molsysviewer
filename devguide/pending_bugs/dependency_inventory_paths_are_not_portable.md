---
summary: Dependency inventory audit rejects valid paths on Windows.
issue: uibcdf/molsysviewer#139
status: active
opened: 2026-10-01
closed:
severity: medium
verification: reproduced
area: [ci, dependencies, windows]
guard: tests/test_dependency_contract.py::test_dependency_inventory_paths_use_portable_separators
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Dependency inventory paths are not portable

**Reported:** 2026-10-01, Windows job `110577800941`, source-pair run
`36924331859`, Viewer commit `015b8884cbecf082492922cc6f0433f751d1f86a`.

## What

The audit rejects the valid recipe, environment inventory and source workflow
on Windows. Linux and macOS pass that audit and their full scientific suites.

```text
[DEPENDENCY_CONTRACT] Conda recipe inventory differs from discovered recipes
[DEPENDENCY_CONTRACT] .github\workflows\ci-python-314-source-pair.yaml: unclassified or duplicate source checkout uibcdf/molsysmt
```

## How

`str(path.relative_to(root))` uses native Windows backslashes, whereas the TOML
inventory and workflow references use slashes. The resulting unequal keys
cause false missing/duplicate classifications. Serialize relative inventory
keys with `as_posix()` at all three discovery sites through one private helper.

## Why

The metadata contract must behave identically on all qualified native hosts.
The real Windows gate exposes this independently of the provider-floor issue
#138: the corrected released provider passes the version/provenance checks.

## What was refuted

The recipe, environment files and provider checkout are valid. Suppressing the
audit, relaxing inventory equality or globally rewriting native filesystem
paths would hide the defect or damage installed-origin checks.

## Resolution

The three discovery sites share the portable serializer. Six real path-object
cases cover Windows and POSIX recipe/environment/workflow keys; the real-tree
audit and invalid/duplicate-route rejection remain required. Focused and
native hosted qualification are pending. Focused qualification passes
**173 tests**, exit 0; Ruff check/format and the read-only metadata audit pass.
