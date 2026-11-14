---
summary: Repair source checkpoint guards and notebook-artifact attribution.
issue: uibcdf/molsysviewer#386
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: reproduced
area: [ci, testing, portability, evidence]
guard: tests/test_source_workflow_coverage.py::test_notebook_failure_artifacts_require_the_actual_executor_to_fail
normative:
blocked_by: []
supersedes: []
---

# Source checkpoint recovery — resolved in source

Run `43553954846` on MolSysViewer `def5f417` and MolSysMT `aee7aa65`
fails all three Python 3.14 hosts. Seven original ZIPs match GitHub's sizes
and SHA-256. Linux passes 4,722 cases with one failure/42 skips; macOS
passes 4,691 with one failure/73 skips; Windows passes 4,694 with two
failures/69 skips. Seventeen Qt cases are deselected on each host.

The shared failure is a stale three-command pytest inventory after the
explicit encoder-diagnostic branch adds a fourth command. The correction
reviews all four roles and retains receptor/rerun, full-suite, JUnit and
bounded diagnostic assertions. Windows additionally exposes native path
separators in the documentation iterator's string identity. Normalize both
Markdown and notebook identities to POSIX, with real PureWindowsPath and
PurePosixPath controls; retain global deprecated-example coverage.

The Linux notebook executor and kernel registration are skipped, but the
broad failure uploader publishes 27 tracked historical logs. Every byte
matches the repository copy: this is not evidence of current notebook
execution or failure. Bind diagnostic publication to the actual executor's
failed outcome. Preserve historical logs and the original artifact.

All 61 codec/export cases pass without omissions on every host, including
Windows automatic AV1 with the formerly failing executable. The twelve
original Unicode decoding failures also pass on native Windows. These
received corrections belong to #385/#169; neither successful subset makes
the complete checkpoint green. Full core/notebook gates were not reached.

The complete four-page, 356-issue history has no equivalent focused report.
Receive scoped guard/negative controls, neighboring route/documentation
checks, then one new full source checkpoint. No renderer, scientific
assertion, media quality or operation deadline changes are needed.

Scoped `795` passes 89 affected cases and final Ruff lint/format. Broader
`796` passes 620 neighboring route/governance cases; its two document-link
failures reflect a not-yet-created receipt and unindexed new archive paths.
After completing those records, `797` passes all 451 link/reporting checks.
Inputs are unchanged and owned cleanup is clean in each profile. The
[receipt](../source_checkpoint_recovery_20261114.json) retains the original
failure and separate scopes. At that initial local checkpoint, native Windows and complete source/core
receiving of this correction remained pending; terminal results follow below.

Published correction `22b51f89a7edb50da15103a399b71ae663d1ffae` is selected
by the single full source checkpoint `43616029893`, with frozen MolSysMT
`aee7aa65`, all three Python 3.14 hosts and the full Linux core/notebook
lane. Native terminal receiving passes 4,724 Python cases on Linux, 4,693
on macOS and 4,697 on Windows, with zero failures/errors. The respective
42/73/69 skips and seventeen deselected Qt cases retain their explicit scope.
Linux executes all 25 documented notebooks successfully; its failure-log
uploader is correctly skipped and no stale notebook artifact is emitted.
All six original ZIPs independently match GitHub's sizes and SHA-256.

This closes the command inventory, portable-document identity and actual-
producer artifact defects. The guard above protects artifact ownership;
`test_python_ecosystem_contract.py` protects all four command roles and
`test_documentation_pages_run.py` protects native path identities plus global
deprecated-example coverage. The original failed run remains failed. Overall
`43616029893` still fails the independent aggregate controls budget under
reopened #244; current source and installed qualification remain separate.
