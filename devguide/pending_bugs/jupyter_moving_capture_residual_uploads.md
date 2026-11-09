---
summary: Investigate residual texture uploads and incomplete moving capture in Jupyter.
issue: uibcdf/molsysviewer#344
status: active
opened: 2026-11-08
closed:
severity: medium
verification: measured
area: [notebook, capture, performance, rendering]
guard:
normative: devguide/transport_state_ownership.md
blocked_by: []
supersedes: []
---

# Residual moving-capture receiving in Jupyter

**Open:** the expanded actual-Jupyter v2 entry is not qualified on production. Its
private working source and original failures are retained. The existing
canonical v1 guard remains unchanged; exclusion of the unqualified expansion
is not a passing moving result. A5/#319 stays partial.

## Current upstream review and isolated receiving

The maintainer requested verification against updated upstream before any
external report. The clean `~/repos@others/molstar` checkout was fetched and
advanced four commits to `6682cc94a230c851e13dbbc6f35fc9d486c0bbdb`.
No upstream code was authored or published. This is the v6 development line,
not the installed Viewer dependency. The fetched v5 branch is
`a4e9cc79415213263090ee47bf380d2a33e0118e` (5.13.1); its text/texture route
retains the earlier unconditional image update on source inspection.

Current upstream already implements the relevant mechanism: shared font
textures keyed by image/spec, image-content revisions, dirty-row uploads and
last-holder release. Its plan is
`.v6/plans/gl/shared-textures.md`; production owners are
`packages/graphics/src/gl/shared-texture.ts`, `gl/renderable/text.ts`,
`gl/webgl/render-item.ts` and `geo/geometry/text/font-atlas.ts`.
The independent native browser probe imports no Viewer or Jupyter code. It
reproduces an unchanged full-atlas upload in installed 5.4.1. Against current
native source, a position-only text rebuild uploads nothing, a new glyph
uploads one row range, complete GPU pixel read-back matches the CPU atlas,
and the last holder releases the GPU resource. This receives that bounded
WebGL mechanism, not all of Mol* v6 or a Viewer migration. The two quality-zero
probes have different atlas dimensions and are not a memory/speed comparison.

**External-report disposition:** the original draft is not published as a new
bug; the current upstream line already addresses its central claim. A possible
v5 backport request needs a concrete useful scope and owner review. The full
dependency migration remains the separate post-1.0 #115 decision. Updating
the inspection checkout changes neither Viewer's lockfile nor its runtime.

A passive actual-Jupyter run identifies 38 full uploads of a 3287 × 3286,
10,801,082-byte atlas consumed by native distance text, totalling 6355.1 ms
(maximum 502.5 ms). Sampled full-byte comparisons are equal. The array match
identifies the distance family; multiple measurements can share it. Scientific
query-handler durations in that run are about 0.2–28 ms, excluding transport
and scheduling. Forwarding through native equal-size subimage loading does
not receive the complete moving guard and is not integrated.

The first new diagnostic fails during *verification after a successful save*:
the oracle calls a public scene reader while a foreign playback callback owns
the scene lock. The corrected independent oracle reads the immutable scientific
source through MolSysMT, retains the source identity/coordinate assertions and
uses the existing ownership wait for final cleanup. Reinspection of the earlier
profile campaign 12 identifies that same oracle failure, not a refused first
save. Earlier unprofiled campaigns 07/11 separately contain actual
`FrontendRequestError` timeouts. Do not attribute every failed case to the font
atlas or combine their distinct causes.

A private exact-byte upload-elision experiment passes all six moving cases
alongside six stopped roundtrips when applied to both actual renderers. It
retains every scientific, post-request frame-change, restore and deadline
assertion. It is not production code or canonical qualification: its bounded
CPU snapshots, lifecycle and dependency ownership require separate review
before choosing a supported consumer solution. The same corrected-oracle
control without texture optimization fails a real Python session capture
timeout after three moving cases. The paired observations support the atlas
cost as a material contributor, without proving a universal timing guarantee.
The experimental cache retains 43,204,328 extra CPU bytes per canvas; it is
not the chosen production infrastructure. See the
[sanitized review and receiving record](../molstar_font_upload_upstream_review_20261108.json)
for all six distinct campaigns, original failure scopes and private custody.

The six original stopped-scene cases pass before expanded moving receiving.
Campaigns 08/10 receive four primary Studio/Python state/session moving saves;
07/09/11 receive one. These distinct prefixes are not combined into full
acceptance. Earlier 01–06 stop before moving capture because of #343's
independently reproduced acknowledgement loss. Source/provider manifests,
raw diagnostics and owned-process cleanup remain private.

The final holder releases only the requesting canvas's genuine dynamic-region
requests on its second actual post-request frame change. It avoids a separate
four-second rAF polling bound, which could abandon Studio before its existing
ten-second deadline. It retains the original public five-second Python default,
camera motion, trajectory playback, native geometry, independent saved-file
recovery and source immutability. The next unprofiled run still times out in
Python after one moving Studio save. Native readiness shows interaction/dynamic
projections behind the current frame on several otherwise-ready draws.

One diagnostic renderer CPU profile records 20.053 s and 13,963 samples. Its
dominant `texImage2D` frame accounts for 6.367 s exclusive and another for 0.312 s.
The profiled campaign fails its first moving case during the verification
oracle, as clarified above; it is diagnostic, not a gate pass. The production runtime remains SHA-256
`337576d70c249194d550b95a187b3a43da7fffef1a83189c818f679979f9230a`.
The exact scientific provider is `42f5ed3bc8f02c979b3351212554e588243de0a5`.
Receiving uses real Jupyter/anywidget/Mol*/SwiftShader, with eight logical CPUs,
six GiB and a two-GiB shared-available reserve; no resource stop occurs.

## Next bounded investigation

Separate the corrected oracle-only control from the private content-cache
experiment. Select a bounded supported consumer route, preserving current
quality and actual glyph updates, before changing production rendering. The
native atlas cost is measured and independently reproduced; transport and
popup convergence still retain their own acceptance. Closed #340 owns its
received custom-annotation correction and is not reopened by this finding.

Keep failed/profiled receiving and complete ownership/deadline assertions.
Do not patch node_modules, manufacture scientific replies, lower scientific
coverage or turn a passing prefix into a complete run. Qualify the full actual
host entry before advertising v2. Installed, human and wider platform acceptance
remain separate; releases and both 1.0 versions stay paused.
