---
summary: New E2E catch handlers violate the fail-fast exit contract.
issue: uibcdf/molsysviewer#375
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: reproduced
area: [tests, lifecycle, ci]
guard: tests/test_e2e_reliability.py::test_e2e_failures_cannot_leave_chromium_alive_until_timeout
normative:
blocked_by: []
supersedes: []
---

# Resolved: terminal E2E failure exits

The existing failure-exit guard rejects eight entries using `process.exitCode`
instead of the required `process.exit(1)`: source-atom-indices and Movie
appearance/export/seek/story/composition/web/legacy. Controlled receiving
`692` retains the native assertion, JUnit and unchanged inputs. This observes
a contract failure, not a demonstrated resource leak or actual browser hang.

The correction changes only each terminal catch, after its existing awaited
`finally` cleanup. Keep all browser/bridge release, fixture ownership, stderr
and scientific assertions. The existing
`tests/test_e2e_reliability.py::test_e2e_failures_cannot_leave_chromium_alive_until_timeout`
guard passes in `693` and the complete runner module again passes in `705`.
It rejects future terminal catch handlers that defer failure to event-loop
drainage. Complete paginated issue
inventory was checked before reporting; #372 owns broader engine qualification.
Registration/exit checks alone do not qualify native or installed behavior.
