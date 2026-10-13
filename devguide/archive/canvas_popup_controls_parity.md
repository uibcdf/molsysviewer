---
summary: Canvas popup must preserve the notebook canvas controls and experience.
issue: uibcdf/molsysviewer#232
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [popup, controls, notebook]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Canvas popup controls parity

**Reported:** 2026-10-13 by the principal maintainer during notebook review:
the canvas popup shows old controls while the original canvas shows modern ones.

## What

Open the canvas popup from a notebook viewer. Both canvases should use the same
controls, mode, positions, reveal behavior, Help, context menu and Studio tools.
The popup control closes its window instead of opening another popup.

## How

`js/src/index.ts` selected a legacy `popup_js_source` before the runtime that
rendered the notebook. A stale legacy source can therefore render a different
frontend in the popup. The AnyWidget bootstrap now binds each render to the
exact source it imported; that source takes precedence over cached fallbacks.

`popup/popup-logic.ts` seeded only the panel style in its local UI model.
Controller options were ignored by model-backed mode getters until asynchronous
initial sync. The host now projects its canvas UI state before creation, so
the first controls build uses the correct mode and preferences. Bespoke popup
control CSS is removed; the shared renderer owns the styles in both windows.

The maintainer's live kernel/runtime provenance has not been captured. These
are source-confirmed divergence mechanisms, not a claim that every observation
has the same cause.

The actual browser exercise also exposed a missing focusable canvas and `V`
shortcut, one-way popup preferences, an absent Studio panel-popout button,
a relative trajectory step echoed back to its origin (advancing twice), and
an exported popup starting from a stale frame. These are corrected in the
shared owners. A cleanup assertion caught late camera notifications after
widget disposal; timers/subscriptions now release before the wire closes.

## Why

An external canvas belongs to the same molecular session. Switching windows
must not switch the available controls or their visual language.

## What was refuted

Duplicating the modern buttons in the popup is unnecessary: both surfaces
already call `ui/controls.ts`. The defect lies in source/configuration
selection and redundant styles, not a missing button constructor.

## Resolution

The bounded `controls-visibility.e2e.ts` guard passes against both the actual
Python exporter and the actual widget bootstrap with a persistent real Python
authority. It asserts first-mount Classic mode, stale legacy-source isolation,
control styles, Help, focus/keyboard, fullscreen, Studio/panel popout, preference
and context-menu changes, one trajectory advance and clean transport teardown.
JS units pass; 3 widget and 67 runtime/router Python checks pass. The single full
Python run preserves 3,095 passes, 21 skips and one Git-index bookkeeping
failure; the repaired clean-checkout link guard passes 4/4. Full core browser integration passes 43/43; the final shared-keyboard
follow-up independently passes the complete controls guard, including a shadow
notebook host and input typing. The transport drains before Python closes.
New exact hosted source CI remains a separate receiving gate; no installed
artifact or publication claim follows. The normative contract is
`devguide/canvas_popup_contract.md`.
