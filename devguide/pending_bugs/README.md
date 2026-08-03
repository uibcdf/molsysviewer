# Pending Bugs

This directory contains confirmed or reproducible defects that affect current
MolSysViewer behavior. Bug reports are evidence and implementation queues, not
future API proposals.

Each report should state the affected public contract, reproduction, cause,
recommended correction, and acceptance tests. Move resolved reports to an
archive only after the implementation and regression tests are complete.

## Current triage

- [`docs_lite_views_pinned_to_unpublished_npm_version.md`](docs_lite_views_pinned_to_unpublished_npm_version.md):
  the docs build rewrites every lite view's CDN link to the current version
  without checking that it exists. npm stops at `0.7.0`, Python is at `0.20.0`,
  so the next docs deploy breaks all twelve interactive views at once — with a
  green Sphinx build. Verified against the deployed site and the registries.
- [`standalone_qt_live_demo_reload.md`](standalone_qt_live_demo_reload.md):
  replacing a loaded demo does not update the real Qt scene. It requires a real
  Qt/WebGL window for the next diagnostic pass.

The movie camera-snapshot defect is confirmed but explicitly deferred under
[`post_1.0/`](post_1.0/README.md).

The former color-digester finding is resolved: `value_range.py` and
`replace.py` exist, their public surfaces are covered by
`tests/test_argdigest_public_api.py`, and the obsolete bug file is no longer
present.

## Recommended execution

The active Qt report is one real-window validation block:

1. Reproduce each defect separately in the supported Qt/WebGL environment.
2. Add temporary, runtime-only diagnostics at both sides of the bridge. Record
   message/generation identifiers and acknowledgements; do not add diagnostic
   events to scene history or export.
3. Identify the first boundary where the expected state disappears.
4. Add the narrow automated regression test at that boundary.
5. Confirm the corrected workflow in the real window before closing the bug.

Fakes remain useful for the regression after the cause is known. They are not
evidence that the original real-window symptom is fixed.

No other bug work should be invented from stale plans. New dogfooding findings
enter this directory only with a reproduction and an affected public contract.
