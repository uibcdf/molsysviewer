---
summary: Historical GitHub Release recovery is superseded by verified 0.24.0.
issue: uibcdf/molsysviewer#82
status: superseded
opened: 2026-09-05
closed: 2026-10-07
verification: inspected
area: [release, distribution]
guard:
normative: devguide/release_and_citation.md
blocked_by: []
supersedes: []
---

# Historical GitHub Release recovery is superseded by verified 0.24.0.

**Recorded:** 2026-10-07 while reconciling the existing issue; this date records the local report, not the original issue opening.

## What / how / why

Tags 0.22.0 and 0.23.0 remain fixed, without GitHub Releases or matching source preservation being retroactively claimed.

## Resolution — explicit maintainer decision, 2026-10-07

The maintainer declines historical backfill because the verified new version supersedes the scenario. Close this issue as superseded, not delivered. Viewer 0.24.0 has a public Release, verified Conda/npm/CDN and version-specific Zenodo source archive. No historical tag is moved and no old package is published.

Prevent recurrence through the maintained release checkpoint: inspect the exact npm workflow completion, verify public package/CDN identity and bytes, public Conda/installed evidence and Zenodo before declaring publication complete. Existing `tests/test_js_build_version_resolution.py` and `tests/test_npm_publish_workflow.py` protect the resolved build/version failure mechanisms; operator verification remains required.
