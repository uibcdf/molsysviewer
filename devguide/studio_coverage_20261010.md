# Completing Studio coverage — 2026-10-10

**Implemented and locally guarded; hosted source CI remains to be reviewed.** The principal maintainer
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
