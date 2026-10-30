---
summary: Make shared Help keyboard-reliable in Qt and adapt its card to canvas size
issue: uibcdf/molsysviewer#284
status: resolved
opened: 2026-10-30
closed: 2026-10-30
severity: medium
verification: reproduced
area: [ui, standalone, keyboard]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative: devguide/standalone_window_chrome.md
blocked_by: []
supersedes: []
---

The maintainer reports that H/h does not open Help in the real Qt window,
although the Help button works. The card remains capped at 640 by 480 CSS
pixels in large windows. Status details/copy and molecular interaction after
window manipulation pass the human receiving; geometry restoration awaits a
clarified close/relaunch test.

The current key handler listens only inside the canvas container, so a native
WebEngine document focus outside that subtree is a candidate cause, pending a
real-key reproduction. Preserve text inputs, modified shortcuts, per-view
ownership, shadow-root notebook hosts and cleanup when correcting it. The
closed #281 exposed native shortcuts but used a Help-button click in its guard.

Use host-relative, bounded Help dimensions and responsive columns without
changing Studio's accepted layout. Verify small canvases, large windows,
resize and fullscreen with actual browser layout and native Qt key events.
Qt remains experimental; no publication or platform-support claim follows.

## Resolution — 2026-10-30

Real Qt key events reproduce the original failure with document-body focus.
Live desktop capabilities now enable a body-only H/h fallback; notebook keys
remain local to their canvas. Help focuses its close button and restores the
previous element, allowing Escape to close Help before leaving fullscreen.
Modified shortcuts, typing, composition and repeated events are preserved.
Window buttons retain Tab access without taking mouse focus from the canvas.

The card reuses `getFloatingPanelSize`, grows text from 13 to 16 CSS pixels,
and selects one/two/three columns according to actual host width and native
capabilities. It observes host resize and scrolls vertically in short canvases.
The rendered native capture was inspected: 1200-pixel width with three columns
and readable 16-pixel base text; Studio's own accepted dimensions are unchanged.

The native guard now sends actual H/h and modified keys, opens Help again
after native maximize/restore, checks its fullscreen bounds and verifies that
Escape closes Help while preserving fullscreen. Four affected Qt/transport/
optional-absence checks pass; an additional presented-capture run passes.
All 332 JS cases pass. The existing `controls-visibility.e2e.ts` receives the
real small/large layout and input assertions through `help-layout-scenarios.ts`;
its complete exported-page, live notebook/popup and scientific-mirror scenarios
pass without skips. Logs, JUnit, the native report and presented screenshot are
retained under `.pytest_cache/qt-help-284/`. Failed reproductions remain separate.
All 40 non-runtime standalone contracts and Ruff check/format (940 files) pass.
Reporting assertions pass; the clean-checkout link guard passes 4/4 after the
new archived file is staged, correcting its initial untracked-file failure.

The original human checks pass status copying in normal/fullscreen and molecular
interaction after window manipulation. The corrected Help and close/relaunch
geometry still await maintainer confirmation. No complete green CI, additional
platform or installed-artifact qualification is inferred.

## Maintainer receiving — 2026-10-30

After receiving 1488a8a7, the maintainer confirms that H/h works and window size
is recovered after closing and reopening the application. This adds those two
human observations to the earlier status-copy and molecular-input results;
it does not infer a separate visual acceptance of the adaptive Help card or
the ten-replacement observation required by #35. Hosted Qt 41114314894 passes;
the other applicable campaigns retain their own states.

## Visual acceptance — 2026-10-30

The maintainer subsequently accepts the new Help size and confirms that the
card is more legible than before. This completes the visual receiving for
this Help refinement; #35 and platform/artifact qualification remain separate.
