---
summary: The noarch Conda package omits three MolSysViewer launchers on Windows.
issue: uibcdf/molsysviewer#101
status: resolved
opened: 2026-09-24
closed: 2026-10-07
severity: medium
verification: reproduced
area: [conda, cli]
guard: tests/test_noarch_conda_launchers.py
normative: devguide/release_gate_evidence.md
blocked_by: []
supersedes: []
---

# Noarch Conda package omits three Windows launchers

**Resolved — 2026-10-07:** the repaired Viewer 0.24.0 noarch build 1 passes
its staged Windows gate, exact-file promotion and the independent public Windows
check. All three installed `.exe --help` commands execute outside the checkout.
The old 0.23.4 artifact and its reproduced failure remain immutable history.

**Reported:** 2026-09-24 by the suite noarch recipe survey.
**Status — 2026-10-06:** Partial; the repaired Viewer 0.24.0 noarch build 1
is staged and its exact Windows launcher job passes in
[37542333568](https://github.com/uibcdf/molsysviewer/actions/runs/37542333568).
The job verifies producer `1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`, version,
build, file hash and installed record, then executes all three `.exe` commands
outside the checkout. Publication and the independent public Windows check
remain pending. See the
[exact candidate receipt](../stabilization_024_preparation_20261006.json).

## What

`pyproject.toml` declares `molsysviewer`, `molsysviewer-qt`, and
`molsysviewer-server`. The noarch Conda recipe omitted their `build.entry_points`, so
the Conda package did not create their Windows launchers.

## How

The recipe should declare the three exact script targets. An installed-package Windows
gate should install one exact staged build and verify its noarch record, channel URL
and SHA-256 before finding and executing all three commands with `--help` outside the
source checkout.

## Why

The Linux build test and source-based CI cannot establish whether Conda created
`Scripts\\<command>.exe` for Windows users. A new noarch build is needed; modifying
the recipe does not change an artifact already published under an immutable coordinate.

## What was refuted

Testing `python -m` would exercise importability rather than the installed launchers.
Running the normal source CI on Windows would not attest the staged Conda artifact.

## Acceptance criteria

- The recipe matches every `[project.scripts]` command and callable target.
- The staged Windows job verifies the exact noarch file and executes all three
  installed commands.
- A new staged build passes that hosted job before promotion or a public repair claim.
- The corresponding public build is independently verified after publication.

## Current state

The exact `entry_points` correction reached `main` through the
`policy-v1.5.2` adoption commit `c35ce1b2`; the earlier dedicated PR
`uibcdf/molsysviewer#108` was closed without a merge. The source now has
Windows jobs for exact staged and public noarch installations. They check the
installed Conda record's version, build, channel URL and SHA-256, find all three
`.exe` launchers inside the environment, and execute each with `--help` outside
the checkout. `tests/test_noarch_conda_launchers.py` checks recipe parity and
the release routes.

The public `0.23.4` tag predates the recipe correction, so its Conda file still
has the defect. Closing requires a new staged artifact, a passing hosted Windows
launcher job, promotion of that exact file, and a passing public Windows job.
Until then, the source fix is not a public repair claim.

Follow-up on 2026-10-01 found a separate promotion-gate defect, recorded in
`uibcdf/molsysviewer#134`: the workflow required the former 21-job pair matrix
and did not require this Windows gate before promotion. The local correction
uses the current four-platform coverage checks and requires a successful
Windows run matching the candidate commit, version, build and SHA-256. Windows
dispatch must use a branch/tag at the same commit as `candidate_sha`; its
checkout validation rejects a different dispatch revision. See
[`../release_gate_evidence.md`](../release_gate_evidence.md#exact-file-promotion-and-windows-launchers).
No new artifact or hosted/public Windows observation has been produced by this
follow-up. #101 therefore remains partial.

## Public artifact reproduction — 2026-10-01

Existing public recheck run `36860171883`, attempt 1, at Viewer commit
`a8aa669c9e3b712f4433511bdf990c5e8df54e30` independently confirms the defect
on `molsysviewer-0.23.4-py_5.tar.bz2`, SHA-256
`85e701449a7310a05d0ab43bdafe98b313d784fd48240f2b6ed53a627a323aeb`.
The shared public registry/index job succeeds and retains verified evidence;
the separate Windows installation succeeds, including the exact installed
record check, then rejects the missing launcher:

```text
verify_noarch_launchers.py:54, verify
    _require(launcher is not None, f"Missing installed launcher: {name}")
verify_noarch_launchers.py:23, _require
    raise ValueError(message)
ValueError: Missing installed launcher: molsysviewer
```

The full workflow conclusion is failure. This is fresh evidence for the
published defect, not repaired-candidate qualification. Native failure log:
`/tmp/msv-shared-verifier-hosted-failure-20261001.log`. No new workflow or
package mutation was requested during this inspection. The repair acceptance
criteria above remain outstanding.


## Public Windows qualification and closure — 2026-10-07

The source recipe fix from `c35ce1b2` is present in published producer
`1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`. The new immutable file is
`molsysviewer-0.24.0-py_1.tar.bz2`, SHA-256
`e31dfb114ab2e49f22b372992d0201455b91849f2631d0165b802069e13abeaa`.
Its staged Windows gate `37542333568` passes candidate checkout, exact package
installation, record validation and all three commands. Promotion `37587274965`
verifies that exact file and moves its label to main without rebuilding it.
The previously recorded independent public matrix `37587631519` passes 16/16.

This review finds the separate post-promotion Windows launcher check had not yet
run for the repaired file. A single read-only dispatch on tag `0.24.0` runs
`verify_public_conda_package.yaml` as `37693319370`. Its actual head is the exact
published producer; current attempt 1 completes with both jobs successful.
The independent label/solver-index verifier passes, then Windows installs
`uibcdf::molsysviewer=0.24.0=py_1` with Python 3.13. From RUNNER_TEMP it verifies
version, noarch build, public URL and SHA-256, resolves each launcher inside
its environment with the `.exe` extension and executes each with `--help`.
The native log explicitly reports all three installed Windows launchers passing.
No tag, release, reconstruction, promotion or duplicated pair dispatch is performed.

Five fresh cases in `tests/test_noarch_conda_launchers.py` pass. Recipe parity
pins the complete set of project scripts and callable targets; additional cases
reject wrong digests/channels and require both Windows release routes to invoke
the installed verifier with exact coordinates. The three help checks establish
installed commands, not visible-window Qt or remote-render certification; #35
remains experimental and remote support remains post-1.0.

Guard: `tests/test_noarch_conda_launchers.py`.
The public receipt ZIP digest is independently compared to GitHub before reading
its bounded JSON. [Exact receipts, native steps and hashes](../remaining_partial_closure_20261007.json).
Cross-suite historical tracking remains uibcdf/molsyssuite#47; the component
repair is complete. The failed old-file run `36860171883` retains its failed
verdict and does not become a pass because the additive release is repaired.
Final 1.0 candidate qualification remains separate.
