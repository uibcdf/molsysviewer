---
summary: Temporary candidate tags change capability release history during qualification.
issue: uibcdf/molsysviewer#171
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [ci]
guard: tests/test_source_workflow_coverage.py::test_temporary_candidate_tags_are_removed_after_installation
normative:
blocked_by: []
supersedes: []
---

# Temporary candidate tags change capability release history

**Reported:** 2026-10-06 in the 0.24.0 staging qualification.

## What

Staging CI run `37538531865`, exact Viewer `6c4ddba31c289a27f761576c07fa641603c4392e`,
Linux Python 3.13 job `112525547372`, returns 2,875 passes, 27 skips and one
failure: `tests/test_capability_audit.py::test_the_generated_document_is_current`.
Interactions changes from `unreleased` to `0.24.0` solely because the job creates
an unpublished local tag for versioningit. The same tag is present in the local
installed qualification snapshot.

## How

The source/staging jobs build exact metadata using a local canonical version tag.
They retain it after installation. `devtools/capability_audit.py` queries all Git
tags containing the capability's adding commit and consequently sees a release
that has not been published. The generated document correctly still says
`unreleased`; it must not be rewritten to claim publication.

Record ownership only inside the branch creating a new local tag. After installing
the package, remove that owned tag, checking its target before deletion. Preserve
a tag that existed before the job. Apply this lifecycle to source-pair and staged
Python/browser jobs. Installed version files and distribution metadata remain
exact; the source tag is a temporary build input. The Conda producer retains its
build input while packaging and does not run the history-sensitive source suite.

## Why

The defect blocks release qualification despite passing scientific checks. A
source-only workflow correction requires a new reviewed candidate commit and a
new immutable build number; the already uploaded `0.24.0` build 0 stays intact.

## What was refuted

Regenerating the document with the candidate tag present would announce an
unpublished release. Changing the capability guard would hide the mismatch.
The native Qt/WebGL failure is separate and remains experimental under
uibcdf/molsysviewer#109. No molecular API or detector change is implicated.

## Progress

Creation outputs and guarded cleanup are implemented. A workflow regression
asserts installation precedes cleanup, ownership is emitted only for newly created
tags, cleanup checks the tag target, and preexisting tags are preserved. The focused validation and original failed full installed outcome are recorded below.

## Resolution

**Resolved in source — 2026-10-06.** 231 focused checks pass; removing only the owned local tag in the isolated snapshot passes all 208 capability checks while installed Viewer remains 0.24.0. The once-run full Conda attempt retains its 2,877 passes, 25 skips and one history failure; it is not relabelled a full pass.
The next candidate uses a new source commit and Conda build 1. Build 0 and its
original failures remain preserved; no published tag or artifact is moved.
