---
summary: Installed scientific CLI cannot resolve its development fixtures
issue: uibcdf/molsysviewer#153
status: partial
opened: 2026-10-03
closed:
severity: medium
verification: reproduced
area: [testing, installed_artifacts, interaction]
guard: tests/test_installed_test_imports.py::test_direct_family_cli_uses_installed_science_without_checkout_on_sys_path
normative: devguide/installed_artifact_qualification.md
blocked_by: []
supersedes: []
---

# Installed scientific CLI cannot resolve its development fixtures

**Reported:** 2026-10-03, integrated installed-wheel core browser qualification.

## What

With `MOLSYSVIEWER_TEST_INSTALLED=1`, the direct family CLI invoked by the Interactions browser suite raises `ModuleNotFoundError: No module named 'devtools'`. The candidate Viewer wheel is `0.23.4+71.g3b475639.dirty`; the experimental provider wheel is `0.22.4+122.g396e6979f`. The first core attempt reached suite 20/36 and stopped there; it is not a passing core result.

## How

`devtools/qualify_interaction_families.py` avoids prepending the scientific checkout correctly, then imports a fixture namespace that its direct CLI never bound. The installed pytest runner bound that namespace separately. The detector benchmark has the same installed CLI boundary.

One private reusable helper now binds only `devtools` to the selected fixture checkout and refuses an existing conflicting namespace. Family CLI, detector CLI and installed runner share it. It does not alter `sys.path`, provider methods or scientific module-origin checks.

## Why

Actual installed-artifact and browser qualification must consume real scientific fixtures while keeping scientific packages in site-packages. The regression executes the direct isolated CLI for all ten real family fixtures and verifies both versions and imported module paths.

## What was refuted

Adding the repository to `PYTHONPATH` would hide the defect by shadowing installed scientific packages. Skipping the family geometry checks would remove the observation the lane must make. Neither is used.

## Resolution

Fix implemented. All four installed import/CLI guards pass, including the real
ten-family isolated subprocess. After the once-run full attempt failed, the
195-case static/import correction selection also passes with installed artifacts.
The helper binds only the development fixture namespace; the guard checks actual
scientific origins, versions and positive calculated observations. Qualification
uses the wheel `0.23.4+71.g3b475639.dirty` and experimental provider
`0.22.4+122.g396e6979f`.

The full attempt retains 15 failures and 44 errors, including exhausted disk
space, two qualification-copy omissions and a native CLI exit of -11 whose
cause is unproven. The later passing subprocess is a scoped recovery, not a
passing full suite. Keep partial until reviewed product/tool integration and
qualification. The original core failure remains in
`/tmp/msv-integration-core-e2e-20261003.log`; counts and artifact identity are in
`devguide/integration_qualification_20261003.json`.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).
