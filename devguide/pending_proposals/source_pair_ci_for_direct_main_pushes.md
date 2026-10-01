---
summary: Run Python 3.14 source-pair CI on direct main pushes.
issue: uibcdf/molsysviewer#137
status: active
opened: 2026-10-01
closed:
verification: reproduced
area: [ci, tooling, dependencies]
guard: tests/test_python_ecosystem_contract.py
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Source-pair CI for direct main pushes

## What

The accepted principal-maintainer development flow uses commits and direct
pushes. Python 3.14 source-pair CI originally accepted PRs or a manually declared
frozen release candidate, leaving an ordinary main source change without an
equivalent development trigger.

## How

Add main pushes using the same paths as PRs. Preserve the exact provider pin,
three platforms, scientific checks and full test selection. Keep manual
candidate runtime/tag identity checks restricted to `workflow_dispatch`.

## Why

The published tooling commit `51872849` passes normal CI `36919958270` and
core E2E `36919958463`. Manual source-pair run `36920527376` correctly refuses
the historical `0.23.4` tag pointing to another commit, before installation and
the new audit; that rejection is not an audit result.

## What was refuted

Moving a published tag, weakening the manual candidate check or claiming the
failed manual run as scientific evidence would violate its identity contract.
The manual invocation was inappropriate for an ordinary development commit.
GH Run Receptor selected a preceding PASS line as the root cause; native logs
settle the subsequent silent shell assertion failure. Provider feedback is
recorded in `uibcdf/gh-run-receptor#56`.

## Resolution

Push routing and its configuration guard are implemented at `78bb4565`.
Focused qualification passes 165 tests. Push run `36922358875` executes the
installed-source audit on all three platforms and correctly rejects the stale
default provider below the runtime floor; remediation is tracked in #138.
Normal CI `36922358871` and core E2E `36922358989` pass. Complete source-pair
scientific qualification remains pending the corrected provider run.
