---
summary: NPM publisher runs twice for one version on tag push and GitHub Release
issue: uibcdf/molsysviewer#104
status: resolved
opened: 2026-09-25
closed: 2026-09-25
severity: medium
verification: reproduced
area: [release, npm, ci]
guard: tests/test_npm_publish_workflow.py
normative:
blocked_by: []
supersedes: []
---

# NPM publisher runs twice for one version

**Reported:** 2026-09-25, while publishing the 0.23.4 GitHub Release after
the tag had already published the npm runtime.

## What

The tag-push workflow run 36126333127 published
`@uibcdf/molsysviewer@0.23.4` successfully. The subsequent GitHub Release
launched run 36127895008, which attempted to publish the same immutable npm
coordinate and reached a failing publish step. The public package and CDN
bundle were independently reachable before that second run.

## How

`.github/workflows/npm-publish.yaml` subscribed to both `push.tags` and
`release.published`. A GitHub Release following a tag is the normal sequence,
so the two triggers were not alternatives. Keep tag push as the sole automatic
npm trigger, retain deliberate manual dispatch without an old-version default,
and leave GitHub Release to the separate Conda and Zenodo paths.

## Why

The redundant run wastes CI time and makes a successful release appear red.
It also obscures a real npm failure, which requires the registry and CDN to be
verified independently of step success.

## What was refuted

The second npm run was not needed to complete the release: the exact 0.23.4
package was already visible in the npm version index, and the CDN returned
HTTP 200 for `dist/viewer.js`.

## Resolution

Removed the `release.published` trigger, made manual dispatch require an
explicit tag rather than defaulting to 0.5.3, and documented the single
automatic route. `tests/test_npm_publish_workflow.py` rejects a second
automatic trigger and guards the explicit manual input. The focused pytest
run passed. The already completed duplicate run remains historical evidence;
its outcome does not affect the successful tag-push publication.
