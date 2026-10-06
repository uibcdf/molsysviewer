# Candidate evidence for the release gate

**Implemented under `uibcdf/molsysviewer#103`.** The local release gate checks
candidate identity against Git, package version, GitHub runs and actual Conda
environment artifacts. A declaration does not supply a passing verdict.

This closes the automated evidence defect. The release plan still owns the
scientific Interactions qualification, human workflow observations and final
candidate decision. A passing automated check does not supply those missing
observations or authorize publication.

This document defines the local Viewer consumer profile. The shared release
schema and reusable staging policy remain owned by `uibcdf/molsyssuite#27`;
this implementation does not adopt a new ecosystem policy or change publication
workflows. Public documentation reconciliation remains a later block.

## Independent checks

| Step | Required evidence | What it establishes |
| --- | --- | --- |
| `conda` | Exact staging pair run and all installed environment artifacts | The declared pair installs from staging on four platforms and Python 3.11–3.14. |
| `public_conda` | A separate public pair run, its environments, public label and repodata | Those exact files are public, solver-visible and installed together. |
| `hosted_e2e` | Successful hosted core E2E at the Viewer candidate commit | The hosted core browser lane ran successfully for that commit. |

The gate retains the local Python, JS, TypeScript, runtime, performance,
core-browser, citation, version and devguide steps. Staging success satisfies
neither the public nor hosted steps. The public pair does not substitute for
the staging gate for this coordinated candidate. Offline HTML and local browser
results do not substitute for hosted core evidence. Qt standalone remains
experimental, and remote-only suites remain post-1.0.

Before execution, list the checks:

```bash
python devtools/release_gate.py --list
python devtools/release_gate.py --candidate-evidence /tmp/viewer-candidate.json --list
```

Listing does not contact services or verify evidence. An execution of selected
steps is diagnostic; it does not announce complete release clearance:

```bash
python devtools/release_gate.py --candidate-evidence /tmp/viewer-candidate.json \
  --only conda,public_conda,hosted_e2e
```

## Candidate declaration

Supply a reviewed JSON object with `schema: "molsysviewer.release-evidence/1"`.
Keep the record outside the candidate worktree so it does not make that checkout
dirty. Its values are operator expectations, corroborated by independent reads:

| Field | Contents |
| --- | --- |
| `molsysviewer` | Stable `version`, full `commit`, integer `build_number`, `files`. |
| `molsysmt` | Stable `version`, full `commit`, integer `build_number`, `files`. |
| `conda` | Staging pair `{ "id": RUN_ID, "attempt": ATTEMPT }`. |
| `public_conda` | Separate public pair `{ "id": RUN_ID, "attempt": ATTEMPT }`. |
| `hosted_e2e` | Hosted Viewer core run `{ "id": RUN_ID, "attempt": ATTEMPT }`. |
| `exceptions` | Optional bounded declarations for an explicitly selected pre-1.0 assessment. |

Every file record contains `subdir`, `filename`, and its lowercase 64-character
`sha256`. Viewer has exactly one `noarch` file named
`molsysviewer-VERSION-py_BUILD.tar.bz2`. MolSysMT has exactly one native ABI3
file per `linux-64`, `linux-aarch64`, `osx-arm64` and `win-64`, with the declared
version and build in each filename. SHA-256 values come from independently
verified producer/channel evidence, never from a filename or version guess.

The checkout must be clean and at the declared Viewer commit; the imported
Viewer version must equal the candidate version. Untracked files count as dirt.
Freezing a candidate is a separate preparation step, not a mutation performed
by this checker. The declaration records the expected source/artifact mapping;
builders and release maintainers remain responsible for that mapping.

## Acquisition and integrity

The authenticated, read-only `gh api` client reads run metadata, attempt-specific
jobs and artifact inventory. GitHub must corroborate repository, workflow,
commit, run ID, attempt, completed status and success. Pair titles must name
the exact versions/builds, all-platform Python 3.14 matrix and staging/public
source. Jobs must include all 16 distinct platform/Python cells and preparation;
every cell must run its scientific/resource validation successfully.

The hosted core profile permits the completed/skipped state only for the exact
conditional `Check skipped-commit backlog` control job. A duplicate control,
failed control, unknown skipped job or omitted core-test step fails. This rule
does not relax the installed scientific matrices.

Each installed environment comes from the exact named artifact, with its
GitHub SHA-256 checked against the downloaded ZIP. The archive is bounded,
contains only the expected environment text, belongs to the selected run/commit
and was created during or after that attempt. The explicit package URLs must
identify the expected files and channel. Their MD5 fragments are bound to the
declared SHA-256 through consistent registry and repodata records. A matching
filename with a different digest is a failure.

Promotion and independent public verification CI call the common immutable
MolSysSuite action (`uibcdf/molsyssuite#48`, local adoption #133), retaining its
`molsyssuite.public-conda@1` evidence. The local candidate gate binds the
registry/index coordinates, build and MD5/SHA-256 records to its installed
environment artifacts for both staging and main. It does not import or restore
the removed local public-verifier script; shared public poststate verification
remains owned by the provider and its actual workflow calls.

Expired or absent artifacts block qualification: repeat the exact installed
gate rather than approving from its old green conclusion. Duplicate cells or
artifacts, skipped scientific validation, wrong source, commit, build, digest
or attempt are failures. Rerun all cells for a new attempt; retained artifacts
from an older attempt cannot silently satisfy missing new cells. The hosted
check also requires the actual `Run core E2E tests` step to succeed; a green
remote-only job with that step skipped is rejected.

Acquisition uses bounded responses, timeouts and ZIP sizes, retains no secrets,
does not extract files into the checkout, and performs no tags, uploads,
promotions, workflow dispatches or channel changes. Network/access problems
remain missing evidence, not a product pass.

## Exact-file promotion and Windows launchers

The promotion workflow has an additional installed Windows launcher gate
(`uibcdf/molsysviewer#134`, supporting #101). Its required `windows_run_id`
identifies a successful `verify_staged_noarch_launchers.yaml` execution at the
Viewer candidate commit. The title must name that exact version, build and
SHA-256. The candidate checkout, exact staged installation and installed
record/command verification steps must all execute successfully in its
`windows-launchers` job. The installed verifier checks the channel URL and
digest, then executes the three `.exe --help` launchers outside the checkout.

Dispatch the Windows workflow from a branch or tag pointing to the candidate
commit, using that same full SHA as `candidate_sha`; the workflow rejects a
different dispatch revision before installation. For both the Windows run and
the MolSysMT pair run, promotion reads the reported current attempt and checks
that attempt's jobs. Pair matrix/scientific-step checks share the local release
gate's four-platform semantics; the former 21-job matrix is rejected.

This pre-promotion check does not replace complete candidate qualification or
its installed environment artifacts. Closing #101 additionally requires actual
staged Windows evidence for a repaired file, exact-file promotion, and the
independent public Windows verifier. Local guards and a corrected recipe are
insufficient to declare the public launcher defect repaired.

## Results and exceptions

`PASS` means that check's evidence agrees. `FAIL` means available evidence is
invalid or contradicts the candidate. `BLOCKED` means required evidence cannot
be obtained. The complete strict gate returns zero only when every step passes;
failures return 1 and missing evidence returns 2. Unknown or duplicate `--only`
names are usage errors rather than empty successful runs.

An explicit `--pre-release` assessment is restricted to Viewer `0.x.y` and
never announces strict 1.0 clearance. A reviewed exception must name one evidence
`step`, the exact Viewer `version` and `commit`, its owning `issue`, a nonempty
`approved_by` and a bounded `reason`. These fields record a maintainer declaration;
the tool does not grant or authenticate approval. It reports missing evidence
covered by that declaration as `EXCEPTION`, never as `PASS`, and returns 2.
Contradictory evidence still fails. Strict 1.0 rejects exception records and the
pre-release mode even if all other evidence is green.

Before publication, a staging-only result is a milestone and public checks may
still be blocked. After promotion/publication, read the public evidence
independently. This state separation does not authorize publishing a candidate
that lacks the other required pre-public checks.

## Regression evidence

`tests/test_release_evidence.py` checks positive staging/public/hosted cases and
rejection of candidate drift, incomplete matrices, skipped core/scientific
steps, wrong environment URLs/digests, stale archives, missing evidence and
misapplied exceptions. `tests/test_release_gate.py` protects local step selection,
nonzero blocked results and the original runtime-version checks.

The reader was also exercised with public historical run `36129993869`,
attempt 1, artifact `10861931707` (`linux-aarch64`, Python 3.13). Its ZIP digest,
run association, installed URLs and live MD5/SHA-256 channel bindings pass.
That old five-platform run remains historical evidence; it is not reused as
the current four-platform candidate's complete matrix or release clearance.
Local acquisition log: `/tmp/msv-release-real-probe-20261001.log`.
