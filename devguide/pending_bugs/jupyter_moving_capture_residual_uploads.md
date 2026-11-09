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

**Open:** the expanded actual-Jupyter v2 entry does not pass globally. Its
private working source and original failures are retained. The existing
canonical v1 guard remains unchanged; exclusion of the unqualified expansion
is not a passing moving result. A5/#319 stays partial.

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
The profiled campaign fails its first moving save; it is diagnostic, not a gate
pass. The production runtime remains SHA-256
`337576d70c249194d550b95a187b3a43da7fffef1a83189c818f679979f9230a`.
The exact scientific provider is `42f5ed3bc8f02c979b3351212554e588243de0a5`.
Receiving uses real Jupyter/anywidget/Mol*/SwiftShader, with eight logical CPUs,
six GiB and a two-GiB shared-available reserve; no resource stop occurs.

## Next bounded investigation

Identify actual texture dimensions/owners and backend-query/draw timing before
changing rendering. Mol* 5.4.1 `Text.update` always advances its font-texture
ValueCell. Native measurement text is a lead, not an identified culprit; other
textures and transport costs remain possible. Closed #340 owns its received
custom-annotation correction and is not reopened from this profile alone.

Keep failed/profiled receiving and complete ownership/deadline assertions.
Do not patch node_modules, manufacture scientific replies, lower scientific
coverage or turn a passing prefix into a complete run. Qualify the full actual
host entry before advertising v2. Installed, human and wider platform acceptance
remain separate; releases and both 1.0 versions stay paused.
