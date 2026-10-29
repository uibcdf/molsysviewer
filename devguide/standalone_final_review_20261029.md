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

## Exact-source hosted receiving

Functional commit `1c6c6c025c9656bc835368cc11f7561abb242549` passes
[Qt run 40941374529](https://github.com/uibcdf/molsysviewer/actions/runs/40941374529):
13 distinct cases, zero failures/errors/skips. The original artifact ZIP
12926868571 matches GitHub's SHA-256
`072d0c6ba0f59ddc41ca564ca34921eb014b8857310cd0e8140a5f5dd1b5de54`.
Its native report confirms the initial binary projection, ten binary
replacements, changing molecular pixels and the all-mode/nonconsecutive-axis
second host. Duplicate report copies in the ZIP count as one observation.

This source-host environment uses public MolSysMT 0.23.0
`pyabi3h03bb3b7_0` from uibcdf, Python 3.13 and canonical PySide6/Qt WebEngine
6.11.2. It is separate from local frozen-source checks and does not qualify a
new canonical Viewer Conda package. Lint, documentation notebooks, suite policy
and Conda governance also pass.

[Browser run 40941374623](https://github.com/uibcdf/molsysviewer/actions/runs/40941374623)
passes all 44/44 core suites on that same functional commit. Remote preview
suites are outside this lane. Source-pair 40941374524 finishes with failure on
all three hosts. Linux has 3,290 passes and 24 skips; Windows/macOS each have
3,263 passes and 51 skips. Every host has exactly the same three documentation
failures. Actual completed-job logs confirm the existing MolSysMT
0.23.0/46ef28eb Pandas4Warning in
`Bonds_DataFrame.sort_values(inplace=...)`, tracked by uibcdf/molsysmt#431.
The affected pages are selections, measurements and saved state. The baseline
failure is retained without changing warning filters or claiming a green matrix.
General CI 40941374526 also finishes with failure: both Python 3.11 cells pass;
the six Python 3.12–3.14 cells each fail only these same three examples. All
six completed-job logs have been checked, including Linux and macOS. The
complete per-cell state is retained in the machine receipt. This existing
provider-baseline incompatibility must be reconciled before claiming overall
release qualification; it is not hidden by the passing Qt/browser gates.

The closing evidence update changes guidance and receipts only. Application
source hashes remain those received on `1c6c6c02`; no second broad campaign
or package rebuild is inferred from the evidence commit.

## Remaining scope

No further source defect was identified in this bounded final pass. Qt remains
experimental for 1.0. Maintainer visual receiving under uibcdf/molsysviewer#35,
platform/installed-host/resource qualification under #109/#113, popouts under
#51 and owner-specific addon rendering remain independent. The general/source
CI baseline's known MolSysMT Pandas4Warning documentation failures are not
silenced or relabeled by these standalone checks. No release, tag or package
is produced in this round.
