---
summary: Improve Studio background contrast without fading text
issue: uibcdf/molsysviewer#254
status: resolved
opened: 2026-10-21
closed: 2026-10-21
verification: measured
area: [studio, ui]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Studio background contrast

**Reported:** 2026-10-21, TcTIM dogfooding.

## What

Keep three background levels with a darker default, without dimming text. The
current panel opacity multiplies background, text, controls and addon content.
The user asked whether three revised levels or four would be preferable.

## How

Let the shell own three background alpha values, defaulting to the darkest.
Apply alpha to the card background only; retain opaque foreground content.
The same choice survives lock, minimize, Dock and ordinary form updates.
Panel-only Studio remains opaque because no molecular scene is behind it.

## Why

Readability against molecular geometry improves without another step in the
cycle. Open and closed background/opacity/layout issues were checked; #183,
#188 and #237 address different behavior and their guarantees remain applicable.

## What was refuted

Adding a fourth level does not address foreground attenuation. Whole-card
opacity is the wrong owner for background-only transparency.

## Resolution

The relevant real-browser receiving passes: exact reveal-rectangle click and
keyboard focus for #251; background-only alpha and retained foreground contrast
for #254; actual initial/host-resized dimensions, retained manual geometry and
normal fullscreen button clicks for #255. The source fix is ready for human
retest; the original intermittent blinking pixels are not independently certified
by a headless screenshot. [The receiving receipt](../studio_card_validation_20261021.json)
separates targeted, integrated, hosted and manual scopes. No release is authorized.
