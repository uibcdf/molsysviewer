---
summary: Python 3.14 source-pair default provider violates the runtime version floor.
issue: uibcdf/molsysviewer#138
status: active
opened: 2026-10-01
closed:
severity: medium
verification: reproduced
area: [ci, dependencies]
guard: tests/test_dependency_contract.py::test_installed_source_floor_and_identity
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Source-pair provider pin below the runtime floor

**Reported:** 2026-10-01, actual push-triggered source-pair run
`36922358875`, Viewer commit `78bb4565a56074bc78f45eb6377fcc8065e1de71`.

## What

All three Python 3.14 platforms reject the default provider before native and
scientific consumers. The Linux log records:

```text
[DEPENDENCY_CONTRACT] molsysmt: installed 0.21.0+726.g8ab42b585 violates molsysmt>=0.22.0
```

## How

The workflow still fixes `8ab42b58520892d54a05222b91c116b9e9114314`, an older
source whose installed version fails the current Viewer requirement. The new
audit now executes on main pushes (#137) and correctly exposes this drift.
Update checkout and both SHA environments together to the public 0.22.4 tag's
commit `e28ceb9ea0de0cc86bc370e5aff1e96c4cc71c69`.

## Why

Scientific feasibility cannot override the declared dependency floor. The
released 0.22.4 provider passed the isolated tooling publication tests; its
source checkout now needs actual three-platform installed qualification.
This does not qualify the uncommitted Interactions implementation (#114).

## What was refuted

The auditor is correct. Lowering the floor, fabricating a provider version or
moving a historical tag would conceal the problem. The GitHub API verified the
0.22.4 release/tag identity and the selected native test and Rust validator at
that exact commit before changing the workflow.

## Resolution

All three references are updated. The real installed-floor guard rejects older
distribution versions independently of the workflow pin, and the distribution
guard checks that checkout and audit use the same reviewed default. Focused
dependency, distribution, ecosystem and reporting qualification passes
**187 tests**, exit 0, with the published provider and the development build
tools. An initial attempt in the minimal installed environment stopped because
the wheel-build guard requires the absent `build` module; using the established
build-capable development environment corrects that setup. Hosted qualification
remains pending. Run `36924331859` completes the audit, native/integration
checks and full Viewer suite successfully on Linux and macOS. Windows rejects
native separators in metadata inventory keys; that independent defect is #139.
The overall run remains failure until the Windows route is corrected.
