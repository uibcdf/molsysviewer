---
summary: Npm publication rejects an already synchronized release version.
issue: uibcdf/molsysviewer#176
status: resolved
opened: 2026-10-07
closed: 2026-10-07
severity: high
verification: reproduced
area: [release, npm]
guard: tests/test_npm_publish_workflow.py::test_npm_version_injection_accepts_synced_and_stale_manifests
normative:
blocked_by: []
supersedes: []
---

# Npm publication rejects an already synchronized release version

**Reported:** 2026-10-07, authorized publication of Viewer 0.24.0.

## What

The tag-triggered run [37584736989](https://github.com/uibcdf/molsysviewer/actions/runs/37584736989)
fails in `Inject version and repo info` with `npm error Version not changed`.
Build and publish never execute. The public tag remains fixed at `1a4c97a5`;
Conda build 1 remains staged with its original SHA-256.

## How

The npm workflow calls `npm version $CLEAN_VERSION --no-git-tag-version`.
The already qualified manifest contains 0.24.0. npm rejects an unchanged
version unless explicitly allowed. Add `--allow-same-version`, preserving
canonical version validation, exact-tag checkout and no additional npm trigger.

## Why

The npm/CDN runtime is needed by public HTML exports. This is a publisher
workflow defect, not a reason to modify or move the qualified source tag.

## What was refuted

No npm package was published by the failed run. Retrying the unchanged workflow
would repeat the same failure. Recovery uses the corrected workflow on main
with explicit tag 0.24.0; Conda is promoted without rebuilding.

## Resolution

The workflow correction and real-npm guard pass **3 tests**. Ruff checks pass.
The full suite runs once: **2,882 passed, 23 failed, 23 skipped**, 482.21 s.
Twenty-two failures are sandbox socket/Chromium/Qt restrictions; the generated
capability inventory also changes after tagging and has been regenerated.
Outside-sandbox follow-up passes **261 tests, one skip**, then stops at an
export notice caused by an unrelated ignored local `_version.py` from an older
development checkout. Eight actual canonical installed-package exports pass
without that mismatch. The two Qt transport checks pass after activating the
required 3.14 environment; the shell had retained `CONDA_PREFIX` from 3.13.
The full suite is not repeated or described as green. Logs are retained in
`/tmp/msv-024-npm-recovery-*-20261007.log` and the maintained candidate receipt.
The correction is pushed in `493f6eb6`. Manual recovery run
[37586395370](https://github.com/uibcdf/molsysviewer/actions/runs/37586395370)
checks out the fixed tag at `1a4c97a5`, builds version 0.24.0 and completes
`npm publish` successfully with signed provenance. npm accepts the upload and
reports asynchronous processing; independent public registry/CDN availability
remains a publication check in the candidate receipt, not a failed version command.
The guard executes that workflow command against both synchronized and older
real manifests; removing the flag makes the synchronized case fail.
