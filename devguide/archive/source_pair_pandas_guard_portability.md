---
summary: Reject invalid source-pair pandas versions explicitly across Bash implementations.
issue: uibcdf/molsysviewer#295
status: resolved
opened: 2026-11-04
closed: 2026-11-04
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
The hosted receiving below supplies the macOS evidence; local Linux checks alone
would not qualify it. No runtime code, dependency floor, package, candidate,
public tag or publication changes.

The separate MolSysMT PR #543 matrix originally passed seven cells. Its macOS
Python 3.12 cell was cancelled without executed steps: GitHub's annotation
states the hosted runner was not acquired and reports macOS arm64 capacity
constraints. Only that job was requested again; original successful cells and
the failed aggregate remain preserved. Owner review and installed receiving
remain separate from this Viewer defect.

## Resolution

Commit `793a92db38c4074dd042d220ac1e49191a9b2905` adds an explicit invalid-version
branch and `exit 1`, preserving the numeric pattern and provisioning order.
The guard named above executes fourteen valid/invalid input cases with normal
options and disabled implicit errexit. The old script fails five local mechanism
controls; the repaired scoped checks pass 100 distribution/workflow cases.

Source-pair run [41899772394](https://github.com/uibcdf/molsysviewer/actions/runs/41899772394)
completes successfully on Linux, Windows and macOS using that exact Viewer
source and MolSysMT `46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`.
All three original artifact ZIP hashes match GitHub; the original JUnit contains
all fourteen guard cases passing on each host, without failure/error/skip.
This directly receives the macOS rejection mechanism instead of inferring it
from another platform.

| Host | Python passes / skips | Original artifact | ZIP SHA-256 | JUnit SHA-256 |
| --- | ---: | ---: | --- | --- |
| macOS | 3,382 / 56 | 13361915524 | `b0bc75317f0b6d00de328a7615a357cafc26c3c8aae377fa6c00e13175b5137c` | `70dff1f3972ca2d292faace9ce172a3a1e563c227cd977dca4087b4781d61714` |
| Windows | 3,382 / 56 | 13359390497 | `e805d1ce41a57a30b94d4769a8b9391116fa03b0240f4fe6d52fb12e6b074be3` | `8ff82c9cbdb32394f60f73a5cf307ecd334075987411a2725d51b51f761d33fe` |
| Linux | 3,409 / 29 | 13357399837 | `8b83b65e1e159dd39d88b2e58441f738314b06cd9abc5ad9c4ddafab3e7513bf` | `4d96ef9c969e1fcb124e79eb58dddfe157a3f3c5b3c35ab64e0ad155a7506ea7` |

Every JUnit has zero failures/errors; omissions outside the guard remain visible.
The original source-pair failure 41884513993 and general CI failure 41884513983
are preserved. General CI 41899772338 passes its four Linux minors; its four
macOS cells remain queued at closure receiving. This bug resolution does not
declare that separate overall matrix successful, qualify a public installed
artifact, or authorize publication. Source ZIPs and their parsed summary remain
in `.pytest_cache/guard295-hosted-source-20261104/` until CI closeout.
