---
summary: Installed scientific CLI cannot resolve its development fixtures
issue: uibcdf/molsysviewer#153
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: medium
verification: reproduced
area: [testing, installed_artifacts, interaction]
guard: tests/test_installed_test_imports.py::test_direct_family_cli_uses_installed_science_without_checkout_on_sys_path
normative: devguide/installed_artifact_qualification.md
blocked_by: []
supersedes: []
---

# Installed scientific CLI cannot resolve its development fixtures

**Resolved — 2026-10-07:** all four installed import/CLI guards pass on the
original promoted Viewer 0.24.0 / MolSysMT 0.23.0 files. The public 16/16 pair
qualification removes the former publication blocker. Earlier dated sections
retain their historical artifact and failed-attempt scope.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

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


## Public qualification and closure — 2026-10-07

The private namespace helper, family/detector CLIs, installed qualifier and its
four-case regression module match the published Viewer producer `1a4c97a5` byte
for byte. Fixtures still come from the selected checkout; the helper does not
put that checkout on the scientific import path or package fixture tools into
the runtime wheel. No further implementation change is required.

Four fresh installed cases pass with Viewer 0.24.0 and MolSysMT 0.23.0 origins
verified before and after collection. The direct family guard executes an
isolated subprocess outside the checkout, confirms both versions and exact
site-packages origins and requires positive observations for all ten real family
fixtures. Other cases cover fixture consumers without test-directory discovery,
installed metadata precedence and rejection of a real source scientific module.
The standalone worker guard also passes against the same installed pair.

The original staging files were promoted unchanged; these local checks are not
new public-URL installations. Public-URL run `37587631519` independently qualifies
all sixteen cells. Existing exact-source pair `37685753081` passes three Python
3.14 hosts, and core `37685752799` passes all 39 suites on unchanged fixture tools.
Their reuse does not replace the preserved earlier failed full/CLI attempts.
The former -11 cause remains unproven; subsequent positive results do not erase it.

Guard: `tests/test_installed_test_imports.py::test_direct_family_cli_uses_installed_science_without_checkout_on_sys_path`.
[Final evidence and qualification boundaries](../remaining_partial_closure_20261007.json).
Final 1.0 artifact qualification remains separate; published files are unchanged.
