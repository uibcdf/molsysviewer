# Completing Studio coverage — 2026-10-10

**Done in `33e73587`: applicable hosted source CI and the new Studio flows pass.** The principal maintainer
accepts the cross-surface improvements before 1.0, retaining only Copy Python
as a future evaluation. Issues #223–#225 and #227 close this work with archived guards; #226 stays post-1.0.

Annotation Focus now uses the existing tagged object owner in live sessions,
including absolute coordinates without atom indices. Broken anchors are disabled;
exported hosts retain atom focus and explain missing coordinate-focus authority.
Interactions uses Visible/Hidden/Hidden by layer, and its count respects layers.

Studio Export now saves/restores JSON state or experimental MSV sessions on
the Python filesystem. Restoration confirms replacement and history clearing;
existing-file replacement requires an explicit overwrite declaration. Public
state/session owners validate and persist the data. No molecular/session bytes
cross the widget transport. File drafts survive frames, projections and tabs;
only the matching action/request/domain reply ends a pending operation.

Folded examples explain multiple/complementary loading, calculation versus
display structures, participant filters, units, anchored/fixed geometry and
state/session contents. Existing public API contracts remain the owners.

## Validation

The focused Python modules pass 27/27. The first JavaScript run found missing
synthetic click event objects in two newly added DOM guards; supplying the same
native event contract as the existing tests corrected the guards. The rebuilt
unit file then passes. Chromium's first launch was blocked by sandbox
`setsockopt: Operation not permitted`; the browser check is rerun with the
required process permissions, with no test skip.
The expanded real Studio/Chromium workflow passes, including live coordinate
focus, layer-hidden wording, failed save/retry, JSON/MSV save and confirmed
restore, request correlation, PNG dimensions/alpha and disabled exported-host
file controls. Session restoration initially left Export hidden by the System
load transition; only its matching requester reply now returns to Export.

TypeScript passes, the bundled JS unit file passes, and the full core Chromium/Mol*
regression passes 43/43. These are development-source checks, not installed
artifact qualification.

The single full Python run reports 3046 passed, 30 failed and 23 skipped.
Twenty-two failures recover with the necessary socket/browser permissions and
tracked, regenerated guide indexes. The affected-state/failed-node check covers
436 cases: 427 pass, eight experimental Qt context failures remain, and one
docstring bookkeeping mismatch is corrected and passes its focused guard.
All state/session/history modules and the expanded file guards are exercised.
This is not a globally green Qt run. Hosted evidence
for the previous 792fd5f6 source does not qualify this changed source or a package.

## Integrated source and hosted inspection

Source `33e735876aa337f1fded86670f0b48d0e1fc0fda` is reviewed and pushed
directly to `main`. #223–#225 and #227 are closed; #226 retains its post-1.0
milestone. The board synchronization check confirms 28 matching reports/issues.

Inspection at 2026-10-10 13:42 UTC finds publication governance, suite policy,
Ruff and notebook-routing checks green. These three source campaigns remain
active or queued, without another dispatch:

| Campaign | Observed state |
| --- | --- |
| [Scientific CI 38055953874](https://github.com/uibcdf/molsysviewer/actions/runs/38055953874) | Four required cells running, two macOS cells queued; separate experimental Qt job failed. |
| [Python 3.14 source pair 38055953998](https://github.com/uibcdf/molsysviewer/actions/runs/38055953998) | Linux has passed Python tests and is running core browser checks; Windows runs Python tests; macOS is queued. |
| [Core browser 38055953588](https://github.com/uibcdf/molsysviewer/actions/runs/38055953588) | Core browser step running. |

GH Run Receptor preserves the pending aggregate and the failed Qt step. The
completed Qt job log identifies `Could not create a WebGL rendering context`
and `Exported scene has no WebGL canvas` under hosted Xvfb/software GPU.
This remains experimental standalone evidence under #109, not a passed Qt
result or an observation of a visible-window GPU host. The applicable source
campaigns have not yet completed, so this inspection does not declare them green.
The machine-readable receipt preserves run identities, job states and log digests.

### Completed source gates and Studio flow review — 14:15 UTC

The final inspection confirms all six scientific Linux/macOS Python 3.11–3.13
cells successful. Each Linux cell reports 3072 passed/35 skipped; each macOS
cell reports 3045 passed/62 skipped. The three Python 3.14 source-pair cells
also pass: Linux 3072/35, macOS 3045/62 and Windows 3046/61. That campaign uses
MolSysMT 0.23.0 source `46ef28eb`, including native/integration checks; these
counts do not represent a new Conda package qualification.

Both the standalone hosted core campaign and Linux source-pair core pass 43/43.
The Linux source-pair campaign executes all 25 documented notebooks with zero
failures. The scientific Linux/Python 3.13 log confirms 327/327 JS unit tests.
Policy, governance, lint and notebook-routing checks retain their successful
conclusions. None of these campaigns was rerun or duplicated.

The scientific workflow's official conclusion is **failure**: its separate
experimental Qt job still fails to create WebGL; required scientific cells
are all green. GH Run Receptor preserves this conclusion and the six successful
jobs. Its cause excerpt selects secondary DBus stderr; the native Qt log above
is the basis for the WebGL diagnosis. No visible-window Qt qualification is claimed.

The requested fresh Studio flow check passes with real Chromium/Mol* and Python
action owners in `molsyssuite@uibcdf_3.14`: absolute-coordinate Focus, layer-aware
visibility/counts, invalid-path feedback and retry, preserved drafts, unrelated
reply refusal, restore cancellation/confirmation, JSON state and experimental
MSV save/restore, retained PNG recipe, real PNG/HTML downloads and disabled
Python-only file operations in exported hosts. No new defect was observed.
The editable provider has advanced to `d1ad4e37`; the receipt records this separately
from the original `edc78df0` local evidence and the exact hosted 0.23.0 baseline.

This completes the automated source review. Human first contact with a final
installed artifact and its exact package gates remain separate; 0.25.0 is still
unfrozen and publication is paused.

## Temporary workspace

The disk reached 100% during implementation. The superseded, idle temporary
`/tmp/msv-0241-receiver-20261008` environment was removed, recovering about
3 GB; its `conda-meta` was preserved beside it. Original release receipts,
package bytes and unrelated work remain intact.

0.25.0 remains unfrozen; no build/upload/tag/public release is authorized by
this source round. Both 1.0 publications remain paused.

## Figure persistence found by the browser guard (#227)

The actual file roundtrip reached the PNG controls as 2× instead of the saved
1.5×. State omitted the workbench recipe, and Whole representation projection
reset the frontend configuration. #227 records both causes. State-v2 now
optionally carries the existing preset/scale/background subset, prevalidates it
and restores through `set_figure_spec`. Whole projection preserves configured
values. The final figure/image-export check passes 40/40, including both JSON/MSV,
invalid metadata without mutation and legacy/reset behavior. This does not
promise workbench storage of export-only dimensions or camera overrides.
Finite positive scale validation belongs to FigureSpec itself, rejecting boolean,
NaN and infinite scales before a recipe can enter a saved document.

## Manual review after integration

Restart the notebook kernel and refresh the browser before creating a new view.
Focus an annotation placed at absolute coordinates. In Export → Save and restore
work, save `review.json`, change an object, restore with confirmation and inspect
the recovered object/frame and PNG scale/background. Save `review.msv`, replace
the molecular system, then restore the session and inspect all structures and
named interaction sets. Confirm that paths refer to the Python host, and that
existing-file refusal/retry preserves the draft. Folded examples should remain
quiet until opened. Human first contact with a final installed artifact remains
separate from these development-source guards.
