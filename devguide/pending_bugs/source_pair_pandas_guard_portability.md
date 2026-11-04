---
summary: Reject invalid source-pair pandas versions explicitly across Bash implementations.
issue: uibcdf/molsysviewer#295
status: partial
opened: 2026-11-04
closed:
severity: medium
verification: reproduced
area: [ci, validation]
guard: tests/test_source_workflow_coverage.py::test_source_receiving_rejects_nonversion_pandas_inputs_before_provisioning
normative:
blocked_by: []
supersedes: []
---

# Source-pair pandas input rejection depends on implicit shell exit

## What

Commit `afd61eb16024a43042095a450609774202167363` passes the four Linux
Python 3.11–3.14 cells in CI 41884513983, with 3,396 passes per cell. Its four
macOS cells fail only the three invalid pandas-version cases, each retaining
3,366 passes. Source pair 41884513993 passes Linux and Windows, while macOS
fails the same three cases. Their authoritative failure conclusions remain.
The original public-provider Pandas4Warning failures are absent in this run;
this is a distinct workflow-validation defect.

## How

The regression executes the workflow's actual validation script through Bash
stdin. On hosted macOS `/bin/bash`, invalid inputs reach the final successful
`Platform scope` echo after the bare `[[ ... =~ ... ]]` command fails. The
script relies on implicit `set -e` handling instead of rejecting explicitly.
The recorded logs establish the behavior of the selected executable, without
claiming a measured Bash version or a general macOS runtime defect.

Locally disabling implicit errexit reproduces five incorrect acceptances,
including empty and newline-terminated inputs added to the regression. The
unfixed selection yields five failures and nine passes. This is a mechanism
control, not a local macOS execution.

## Why

The scientific source baseline must remain a single exact numeric version
before environment provisioning. A shell-dependent rejection weakens that
contract and prevents the full required matrix from completing. The fix uses
an explicit invalid-version branch, diagnostic and `exit 1`, retaining the
existing numeric pattern, provisioning order and platform/candidate rules.
The regression checks both normal options and disabled implicit errexit.

## Receiving and remaining work

Local affected-module and distribution checks are recorded in the
[receiving receipt](../ci_guard_portability_receiving_20261104.json).
Original hosted captures and red/green JUnit remain in `.pytest_cache/`.
Review committed-head hosted results before archiving this report; local Linux
checks do not qualify macOS. No runtime code, dependency floor, package,
candidate, public tag or publication changes.

The separate MolSysMT PR #543 matrix originally passed seven cells. Its macOS
Python 3.12 cell was cancelled without executed steps: GitHub's annotation
states the hosted runner was not acquired and reports macOS arm64 capacity
constraints. Only that job was requested again; original successful cells and
the failed aggregate remain preserved. Owner review and installed receiving
remain separate from this Viewer defect.
