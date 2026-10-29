# Standalone source review — 2026-10-29

The local Qt host now uses the shared live workbench with a persistent Python
view. This round repairs authority/preferences, independent host profiles and
normal lifetime, native download destinations, current-scene portable export,
fullscreen/Escape, and camera/movie replies. Qt remains experimental; no tag,
package, platform certification or 1.0 publication is introduced.

## Measured behavior

The native Linux guard
`tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu` passes
on the real desktop/GPU with Python 3.14.7, official PySide6/Qt 6.11.2 and an
NVIDIA Quadro M2000. The provider runtime is frozen at bytes matching MolSysMT
71fbe4f4, including the retained Rust backend; the active sibling checkout is
not edited. The child report verifies its actual provider import path.

The guard creates a Python-owned region through the real shared context form,
receives camera and PNG replies, synchronizes Cinema/Standard preferences both
ways, enters fullscreen with a real button click and exits using Escape. It
accepts a Studio HTML download, cancels another download without creating a
file, and exports the edited scene from the native menu as portable HTML.
Ten dialanine/pentalanine replacements alternate 22/62 atoms and change the
central molecular image every time. Three raw orbit frames capture distinct
viewpoints while a Qt timer continues running. Missing replies time out.
A second native window owns a separate profile, closes its view and removes
its implicit shell file; the first remains usable. Late sends fail visibly.

The final focused Python contracts pass 101 cases with one optional-path skip;
332 JS unit cases pass outside the restricted execution sandbox. Ruff check
and format pass (935 files), and `build:runtime` regenerates the runtime without
changing package-version metadata. All 282 reporting/link checks pass.
The two selected Qt render guards also pass with Xvfb/SwiftShader; they
remain software-host observations, separate from native GPU/human evidence.
The machine-readable
[receipt](standalone_review_20261029.json) carries source hashes and scopes.

## Original failures remain evidence

The single full local core campaign ends with 3,288 passes, eight failures,
21 skips and four repeated xdist collection errors. Seven failures originate
from an overlong temporary directory exceeding Chromium's Unix socket limit;
one is the clean-checkout link check seeing new untracked reports. The unique
collection error is a native helper executing its CLI body during doctest
collection. It now imports safely behind `main()`; reports are tracked and a
short temporary root is used. All 13 selected affected checks subsequently
pass. The full suite is not rerun or retrospectively relabeled green.

The compact receptor counts the deduplicated collection error as a ninth
failure; native JUnit remains authoritative. The same counting boundary is
tracked under uibcdf/pytest-receptor#46. Earlier Qt retries, an inconclusive
child timeout and a successful run whose child lost the requested provider
path are retained in the task cache. Only the final native result above uses
the corrected provider propagation and all final behavior assertions.

The initial core browser run passes context-menu and controls-visibility,
then stops at Studio's obsolete assertion that MolSysMT has no addon. The
restored addon is a real discovered provider; the guard now checks the actual
catalogue and passes. The other 41 core suites subsequently pass, receiving all 44 core suites in
three segments (two unaffected, corrected Studio, remaining 41). This does not
rewrite the original stopped run or qualify remote preview suites.

## Remaining scope

- uibcdf/molsysviewer#35 keeps the requested maintainer visual confirmation:
  alternate File → Load Demo entries, observe each new molecule and Ready
  status, and confirm camera/interaction still work. Native automated pixels
  supplement that observation.
- uibcdf/molsysviewer#109/#113 retain native Windows/macOS and installed-host
  qualification. The broader initialization/image-export resource exception
  is narrowed by normal local-host cleanup, not retired.
- uibcdf/molsysviewer#51 retains Qt popout/child-window parity. Popout stays off
  by default; no new `createWindow` implementation is claimed.
- Notebook-widget addon panels require owner-specific Qt qualification.
  Shared authority and discovery alone do not establish that rendering path.

For manual receiving, activate `molsyssuite@uibcdf_3.14`, launch
`python -m molsysviewer.standalone_qt dialanine --demo`, and check the shared
context menu/Studio, demo replacement, fullscreen/Escape and the native export
dialogs. Keep explicit user outputs; only shell-owned temporary files are
removed automatically. The code changes for #36 and #270–#273 are guarded;
closing their source defects does not change the standalone support boundary.

## Hosted receiving on c08d4c73

Qt run 40923884784 preserves a failure: transport and resource probes pass,
but the new live-workbench guard does not find the native HTML destination
after its dialog. The native JUnit locates that wait precisely; the compact
Actions receptor instead selects nearby D-Bus stderr (known diagnostic boundary
uibcdf/gh-run-receptor#62). No graphics/D-Bus workaround or timeout extension
is inferred from that output.

The follow-up strengthens dialog automation: set its directory explicitly,
verify accepted result and exact selected path, and retain bounded dialog/file
context on failure. That complete software-host flow passes locally; hosted
receiving of the stronger guard remains pending. Product behavior assertions
and export bytes are retained.

Core run 40923884520 independently fails three documentation blocks on Linux
and macOS Python 3.14 because the installed provider emits Pandas4Warning
(`Bonds_DataFrame.sort_values(inplace=...)`). This is the known public-provider
boundary under uibcdf/molsysmt#431. It is not suppressed or presented as a Qt
regression. Policy, Ruff, Conda governance and documentation notebooks pass;
source-pair, other core cells and hosted browser results are still being received.

### Dialog diagnosis confirmed on 937a7340

Run 40925545119's native JUnit records an accepted dialog whose selected file
is still `molsysviewer-export.html`, the application's proposal, rather than
the test's `native-view.html`. The export wrote the proposed destination;
`selectFile()` did not replace the focused editor in this hosted execution.
The guard now uses QTest to type into the real filename editor and click its
Save button, retaining exact destination/result/bytes assertions. The local
software-host flow passes again (39.87 seconds). Application export behavior,
graphics configuration and timeouts are unchanged.

The automation forces widget-based QFileDialog instances for interaction;
it does not certify every operating system's proprietary native picker.
The source-pair Linux job 123624108154 independently confirms the same three
Pandas4Warning documentation failures as standard CI; no new provider defect
is inferred. Cleanup removed 91 duplicate task-owned HTML files (373 MiB),
retaining logs/JUnit/JSON, images and final native/software artifacts.

### Native surface receiving on 7a19303a

Run 40926652147 confirms the real filename edit and fullscreen/Escape, then
fails the new image guard: ten systems load with correct atom counts, but the
native molecular image never changes (`changed=0.0`). Stderr explicitly reports
failed native-pixmap/dma_buf acquisition and null compositor textures. The old
completion-only check could not observe this boundary.

Qt 6.11.2's [compositor source](https://github.com/qt/qtwebengine/tree/v6.11.2/src/core/compositor)
provides a CPU image output path separately from native GPU texture import.
The CI configuration now keeps WebGL through ANGLE/SwiftShader and selects
`--disable-gpu-compositing` for frame composition. Both render guards plus the
workflow contract pass locally (3 cases, 52.82 seconds), including real native
molecular pixels and movie frames. The workflow also retains only test-owned
PNG/report/GIF observations beside JUnit, for 14 days.

The generic Qt Quick software override was tested and refuted: keeping forced
ANGLE aborts with unsupported SceneGraph; letting Qt choose its software path
loses WebGL. Neither configuration is shipped. No application default, native
GPU path, assertion threshold or timeout changes. The new picture assertion is
the explicit reason for revisiting the historical completion-only GL recipe;
native-GPU and software-host qualification remain separate. Hosted receiving
of the CPU-composition configuration is pending.

## Hosted Qt closeout and QPA correction

Hosted run [40929332143](https://github.com/uibcdf/molsysviewer/actions/runs/40929332143)
on 407777c4 passes **13 distinct JUnit cases**, zero failures/errors/skips:
one live-window smoke, two render guards and ten transport/resource probes.
Its actual images show dialanine and pentalanine; all ten replacements change
molecular pixels (minimum fraction 0.10344), three raw movie images have distinct
viewpoints, and both host lifetimes complete. The original ZIP was downloaded;
its artifact id/digest and scoped observations are retained in the receipt.
The pytest `current` alias duplicates some artifact files; it is not a second
observation or extra test count. #36 and #270–#273 close with guard/archive links.

**Correction to local software attribution:** launching `xvfb-run` was not enough
to select X11 in this Wayland desktop session. A direct unchanged-launch probe
reports QPA `wayland`. Earlier local software attempts did not record QPA and
must not be counted as X11 qualification. Their actual rendering/behavior
results remain observations, with this narrower scope. The workflow now makes
`QT_QPA_PLATFORM=xcb` explicit; the child records it and the guard verifies it.
A fresh local explicit-xcb run passes all three affected cases (72.54 seconds),
including actual molecular pixels, with platform `xcb` in the report. This is
separate from both the real native-desktop observation and the completed hosted
run above. No user application platform default is changed.

All 285 final classification/reporting/link guards pass. Unrelated notebook
and addon-receiving work remains untouched. Superseded runs started by this
review are cancelled where still active; historical failures and partial
outcomes are retained. The current core/scientific campaigns still have the
known provider warning boundary and are not relabeled green by Qt success.
The explicit-QPA hosted follow-up is the remaining automatic check; #35 keeps
its maintainer visual confirmation, and platform/popout exceptions stay open.
