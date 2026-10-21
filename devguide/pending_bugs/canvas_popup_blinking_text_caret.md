---
summary: Intermittent text caret appears near canvas-popup controls
issue: uibcdf/molsysviewer#251
status: open
opened: 2026-10-21
closed:
severity: low
verification: asserted
area: [popup, ui, interaction]
guard:
normative:
blocked_by: []
supersedes: []
---

# Intermittent text caret appears near canvas-popup controls

**Reported:** 2026-10-21, TcTIM pre-1.0 dogfooding.

## What and how

Diego reports a blinking vertical text caret near upper-right canvas-popup controls, seen once after fullscreen and Studio popout. He confirms it was a text caret. Exact trigger, screenshot, focused element and browser caret-browsing setting are unknown.

Open/closed #193, #209, #232 and #250 were checked: form focus, keyboard focus and popup layout do not record this symptom. The canvas container has tabIndex=0 but no contenteditable. Chromium native caret browsing can place a cursor in non-editable page text; browser mode or retained DOM selection are hypotheses, not a proven application cause. Do not disable accessibility navigation or hide every input caret speculatively.

## Receiving / next action

Investigate the real popup/fullscreen/Studio sequence and inspect focus and selection, preserving ordinary text entry and keyboard shortcuts. The user may provide a screenshot if it recurs. Remains open; the simultaneous default-lock/fullscreen requests are separate #252/#253.

## Bounded investigation — 2026-10-21

Real Python pentalanine/widget/Mol*/Chrome 155.0.8059.84 receiving followed
canvas popout → canvas fullscreen → Studio popout. Both the normal launch and
a launch requesting Chromium's `--enable-caret-browsing` option returned
selection type None at all three checkpoints; active elements were BODY or
BUTTON, never editable, and the visible input was unfocused. Both probes
returned exit 0 and retained screenshots/focus/selection JSON. The flag request
is not evidence that the reporter uses caret browsing, nor proof that the flag
activates that setting in this Chrome version. Blink pixels were not reproduced.

[The receiving receipt](../studio_chrome_validation_20261021.json) retains the
probe scope and digests. Keep this report open at asserted verification for the
human symptom. No speculative cursor/focus CSS or accessibility override was
introduced. Next evidence: screenshot and trigger details if it recurs.
