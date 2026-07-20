# Context menu opens (and stays open) while right-dragging the structure

**Status:** Reported during dogfooding, not fixed
**Severity:** moderate — breaks a basic navigation gesture

## Symptom

Right-dragging on the canvas to pan/move the molecular system also opens the
canvas context menu, which then stays open for the whole drag.

## Cause

`handleCanvasContextMenu` (`src/managers/viewer-controller.ts`, ~line 1190) is
bound to the browser's `contextmenu` event, which fires on a right-button press
regardless of whether the user is starting a drag. Mol* uses the right button for
panning, so the two gestures collide: the menu opens even though the intent was
to navigate.

## Fix direction

Distinguish a click from a drag before opening the menu:

- on `mousedown` with `button === 2`, record the pointer position;
- on `mousemove`, if the pointer travels past a small threshold (a few pixels),
  mark the gesture as a drag;
- in the `contextmenu` handler, when the gesture was a drag, `preventDefault()`
  but do **not** open the menu (and close it if already open).

The threshold keeps a plain right-click working as before.

## Test

A JS unit test over the gesture decision (press → move beyond threshold →
contextmenu ⇒ menu suppressed; press → contextmenu without movement ⇒ menu
shown), so the behavior is pinned without needing a browser.
