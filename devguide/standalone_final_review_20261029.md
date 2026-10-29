# Final standalone source review — 2026-10-29

The final pass found and repaired two additional live-host discrepancies:
uibcdf/molsysviewer#274 ignored `load_mode="all"` and discarded unselected
atoms; uibcdf/molsysviewer#275 never entered the declared array-native path
in the actual host. The factory and Qt now share their loading policy, and
the negotiated Qt adapter consumes the canonical lazy projection before
numeric JSON exists. Raw messages retain their own data.

The earlier [review](standalone_review_20261029.md) remains evidence of its
own checks. Its transport observations alone did not establish binary live
loading. The corrected [data-plane contract](data_plane_architecture.md)
and [source receipts](standalone_final_review_20261029.json) distinguish the
new guards from those earlier results.

## Current verification

The one complete non-Qt regression passes 3,298 cases with 21 explicit skips,
zero failures/errors. Forty-three focused Python contracts, 289 guide/closure
checks and 332 JS unit tests pass. Runtime rebuilding uses `build:runtime`,
with no package-version changes. The live Qt
workbench guard passes both on the actual Linux/Wayland desktop and on explicit
X11 with SwiftShader WebGL and CPU frame composition. Native GPU receiving
uses canonical PySide6/Qt 6.11.2, Python 3.14.7 and the Quadro M2000.

Both configurations receive the initial system and ten alternating replacements
without materializing numeric JSON, serve real binary payloads and show
different molecular pixels. A second independent host retains all 62 atoms
with a visual selection of two and structures [8, 0, 3]. Existing checks of
shared Studio/context actions, portable export, native save/cancel dialogs,
fullscreen/Escape, camera/image/movie replies and cleanup continue to pass.

All 3,004 frozen provider source hashes remain unchanged and match the retained
MolSysMT 71fbe4f4 snapshot. These are source/runtime
checks, not qualification of a newly published Viewer package. The receipt
records the broad regression and hosted receiving separately when available.

## Remaining scope

No further source defect was identified in this bounded final pass. Qt remains
experimental for 1.0. Maintainer visual receiving under uibcdf/molsysviewer#35,
platform/installed-host/resource qualification under #109/#113, popouts under
#51 and owner-specific addon rendering remain independent. The general/source
CI baseline's known MolSysMT Pandas4Warning documentation failures are not
silenced or relabeled by these standalone checks. No release, tag or package
is produced in this round.
