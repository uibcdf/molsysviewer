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
