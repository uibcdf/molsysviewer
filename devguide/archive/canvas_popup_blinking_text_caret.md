---
summary: Intermittent text caret appears near canvas-popup controls
issue: uibcdf/molsysviewer#251
status: resolved
opened: 2026-10-21
closed: 2026-10-21
severity: low
verification: reproduced
area: [popup, ui, interaction]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
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

## Further isolated receiving — 2026-10-21

A persistent temporary Chrome profile now sets the actual browser preference
`settings.a11y.caretbrowsing.enabled=true`, as defined by Chromium's
[preference owner](https://chromium.googlesource.com/chromium/src/+/main/chrome/common/pref_names.h).
The positive control (clicking ordinary paragraph text) produces selection type
Caret. The real molecular popup → fullscreen → Studio popup sequence still
produces selection None, noneditable BODY/BUTTON focus and no observed symptom.
The preference is verified in the disposable profile after browser shutdown;
no user profile or browser accessibility setting was changed.

The first attempt stopped before fullscreen because the fixture had Classic
controls rather than the Minimal Fullscreen button; after selecting the intended
mode the complete probe exits 0. This is stronger bounded negative evidence than
the earlier flag-only request, but does not establish the reporter's browser
setting or explain the intermittent caret. No speculative global `caret-color`,
selection clearing or focus stealing is introduced. A screenshot and disappearance
behavior on Esc/canvas click were requested while other authorized work proceeds.
The human symptom remains asserted and #251 remains open.

## Trigger isolated — 2026-10-21

Diego narrows the trigger to a mouse click in the rectangular area surrounding
the auto-hiding canvas-popup buttons. Clicking an exposed corner of the actual
`data-molsysviewer-controls-hotspot` reproduces a collapsed Caret selection
anchored in the empty focusable DIV, in both isolated browser-preference profiles.
The button-click probes above had missed this exact rectangle. No conclusion
about the reporter's accessibility setting follows; even the ordinary paragraph
control returns a collapsed DOM selection in both modes, so DOM selection alone
is not a certification of painted blinking pixels.

The reveal control's pointer handler focused the DIV but allowed the browser's
default text-selection action. It now prevents that default while retaining its
explicit focus, and suppresses text selection on that nontext control only.
After this change the exact click leaves selection None with the DIV still
focused. A later diagnostic action timed out because autohide hid Panel; that
partial probe is not counted as a complete successful popup/fullscreen run.
The registered popup receiving scenario guards the click, absence of a caret
selection in the rectangle, retained focus and subsequent Enter focus transfer.
Full integrated receiving and human retest are recorded separately in the new
[card/caret receipt](../studio_card_validation_20261021.json).

## Resolution

The relevant real-browser receiving passes: exact reveal-rectangle click and
keyboard focus for #251; background-only alpha and retained foreground contrast
for #254; actual initial/host-resized dimensions, retained manual geometry and
normal fullscreen button clicks for #255. The source fix is ready for human
retest; the original intermittent blinking pixels are not independently certified
by a headless screenshot. [The receiving receipt](../studio_card_validation_20261021.json)
separates targeted, integrated, hosted and manual scopes. No release is authorized.
