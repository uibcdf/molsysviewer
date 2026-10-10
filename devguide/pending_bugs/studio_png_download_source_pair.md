---
summary: Studio PNG download guard times out in the Python 3.14 exact source-pair lane
issue: uibcdf/molsysviewer#198
status: partial
opened: 2026-10-09
closed:
severity: medium
verification: measured
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio PNG download guard times out in the Python 3.14 exact source-pair lane

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Run 38000819781 on c92c2760 times out waiting for the Studio PNG download. Independent core 38000819783 passes 42/42. The cause is not established.

## How

Diagnose the actual PNG request/render/download path with bounded evidence, preserve original failure, and fix the mechanism rather than increasing the timeout or skipping the assertion.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution

Dimension updates now change the PNG readout in place instead of replacing the
button between pointer-down and pointer-up. The real browser guard deliberately
holds the button during two dimension notifications, then downloads and checks
actual PNG dimensions/alpha. It passes locally in scoped and core runs. Rendering
failures and download initiation now produce bounded inline status/console evidence.

This establishes and guards a deterministic click-preservation defect. It does
not establish the cause of historical run 38000819781. Its raw failure is retained;
no timeout is increased and no assertion skipped. Review the next exact-source
hosted source-pair gate before closing this report or claiming hosted repair.

## Follow-up — 2026-10-10

Exact source a699f5b5 fails again in core browser run 38034284562, at
`studio-usability`: 30 seconds waiting for the PNG download. Source pair
38034284506 also fails on Linux; Windows and macOS pass. The eight guards
and individual Studio PNG/HTML browser check for the #206–#208 round pass
locally; that does not diagnose the hosted input/render/download failure.
The browser guard now retains pointer-down/up/click, current inline status,
disabled state and drawing-buffer dimensions if its download wait fails.
The wait and image byte/alpha assertions remain unchanged. Inspect the next
source's bounded evidence before claiming a hosted repair or closing #198.

## Render-stage evidence — 2026-10-10

Core run 38037909757 on 0e7b6593 fails with all three input events present:
pointer-down, pointer-up and click, each on a connected element. The status is
`Rendering PNG…`, the button is disabled, and the drawing buffer is 1050×760.
The historical input-replacement correction is therefore insufficient to explain
this current render-stage wait. Download initiation has not been reached.

Mol* 5.4.1's screenshot helper awaits task progress, background update, image-pass
rendering and image encoding. Local source review uses the installed dependency
and the available upstream checkout, without changing Mol*. The browser guard now
retains the last eight Generate Image task updates, background variant,
illumination flag, context-lost flag and encoding-canvas dimensions. These are
read-only observations; no timeout, GPU quality or success assertion changes.
Root cause and next exact-source hosted render evidence remain pending.

## Encoding-yield observation — 2026-10-10

Core 38038849065 on 00716efb reaches task messages Rendering image… then
Encoding image… before its unchanged download wait fails. Context loss is false,
background is off, illumination is disabled, image-pass size is 1575×1140 and
the encoding canvas is still at its initial 300×150. Mol* has returned image data
and called `ctx.update('Encoding image...')`, but has not resized/filled the
encoding canvas. The helper awaits that task update before writing pixels.
This is stronger phase evidence than the previous Rendering PNG… button status;
it does not yet distinguish a costly render exceeding the deadline from a stalled
task yield. The next observation adds elapsed task times and the last four
page errors, without altering scheduling, GPU quality or the deadline.

## Measured cause and lifecycle correction — 2026-10-10

Core 38039675000 on ff8e52d5 measures Rendering image… at 0 ms and Encoding
image… at **30254 ms**. No page errors or context loss occur. The guard's
30-second event timeout tears down a legitimate high-quality render before
encoding can write the pixels; the latest failure is not a stalled encoding
promise. The whole-render-under-30-seconds assumption is refuted by phase timing.
This measurement establishes the current failure mechanism, not the uninstrumented
phase of every historical run.

The guard subscribes to downloads before input, waits for the real pending render
to finish within the existing E2E suite budget, requires the successful PNG
status, and retains any event arriving early. Only subsequent file delivery uses
the existing 30-second deadline. The outer core runner's 180-second per-suite
limit is unchanged. Errors, dropped clicks, incomplete rendering, missing
downloads, wrong filename/dimensions or incorrect alpha still fail. No image
resolution, multisampling, shading quality, production renderer or public API is
changed. The previous down/resize/up click-preservation assertion remains.

This is a measured lifecycle/deadline correction, not a larger unexplained
whole-operation timeout. Local and new exact-source hosted verification of the
corrected guard are required before closure.

The corrected guard passes locally through the core shared-Chromium runner,
including the actual PNG filename, dimensions/alpha and downloaded standalone
HTML checks. TypeScript and the E2E build pass. Exact-source hosted core/source-pair
confirmation is pending; the report remains partial until that evidence exists.

Independent source-pair evidence on ff8e52d5 confirms the same measured cause:
Linux 38039674975 reaches Encoding image… at **32994 ms**, with intact context
and no page errors, before the old 30-second event wait aborts it. Its completed
Linux failure and notebook artifact remain available after cancellation of the
superseded pending jobs. This is source-pair phase evidence, not qualification
of the corrected 32565b6d guard.

Corrected-source core 38040586615 fails in `controls-visibility`, before reaching
`studio-usability`; it provides no PNG result. That distinct keyboard focus
transfer is tracked as `uibcdf/molsysviewer#209`, not attributed to PNG.
Source-pair 38040586601 remains active at observation.
