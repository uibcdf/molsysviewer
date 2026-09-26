---
summary: Public noarch promotion succeeds but final verifier exits one
issue: uibcdf/molsysviewer#105
status: active
opened: 2026-09-25
closed:
severity: medium
verification: reproduced
area: [release, conda, ci]
guard:
normative:
blocked_by: []
supersedes: []
---

# Public noarch promotion succeeds but final verifier exits one

**Reported:** 2026-09-25, during promotion of MolSysViewer 0.23.4 build 5.

## What

Run `36128473826` passed `Promote the exact staged artifact` and uploaded
`molsysviewer-conda-promotion-0.23.4-py_5`, then marked the job failed in
`Independently verify the public package record`. That final step printed
`https://conda.anaconda.org/uibcdf/noarch/molsysviewer-0.23.4-py_5.tar.bz2`
and immediately exited 1.

## How

The precise shell exit-1 mechanism is not yet established. The duplicated
post-promotion check is in `.github/workflows/promote_conda_package.yaml`.
Separate it into a read-only, independently rerunnable verifier with a test
for the full success path. Coordinate the pattern with MolSysMT through
`uibcdf/molsyssuite#48` and the broader proposal `uibcdf/molsyssuite#27`.
Do not rerun the promotion mutation merely to change the workflow conclusion.

## Why

An operator sees a failed release workflow despite a public package. The
failure should be investigated, not reinterpreted as a missing package or
waived without independent evidence.

## What was refuted

The exact noarch file is not absent: the promotion action verified its target
label and SHA-256; a separate Conda search found the same public URL and
digest `85e701449a7310a05d0ab43bdafe98b313d784fd48240f2b6ed53a627a323aeb`.
The public installed-pair matrix passed all 20 cells in MolSysMT run
`36129993869` with public-channel provenance.

## Resolution

The original shell exit-1 mechanism remains undiagnosed: the step log prints
the correct URL and then reports status 1 without a traceback. A replacement
is in progress. `devtools/conda-build/verify_public_package.py` checks the
public Anaconda release API for the exact basename, SHA-256 and `main` label,
then checks the public `repodata.json` entry for solver visibility. It retries
bounded propagation but fails immediately on a wrong digest.

The promotion workflow now calls that script. A separate
`verify_public_conda_package.yaml` dispatch calls the same script without a
publication token or promotion action. Local positive/negative tests pass,
and a live read-only invocation passed for the public noarch build-5 file.
Hosted execution of the new workflow remains to be verified before closing
this report; the old failed run does not become green retroactively.
