---
summary: Keep scientific mirror picking geometry inside the native camera depth interval.
issue: uibcdf/molsysviewer#402
status: partial
opened: 2026-11-17
closed:
severity: medium
verification: reproduced
area: [tests, picking, camera, qualification]
guard: molsysviewer/js/tests/e2e/canvas-popup-mirror.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Mirror picking camera precondition

**Source receiving complete; covering CI pending:** source recovery
`44031725024` fails the first sphere pick after successful popup bootstrap and
bidirectional navigation. Native causal controls receive both the camera-depth
and physical-pixel corrections; the complete canonical mirror passes in `1027`.
The [receipt](../mirror_camera_clipping_receiving_20261117.json) preserves the
original failures and actual scopes. This is
separate from #344's actual-Jupyter popup initialization observation.

The run consumes MolSysViewer `c08d4990` and MolSysMT `4b0b1f8a`. Python
passes 4,743 cases with 42 skips and 17 deselections; all 25 documented notebooks
execute successfully. Three core entries complete before entry four fails.
The two original ZIPs match GitHub's sizes and SHA-256; the original job log
is retained privately. This is not a complete green source gate.

The fixture requests position `[0,0,120]`, target `[0,0,0]`, radius 50 and
radiusMax 100. Mol* 5.13.1 derives radiusMax from the actual scene and clamps
radius to 30.52230923. Its near plane is then 89.47769077. The sphere at
`[30,30,30]` Å, radius approximately 3 Å, intersects that plane. A private
image shows a crescent: the original probe grid is over the removed front.
The object's existence, visibility and pickability cannot establish that this
particular camera leaves its surface available for the intended pick.

Minimal diagnostic `1021` reproduces zero primary sphere hits, then fails
its own incorrectly placed fresh-draw wait on the idle popup. That original
is retained as a diagnostic setup failure. Corrected `1022` observes each
new draw relative to the instant before the camera intent. In both windows,
the original camera yields zero sphere hits and positive label hits. With
position `[0,0,135]` and target `[0,0,15]`, the unchanged native geometry and
probe grid yield positive sphere and label hits in both windows. This receives
the clipping discrimination, not the omitted preceding navigation workflow.

The correction centres the fixture's depth framing and receives an explicit
native near/far precondition after its applied draw. It keeps the original geometry, real GPU
identification, single physical clicks, marker assertions, updated-label and
occurrence controls, complete mirror workflow and all deadlines. Production
camera behavior, native clipping and the hidden-unit-cell correction remain
unchanged. The complete canonical mirror is received below; preserve this
failed source run and receive the applicable covering source gate.

Duplicate review acquires all four issue pages: 373 issue/PR entries and 347
issues in all states. #388 concerns selection after a successful hit; #389
concerns a pending native buffer read; #400 concerns idle camera echo. None
establishes this fixture's clipping precondition. No new MolSysMT scientific
defect, installed acceptance or publication is claimed.

## Complete causal control

`1023` passes types and the canonical E2E build, then executes the complete
mirror up to the new native clipping precondition with the original camera.
It fails that assertion directly: the sphere's front depth is 86.98458027,
before the near plane at 89.47769077; the label remains inside. All preceding
navigation and selection phases pass. The 292.66-second bounded execution
keeps all 9,995 selected inputs unchanged, triggers no resource stop and retires
all 25 owned processes. This is the expected causal negative, not a green
mirror run or an aggregate-budget failure. Its exact source variant is retained.

The corrected fixture shifts camera position and target together by 15 Å in
depth. No production/runtime byte changes. Complete `1024` passes this native
precondition and the sphere's real click/markers, then fails the original
primary annotation selection predicate. It is not a passing complete mirror.

Minimal `1025` retains passive DOM, native-input and plugin-click events.
The single sphere click succeeds in both endpoints. The primary annotation
click reaches the canvas and native input, but its plugin event has empty
loci. The diagnostic queried a fractional screen y-coordinate (147.05242918),
whereas the actual mouse event delivers y=147. Native coordinates include the
canvas offset (139 rather than 139.05242918). Mol* flips and floors that
coordinate when reading a pixel. Receive matched native probes of the
fractional and actually delivered physical point before attributing a native
picking, focus or selection defect. Keep the original failed `1024`/`1025`
and all single-click/marker assertions.

Matched `1026` queries those two points against the same actual native buffers:
the fractional coordinate identifies `mirror-label`, while its integer mouse
coordinate returns no hit. Testing integer candidate coordinates before choosing
the original single click selects both objects in both windows. No focus repair,
selection injection, repeated click, delayed interaction or native patch is
needed. The canonical mirror now queries integer screen coordinates before
using them for the real mouse action; its complete receiving remains separate
from this minimal control.

## Complete current mirror received

`1027` passes types/build and the entire canonical mirror at 4 CPU / 4 GiB:
both camera directions, exact atom selections, real sphere/annotation clicks
and both selected markers, revised-label pending/synchronous identification,
old-occurrence refusal, window-local Dock, scene visibility and stopped
frame-specific interactions/playback. Its 358.86-second outer invocation
retains all 9,995 selected inputs and retires all 25 owned processes without
a resource stop. The original 480-second suite allowance and all operation
deadlines remain unchanged. Production/runtime bytes match `c08d4990`.

Published `0ea58be0` delivers the fixture corrections. Its single
[full Linux source recovery](https://github.com/uibcdf/molsysviewer/actions/runs/44118070148)
is in progress, not accepted; keep the issue partial until that gate is
received. #344, installed/native-host,
human and final-candidate acceptance remain separate.

The scoped reporting/build-route checks pass 552 cases with zero skips, and
the generated indexes are current. Selected original failures, input manifests,
native observations and both verified CI ZIPs are hash-verified in Diego's
approved private custody; the receipt retains the manifest digest.
