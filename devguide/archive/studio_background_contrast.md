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

## Human design revision — 2026-10-21

Diego confirms the cursor fix (#251) and larger card (#255), but rejects the
new transparent darkness levels and requests the previous behavior. #254 is
reopened for that bounded reversal. Restore whole-card opacity 0.90/0.70/0.45,
starting at 0.90, over the original fixed gray background. The earlier
background-only "wrong owner" assessment belongs to the rejected experiment
and is not the accepted design rule. The cursor and proportional sizing
corrections remain in place. The existing browser guard now protects the
restored cycle and its retention across Dock/Float.

[Restoration receiving](../studio_opacity_restoration_20261021.json) records
final local results and their scope. Human visual retest of this reversal is
still pending; no release or candidate freeze is authorized.

## Fourth level approved — 2026-10-21

Diego accepts the restored whole-card transparency mechanism and explicitly
approves extending its cycle to 0.97/0.90/0.70/0.45, with 0.97 initially.
The background, compositing mechanism and three existing values are preserved.
The real-browser guard now checks all four clicks, return to the initial level
and opacity retention across Dock/Float. The [receiving ledger](../studio_opacity_restoration_20261021.json)
records the four-level follow-up separately; visual acceptance of this new level
is pending. No release or candidate freeze is authorized.

## Three-level revision approved — 2026-10-21

After discussing the most transparent level, Diego selects 0.99/0.90/0.70,
with 0.99 initially. The 0.97 and 0.45 trial values are retired. The gray,
whole-card transparency mechanism, cursor correction and larger geometry
are retained. The existing browser guard checks the revised three-click cycle
and retained opacity across Dock/Float. The [receiving ledger](../studio_opacity_restoration_20261021.json)
keeps the preceding trials separate from this three-level revision.

## Three-level refinement — 2026-10-21

Diego requests trying 0.98/0.85/0.70, with 0.98 initially, superseding the
0.99/0.90/0.70 trial. The same gray and whole-card opacity mechanism are
retained. The existing browser guard checks this cycle, its wrap to the
default and retention across Dock/Float. The [receiving ledger](../studio_opacity_restoration_20261021.json)
records this refinement separately from the preceding trials.
