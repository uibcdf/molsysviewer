---
summary: Native Qt file-dialog guard types while its modal window is inactive.
issue: uibcdf/molsysviewer#287
status: partial
opened: 2026-11-08
closed:
severity: medium
verification: reproduced
area: [qt, tests, loading]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Native file-dialog path entry receiving

Reopened #287 preserves its prior qualified source and hosted/native evidence
in the archive. While receiving #342, the broader workbench guard completes
file-picker cancellation but never clicks Open: its zero-delay absolute-path
input leaves the basename in the editor and selects all path ancestors plus
the requested existing file. Original diagnostics and JUnit are retained.
This does not establish a product molecular-loading failure.

A plain real QFileDialog reproduces this without Viewer. Original input and
an explicit-focus-only control both fail to establish the one requested file.
Five-ms key pacing establishes that selection and a real accepted Open click,
but takes 11.62 s locally and is not adopted over the existing ten-second bound.
A separate activation control establishes actual filename focus and accepts the
real file in 120 ms. Focus without window activation does not fix the control.
The fixture now activates its own modal, verifies editor focus and retains the
original genuine typing, single real Open click, selection equality and deadline.
It does not fabricate selectedFiles, call accept/selectFile or retry acceptance.
The exact Qt-internal path-selection mechanism is not claimed from these controls.

The full actual Wayland Qt workbench then passes in 30.26 s, including typed
file Open/Cancel, ten binary replacements and independent-window lifetime.
Original failures remain preserved. Exact-source hosted qualification is pending
the consolidated CI checkpoint; local receiving does not close this reopened
issue or replace the postponed human observation.

The first full workbench attempt is interrupted by the resource monitor after
55.3 MiB of global swap activity in five seconds; its child exit 0 is not a
passing result and no terminal report exists. The lower-resource four-CPU/
four-GiB attempt reproduces the selection failure without a resource stop.
Owned processes close in both attempts. Keep source/capture receiving and this
independent UI-input problem separate. Human and hosted qualification remain
distinct; no publication is authorized.
