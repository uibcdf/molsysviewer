---
summary: Wait for actual native screenshot assets before PNG and Movie rendering.
issue: uibcdf/molsysviewer#382
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: measured
area: [export, rendering, movie]
guard: molsysviewer/js/tests/e2e/studio-image-export.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Resolved: first PNG waits for native SMAA uploads

**Resolved 2026-11-13.** The initial investigation below retains its original
scope; the Resolution section names the current correction and receiving.

Receive bounded, cancellable readiness without warming the renderer or
changing the requested quality. Keep the private native seam explicit,
byte-qualified and replaceable by a future public native readiness API.

Independent control 757 uses real pentalanine without detached Studio or
PNG routing. Its first ordinary export has encoded SHA-256
'0c02595b9a87ee382c0eb02bd27b20b7c5cb5db3a249f8aae2463c8165605617';
repeated native and cancellable exports share
'71bea85715ca0d4fc44c8961b0bfc8ba795ea69e84f68655c9b8c2b1b8731273'.
They match the respective #380 first/repeated PNGs byte-for-byte. Camera,
background and inspected native settings remain identical. This establishes
the native first-use distinction, not a version regression.

Installed Mol* 5.13.1 constructs SMAA textures through 'loadImageTexture':
new images upload in 'onload', without a readiness promise. The pending causal
control receives actual texture dimensions before rendering, first/repeated
pixels and cancellation/timeout. The source adapter reads those exact native
textures; it does not patch their contents, preload extra renderers or silently
switch antialiasing. All runtime/harness/unit builds reject changed reviewed
native bytes. Current controlled receiving remains pending.

The all-state inventory before filing has four pages and 352 issues, excluding
PRs. No equivalent focused record was found. No external Mol* issue has been
published; any external disclosure retains the maintainer review requirement.

## Resolution

The source reader awaits the actual qualified SMAA lookup dimensions:
area 160 x 560 and search 66 x 33. Native 1 x 1 placeholders are explicitly
not readiness. The wait has a five-second internal bound, caller/controller
cancellation and deterministic timer/listener retirement. Failure refuses
rendering; antialiasing, sampling and source images are never substituted.
Legacy PNG, detached PNG and Movie share this boundary. A closed controller
does not resume rendering or restore state into its disposed plugin.

All five native implementation files are checked against committed reviewed
digests and exact 5.13.1 metadata before runtime/harness/unit output. The
read-only private chain is deliberate until a native public readiness API can
replace it. Later version review under #115 must reconsider it; no external
issue was published.

Source type/runtime/harness/entry builds and 490 units pass in 761, including
partial upload, placeholder rejection, timeout, cancellation/retirement and
unqualified-seam refusal. Current actual-browser 762 observes placeholders
before the first capture and real lookup dimensions before rendering; its
first/repeated PNGs equal independent native decoded RGBA SHA-256. Opaque and
nested-popup paths also pass. Native Movie regression 763 receives media,
recipe, overlays, real task cancellation and preserved unrelated tasks.
Native bytes and selected source inputs remain unchanged throughout receiving;
cleanup is complete. Earlier failed comparisons and independent native-only
control 757 are retained, not relabelled as current qualification.
