---
summary: Scientific test environments omit OpenMM required by the AMBER workflow
issue: uibcdf/molsysviewer#163
status: partial
opened: 2026-10-06
closed:
severity: medium
verification: reproduced
area: [ci, testing, loading]
guard: tests/test_distribution_artifact.py::test_amber_test_environments_include_openmm
normative:
blocked_by: []
supersedes: []
---

# Scientific test environments omit OpenMM required by the AMBER workflow

**Reported:** 2026-10-06 from exact-source run `37438220076`, Linux
job `112185204331`, after the RDKit collection repair.

## What

`tests/test_studio_loading.py::test_complementary_amber_files_remain_one_system`
fails with `NotSupportedFormError` during form detection of the bundled real
`pentalanine.prmtop`/`pentalanine.inpcrd` files. The hosted complete run returns
2,814 passed, 27 skipped and two failures; the other is a development-guide
link to an untracked local prototype.

## How

MolSysMT maps `file_prmtop` and `file_inpcrd` to the optional OpenMM backend.
Their converters use `AmberPrmtopFile`/`AmberInpcrdFile`. The source-pair test
environment supplies MDTraj and RDKit but omits OpenMM, so these form detectors
are unavailable. The shared local environment has OpenMM 8.6.1, masking the
omission in local qualification.

Declare OpenMM in the source/main test recipes and the development recipe;
retain the unconditional real complementary-file regression and guard its
backend dependency. Mandatory Viewer runtime dependencies do not change.

## Why

Scientific qualification must execute the promised complementary-file workflow
in the environment assembled from committed inputs. A skip would not qualify
the existing loading contract.

## What was refuted

This is not evidence that the prmtop/inpcrd files were treated as independent
systems or that their coordinates were corrupted. Form detection fails first
because its backend is absent. The unrelated prototype link must point to the
tracked design record, preserving the local scratch artifacts.

## Resolution

OpenMM is declared in both hosted test recipes and the development recipe.
The 47-case AMBER/distribution/link selection passes locally with the real
bundled files. Removing OpenMM from each of the three recipes in independent
temporary copies makes the backend guard fail with the affected filename.
Exact hosted confirmation remains pending; no complete local suite is repeated.
