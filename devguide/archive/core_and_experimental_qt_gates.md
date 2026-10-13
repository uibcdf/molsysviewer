---
summary: Separate core release gates from experimental native Qt diagnostics.
issue: uibcdf/molsysviewer#231
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [ci, release, testing]
guard: tests/test_core_qt_gates.py
normative:
blocked_by: []
supersedes: []
---

# Separate core gates from experimental native Qt diagnostics

**Reported:** 2026-10-13 during the authorized review before documentation.

## What

CI PR aggregation, the local Python release step and the nightly recovery
watermark require experimental Qt success, despite its accepted scope outside
core 1.0. Source f272e384 has six scientific cells, three Python 3.14 hosts,
43 core browser suites and 25 notebooks passing; the official CI workflow
remains failed on Qt WebGL initialization. The local full run contains eight
Qt context failures. Those observed failures retain their original verdicts.

## How

Keep pure Python/bridge contract tests in core. Mark only real native Qt
process/window/GPU/resource probes, use explicit core selection in gates and
source CI, and preserve all native diagnostics in an independent workflow.
Recover deliberately skipped core and Qt commits with separate watermarks.

## Why

Installing an optional binding must not turn an experimental host failure into
a core release failure. Conversely, a passing core must not certify Qt, hide its
failed diagnostics or clear its separate backlog. #35/#109/#113 own Qt fixes
and certification; this issue owns validation selection and wiring.

## What was refuted

`continue-on-error` and broad removal of standalone tests would blur failures
or lose core contract coverage. The change uses a dedicated failed-capable
workflow and narrow runtime markers. Source inspection identified the wiring;
executed collection/behavior and applicable regression evidence follow below.

## Resolution

The actual pytest collection guard confirms exactly 12 native Qt cases and
retained pure bridge/Chromium cases. Workflow scope/failure wiring and unknown
failed/skipped core jobs are guarded in `tests/test_core_qt_gates.py`; recovery
watermarks in `tests/test_ci_backlog.py`; the local release command in
`tests/test_release_gate.py`. The scoped group passes 18/18. Receptor/tagging/
distribution guards retain coverage and exact candidate handling.

The single complete **core** run passes 3,095 tests, 21 skips and zero failures
or errors in 554.873 seconds. Its complementary 12 Qt cases are deliberately
outside this core selection, not passing Qt evidence. The existing Qt runtime
failures remain under their owners and retain their original official verdicts.
Configuration validates with nine exact GH Run Receptor workflow rules.

The maintained normative scope is `devguide/core_qt_qualification.md`; receiving
provenance and source/artifact boundaries are in
`devguide/core_qt_qualification_20261013.json`. Current devguide reconciles the
prior terminal f272e384 results, resolved Studio/Interactions status and the
order docs → candidate build/qualification → installed first contact before
publication. Remote guide-only work and unrelated sandbox files are preserved.
Viewer 0.25.0 remains unfrozen and both 1.0 publications stay paused.
