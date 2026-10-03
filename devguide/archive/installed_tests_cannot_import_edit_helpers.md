---
summary: Installed-package tests cannot import local edit helpers.
issue: uibcdf/molsysviewer#131
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: medium
verification: reproduced
area: [testing, distribution]
guard: tests/test_installed_test_imports.py::test_edit_helper_consumers_import_without_the_tests_directory_on_sys_path
normative:
blocked_by: []
supersedes: []
---

# Installed tests cannot import edit helpers

**Reported:** 2026-10-01, isolated installed-wheel validation with public dependencies.

## What

`MOLSYSVIEWER_TEST_INSTALLED=1 python -I -m pytest --import-mode=importlib`
fails while collecting `tests/test_selections.py`, with
`ModuleNotFoundError: No module named '_edit_helpers'`. Seven load tests pass
first against the installed wheel and public MolSysMT 0.22.4.

## How

Seven test modules import `from _edit_helpers import ...`. Development's default
pytest path insertion resolves that name; importlib mode avoids inserting the
tests directory. Give the helpers an explicit tests package and qualify those
imports. Preserve the scientific-package site-packages guard.

## Why

Installed-artifact validation must collect the actual reconciliation tests
without importing molecular libraries from their development checkouts.

## What was refuted

The installed package imports successfully and its dependencies satisfy pip's
requirements check. This is test-helper resolution, not an incompatible
scientific package or a molecular viewer failure. Adding the source checkout
to PYTHONPATH would weaken the evidence and is unnecessary.

## Resolution

Resolved 2026-10-01. Define the explicit tests package and qualify the seven
edit-helper imports. The first full development attempt exposed two additional
bare `conftest` collection imports; qualify those and the function-local addon
reference as well. No production library or source-location assertion changes.

The guard starts isolated Python outside the repository, loads the real tests
package, imports all ten consumer modules and verifies the actual helper and
conftest origins without putting the tests directory on sys.path. Restoring
either a bare edit-helper import or a bare lifecycle conftest import makes it
fail with the respective ModuleNotFoundError. Both mutations restore exact
original bytes in finally blocks.

In the public-dependency installed environment, the guard and lifecycle,
teardown and addon selection passes 59 tests; the same selection passes in
development. The original eight-file development selection passes 89 tests.
Whole-suite collection then passes after the remaining import corrections.
The initial full attempt stopped during collection and is not reported as a
passing full regression or repeated. Earlier full product validation remains
separate evidence.

The current installed Viewer wheel additionally passes seven load, 108 public
workflow and eight offline Chrome export tests. See
[the artifact qualification](../installed_artifact_qualification.md) for exact
versions, hashes and the distinction from compatible Interactions qualification.

Logs: `/tmp/msv-installed-test-import-20261001.log`,
`/tmp/msv-installed-helper-mutation-20261001.log`,
`/tmp/msv-installed-conftest-mutation-20261001.log`,
`/tmp/msv-installed-lifecycle-20261001.log`,
`/tmp/msv-installed-source-specific-20261001.log`,
`/tmp/msv-installed-source-lifecycle-20261001.log`,
`/tmp/msv-installed-source-full-20261001.log` (aborted collection) and
`/tmp/msv-installed-source-collection-20261001.log`.
