---
summary: Polish Studio Load for short canvases and explicit host-file selection
issue: uibcdf/molsysviewer#286
status: resolved
opened: 2026-10-30
closed: 2026-10-30
verification: reproduced
area: [studio, loading, ui]
guard: molsysviewer/js/tests/e2e/composite-load.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Studio Load usability and file selection

The maintainer accepts the five improvements and contextual action labels from
our final review of #265. Current 480 px notebook-height rendering places Load
below the initial viewport; minimum desktop geometry hides even the source
field. Large shared-canvas rendering is ordered, but does not establish native
Qt visual qualification. Source inspected: 531f3814.

## Accepted implementation

Use a fixed primary-action/result footer and one scrollable input area. Keep
source/PDB entry simple; disclose labels, atom/frame selectors and tips. Make
Append unavailable without a system; show pairing only for independent
multi-structure inputs, retaining explicit scientific choice. Dynamic action
labels state Load/Add/Replace/Append. Preserve Python view.load and defaults.

Browse explicitly targets the running Python filesystem. Jupyter uses bounded,
paged directory requests and explicit file selection, without uploading browser
files or duplicating trajectory bytes. Qt supplies its own native multi-file
picker to the same private file-acquisition action. Choosing files populates the
draft and never loads automatically. Cancel/error leaves molecular data intact.
Directories, hidden files, parent navigation, multiple choices and manual paths
remain available; static exports have no filesystem authority. Filesystem replies
are correlated per requesting form and excluded from replay history.

Verify real browser notebook/narrow/large layouts, all inherited molecular load
scenarios, picker paging/hidden paths/cancel/retry and popup parity. Keep source,
installed-artifact and native/human evidence separate. #277 demos/recents remains
post-1.0 and independent. No scientific API or release expansion.

## Resolution — 2026-10-30

Implemented the accepted UI and acquisition contract. Source input and Browse
share a row; a fixed footer retains the contextual primary action and result
while the editor scrolls. Options disclose labels and atom/frame filters without
changing scientific defaults. Enter submits, incompatible Append is disabled
with an explanation and pairing is contextual. The Python API is unchanged.

The real composite browser guard checks 1000×480, 560×360 and large layouts with
actual hit targets for the input, Browse and primary button. It drives the Python
file-action route through directory navigation, hidden files, paging, multiple
selection, Escape, cancellation, late replies and failure. Choosing paths does
not load any molecular data. Existing batch/progressive/replacement/complementary,
append, nonconsecutive pairing, coordinates and source-region assertions pass.
Four distinct affected browser suites pass; the final compact row and Append
availability are additionally verified by the composite guard. JS passes 334/334;
63 directed Python load/dispatch/transport/file cases pass. The native Qt guard
also performs actual selection/cancel/typing/click and scientific replacement.

Directory browsing retains 80 names plus one lookahead, scans metadata without
reading molecular bytes and has no browser-upload transport. Selection metadata
can grow with explicit user selections; no universal RAM or performance bound
is claimed. Replies are request-correlated and excluded from replay. Static
exports omit Load. Qt releases its native picker callback at host close.

Wide, notebook-height, minimum-size and native Qt captures were inspected. The
owner record is studio_load_polish_receiving_20261030.json; this is source
receiving, not installed package or platform admission. The base 531f3814 browser
and Qt hosted runs pass; general/source runs retain exactly the three known
Pandas4Warning documentation failures under uibcdf/molsysmt#431. New hosted CI
will be inspected on the published source. No tag, package or 1.0 publication.
