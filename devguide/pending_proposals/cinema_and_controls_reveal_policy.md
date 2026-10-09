---
summary: Apply Cinema preset and expose consistent control-area autohide
issue: uibcdf/molsysviewer#180
status: partial
opened: 2026-10-08
closed:
verification: reproduced
area: [canvas, configuration, interaction, export]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/interaction_gestures_and_menus.md
blocked_by: []
supersedes: []
---

# Cinema and canvas control reveal policy

**Reported:** 2026-10-08, during the maintainer's visual acceptance of the
parallel context menus under `uibcdf/molsysviewer#179`. View → Cinema changes
the mode name but leaves the viewport controls unchanged. Undocking Studio
changes reveal from the button area to the whole canvas.

## What

Apply the Cinema controls preset at runtime, and make the reveal area explicit:
`view.set_controls_visible(True, autohide=True, autohide_scope="controls")`
reveals near the buttons by default; `"canvas"` reveals anywhere in the canvas;
`autohide=False` retains enabled controls. `visible=False` remains authoritative.
Settings offers the same choice. Keyboard access and touch must remain possible.

## How

The context owner called `setViewerMode` without applying `controls_mode`.
The controls owner selected its hotspot from fullscreen/Dock instead of a
user preference. Its trajectory observer reset opacity on every state update.
Control rebuilds removed the root bar but retained the Cinema scrubber, Help
handlers and observers. Popup controls duplicated the widget's implementation;
exported pages supplied an immutable model stub, so runtime mode changes could
not rebuild their controls.

Share the controls renderer, observable local UI traits and reveal policy across
widget, exports and popups. Release the previous controls lifetime before each
mode rebuild, including layout/trajectory subscriptions, timers and hotspots.
Carry the validated scope through config, widget, copy and HTML configuration.

The real self-contained export exposed another delivery defect: Chrome reports
`file://` locally while the popup's recipient origin is opaque (`null`). Passing
`file://` to postMessage prevented even its ready event from reaching the host.
The popup-channel owner now provides the shared target-origin rule: opaque/file
origins use `*`, network origins remain exact. Window, channel/token and endpoint
checks still authenticate every accepted message. The host awaits popup boot
so bootstrap failures are observed; readiness follows mounted shared controls.

## Why

Switching to Cinema must visibly remove viewport buttons while retaining
discoverable trajectory controls. Button-area reveal must behave consistently
after Dock/fullscreen changes and must not be overridden by trajectory updates.
Hidden buttons must not intercept canvas picks. Keyboard focus must reveal the
controls without letting pointer focus keep them visible after the mouse leaves.

## What was refuted

Changing the mode's label alone does not apply its controls preset. A second
popup-only reveal implementation would preserve the existing divergence.
The boolean autohide flag alone cannot express both areas. Merely removing a
rebuilt root element does not dispose listeners or the Cinema scrubber.

## Verification

Seven native-demo Python configuration checks pass. The public inventory,
runner inventory and clean-checkout links pass 25 focused checks after adding
the new digester/suite and staging the report. The focused frontend owners pass
69 cases: ContextMenu 17, GroupPanel 35, popup host 11, popup boot 4 and addon
lifecycle 2. Existing protocol mocks isolate relay/model projection; the new
real Python export/Mol*/Chromium guard owns actual control rendering and popup
bootstrap. TypeScript, runtime/harness rebuild and Ruff pass.

The one full Python run records 2,948 cases: 2,914 pass, 23 skip, eight known
experimental Qt-host failures (OpenGL/Vulkan/D-Bus) and three inventory/index
failures corrected by the focused checks above. The one full JS run records
316/323 passing: four legacy duplicate-toolbar mocks and three failures from
their asynchronous teardown contamination. Shared-provider protocol seams are
updated; each affected owner passes its focused run. Neither full regression
was repeated or relabeled green. These are development checks, not installed
artifact qualification. Browser campaign completion is recorded below.

The shared browser campaign passes its first seven suites: ContextMenu,
controls-visibility, popup-channel, panel-popup-welcome, structure-data-relay,
widget-seam and exported-page-colour. The new controls guard exercises three
Cinema/Classic/Integrated cycles, constant subscriptions, keyboard access,
Settings, Dock/fullscreen, hidden-frame updates and a production disk-export
popup. The export-framing guard still assumed buttons remained visible after
frame changes; its interaction now approaches the reveal area before clicking.
That owner and the previously unreached Movie suite pass their separate 2/2 run;
this is targeted recovery, not an uninterrupted green nine-suite campaign.

The focused reporting/profile validator passes 184 cases and generated indexes
are current. Native JUnit and receptor counts agree for the full Python run.

## Discovery refinement — 2026-10-09

The maintainer confirms Cinema and the new reveal policy work, and requests a
two-second initial appearance so the user can discover the controls. The shared
visibility owner introduces its surface once, when it first becomes available;
mode rebuilding gives the new surface its own introduction. Hover, frames,
policy changes and Dock/fullscreen do not restart it. Explicit hide and overlay
suppression remain authoritative. Disposal cancels the timer. Cinema's available
trajectory scrubber follows the same rule; its helper toast is separate.

The real browser guard now observes initial visibility transitions and verifies
the duration, Cinema introduction, returning to Integrated and explicit hide
during introduction, while retaining popup and subscription checks. Validation
of this refinement passes in real Chromium, including the earlier popup,
keyboard, Settings and subscription checks. Human confirmation remains pending.
The complete JS regression now passes 324/324 cases; the 2026-10-08 failed
campaign above retains its original scope. TypeScript/runtime regeneration,
188 reporting/link checks and generated-index checks pass. Python implementation
and public configuration are unchanged; the earlier native-demo checks retain
their scope. The previous checkpoint's hosted E2E run `37847308489` is successful
at `2b0d1ef7`, separately from this local introduction guard.
Prior menu and functional acceptance are preserved. Publication and both 1.0
versions remain paused.

## Restore whole-surface fading — 2026-10-09

The maintainer observes abrupt, fragmented disappearance after the discovery
refinement and requests comparison with the former Cinema implementation.
`controls.ts` at `21ac9209` animated the entire scrubber's opacity for 200 ms
and moved it downward 45 px over 250 ms. The shared owner's immediate
`visibility: hidden` prevented painting the intended opacity transition. The
previous browser guard observed inline targets/duration but did not sample the
rendered fade, so it could not catch this visual regression.

The shared owner now delays computed visibility until the group fade ends and
makes the subtree inert immediately. This preserves input safety despite
descendants' explicit pointer-events. Cinema receives its original shown/hidden
transforms through the shared owner; reveal reverses the transition without
another timeout. Normal toolbar positioning remains owned by the renderer.
The browser guard samples actual animation frames for intermediate opacity,
uniform descendant visibility, inert hit testing and downward Cinema motion.
Those checks pass. Its first run additionally found that Enter could try to
focus a descendant before the visibility reversal reached computed styles.
The reveal action now establishes keyboard intent explicitly and transfers
focus on the next animation frame, cancelled on disposal or loss of hotspot
focus. The corrected real-browser run passes those checks and the retained
discovery, modes, Settings, Dock/fullscreen, popup and subscription workflows.
The complete JS regression passes 324/324 cases, TypeScript/runtime rebuild
passes, and 188 reporting/link guards and generated-index checks pass. Python
and the public controls configuration are unchanged.
Human visual confirmation remains pending.
