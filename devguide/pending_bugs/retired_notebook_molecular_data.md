---
summary: Identify why closed notebook controllers retain molecular data during repeated real work.
issue: uibcdf/molsysviewer#356
status: partial
opened: 2026-11-10
closed:
severity: medium
verification: measured
area: [jupyter, memory, lifecycle, performance]
guard: tests/test_jupyter_live_capture.py::test_live_jupyter_controller_release
normative:
blocked_by: []
supersedes: []
---

# Retired notebook molecular data — cache correction; prolonged receiving pending

After 15 complete E2 cycles in one actual Jupyter kernel, the independent
1TCD witness is the only connected controller. Thirty other controllers remain
observable through weak references despite being marked disposed and detached;
all still expose a 62-atom molecular structure. The observer checks that GC
is exposed and invokes it before sampling; it does not keep a strong list of
controllers. It has not identified a retaining path or certified VRAM release.

In campaign `265`, browser-reported heap reaches 752.2 MiB. The cgroup's last
completed-cycle current/peak samples are 3166.7/3267.1 MiB, with no recorded
max/OOM events at that point. Shared memory pressure then crosses the agreed
limit during cycle 16 (full avg10 2.54, about 11.9 GiB globally available and
zero swap activity). All 26 owned processes retire and 10,890 inputs stay
unchanged. This pressure observation does not identify which allocation or
process caused it. Summed RSS includes shared mappings and is not cgroup RAM.

Viewer `cb326235b3377185b18a17c7f59c71fd53cdab2a` and the source receiver
`66273e4d3ad722726336055b4bf38dc76761e35e` (MolSysMT PR #706) are identified in
the [prolonged-session receipt](../prolonged_scientific_session_receiving_20261110.json).
#354's recovered-frame observation did not recur in these 15 cycles. Neither
that non-reproduction nor native exit zero completes the interrupted campaign.

The single-cycle actual-host diagnostic `270` again observed two retired
controllers; its full heap capture lost the browser target and yielded no
usable snapshot. The cheaper differential `271` completed. It disposed the
four notebook element handles obtained by the observer and sampled after GC
on two separate tasks. Both 62-atom retired controllers remained observable
in both samples, alongside the connected 1TCD witness. Releasing those handles
alone is insufficient. Neither diagnostic explains the earlier shared pressure.

The reduced Jupyter workflow in `274` reproduces without edits, popups,
playback or a retained element handle. Closing and dropping the 62-atom View,
then replacing its notebook output, still leaves its detached controller
observable after collection. The 22-atom witness remains connected. The
victim is the bundled pentalanine trajectory (5,000 structures), despite the
probe's original scope label; its witness is the one-structure dialanine.
The continued presence of the removed output element is not a necessary
condition. This does not rule out notebook/widget runtime retention after
removal or a dependence on trajectory size.

`276` selects only pentalanine structure 0 and asserts that each View has one
structure before display. The same retired 62-atom controller remains after
closing and replacing its output; the independent 22-atom witness survives.
The full trajectory is therefore not necessary to reproduce the observation.
The probe exits normally in 48.00 s at 2 CPUs / 4 GiB without swap or resource
stop; all 20 owned processes retire and 10,904 selected inputs stay unchanged.

The direct host control `285` creates the same 22- and 62-atom systems from
their single-structure JSON payloads with actual Mol* draws and no widget.
After disposal and DOM detachment, both separate GC samples report that the
retired controller is unreachable and the independent witness is connected.
The 18.10 s probe uses 2 CPUs / 4 GiB, retires all 13 owned processes and
preserves all 10,910 inputs. This control differs from Jupyter in both host
ownership and input transport.

The matched array-native comparison `290` uses the same two single-structure
systems and binary coordinate decoder in both paths. The direct host releases
the 62-atom retired controller in both collection samples. The actual Jupyter
widget confirms array-native loads of both systems and still exposes the
retired 62-atom controller after close and output replacement. The independent
22-atom witness stays connected in both paths. This isolates the next comparison
to the widget lifecycle and notebook host, including the earlier messages in the
widget transport. The array-native decoder alone is insufficient to explain
retention. The 49.18 s run at 2 CPUs / 4 GiB retires 34 processes, preserves all
10,942 inputs and reports no resource stop. The receipt records both observations.

The adapted-widget control `295` keeps the actual production widget bootstrap
and real Python authority, with the notebook model/comm replaced by the test
transport. The retired 62-atom controller stays observable while the detached
test model is retained. Dropping that model releases the controller in both
collection samples. In actual Jupyter, `296` explicitly unregisters 17 tracked
widget-model subscriptions and releases the original cleanup callback after it
runs. The retired controller still has the 62-atom structure after output
replacement and collection, and the 22-atom witness stays connected. The test
model's behavior therefore does not establish the actual retaining path.

The bounded heap capture `275` loses the browser target in the same workflow.
Its private partial stream reaches the 128 MiB recording cap; it is not
a valid heap snapshot and proves no retaining path. The supervisor retires all
owned processes. Avoid further full heap snapshots on this shared host.

The real-Jupyter ownership probe `302` observes the retired view's abort event.
After output replacement, its abort signal and returned cleanup are unreachable
in three samples. Its host element, model proxy and controller remain reachable.
The connected witness and its ownership remain intact. `303` removes the resize
handle from the retired host, then removes its remaining child. In both stages
the retired controller still exposes the 62-atom structure after collection.
The retained host's child nodes are therefore insufficient to explain the
observation. The probes do not establish the direction of ownership between
the surviving host element, model proxy and controller.

The native-model registry probe `307` confirms that the retired model is
closed, has no comm or registered views, and is absent from both Jupyter
manager indexes. Its settled `state_change` still resolves to the old widget
view. Replacing that settled promise only in the closed test model leaves the
62-atom controller observable in both collection samples. Neither manager
registration nor that retained promise alone explains the remaining lifetime.

## Current causal receiving — 2026-11-11

The detached canvas output retains `molsysviewerOpenPopup` and
`molsysviewerClosePopup` closures; its resize handle also has an unreleased
callback. In the reduced actual-notebook differential `459`, removing the
retired children alone leaves its controller reachable. Removing the two
popup properties then releases the controller, native structure/model and
the observed coordinate axis array in both GC samples. The independent
22-atom witness remains connected. The coordinate backing buffer remains
reachable, so that diagnostic correctly exits with a failed buffer assertion.
The preceding `458` attempt fails at Chromium startup because its Unix socket
path is too long; it never tests the product.

The source correction retires only the closing render's popup methods, its
resize handle/active drag listeners and its own target element. Independent
result surfaces retire their corresponding methods too. It does not modify
the structure accessor or replace live scientific data. The permanent real
Jupyter guard fails on the original runtime (`460`) and passes on the corrected
runtime (`462`): retired controller/structure/model/axis collection is actual,
the independent witness's coordinate values are unchanged and it completes a
fresh native draw. Popup methods belonging to a later mount are preserved by
identity checks.

This is a partial correction. The one-structure 62-atom case still observes
its 744-byte coordinate backing buffer after controller collection. Neither
the guard's narrower passing scope nor the reduced array size proves the
owner or scaling of that residual lifetime. Preserve the failed `459` scope;
do not credit E2 or run the full thirty-cycle gate as though #356 were closed.
The [receiving record](../widget_controller_release_receiving_20261111.json)
separates native receiving, fixture correction #362, integration and custody.

The [buffer-isolation receipt](../jupyter_buffer_isolation_receiving_20261111.json)
receives the smaller direct controls `478`, `480` and `481`. The controller,
plugin, structure/model, trajectory and all three coordinate axes collect; the
744-byte input buffer remains reachable without Jupyter. Equal-size unowned
decoded/planar controls collect. Targeted prototype queries find no matching
Float32Array, Uint8Array or DataView; clearing the console and four separate
collection tasks without dereferencing the targets do not release the buffer.
This narrows the comparison but identifies neither its owner nor its scaling.
The direct control does not qualify actual-notebook memory release.

The heap diagnostic `479` terminates before producing a usable snapshot; its
native SIGTERM and unknown cause remain recorded. The installed Chromium does
not support `482`'s targeted V8 tracing intrinsic. Neither attempt supplies a
retaining path or evidence of a product failure. Do not repeat full snapshots
on this shared host. Next isolate native/input-buffer ownership with a bounded
control, then receive the residual disposition and complete same-kernel gate
within the agreed resource stops. Universal memory/VRAM bounds, installed/human
qualification and a cause of the original pressure stop remain unestablished.

## Working cache finding — 2026-11-12

The [new receiving record](../molstar_component_cache_receiving_20261112.json)
identifies a native retaining path. Without an explicit `chem_comp` table,
Mol*'s private `getUniqueComponentNames` calls `memoize1`, whose strong Map
keys retain BasicData, `atom_site`, coordinate columns and shared backing
storage. Five direct molecular cycles retain five non-detached 744-byte
buffers. Native CPU parsing and a smaller component-properties-only control
reproduce without Jupyter, a controller or WebGL.

After a clean fast-forward pull to upstream `dabbf29f9`, selected unmodified
v6 source modules reproduce the same fallback retention. Five explicit-table
controls collect. A private WeakMap-only differential releases all ten inputs
and preserves complete chemical/saccharide maps. This is selected-source
evidence, not the complete upstream suite or installed v6 qualification.

The working MolSysViewer repair applies that cache-lifetime change at build
time only to exact reviewed Mol* 5.4.1 source bytes. Runtime, harness and unit
builds share the adapter; installed dependencies and scientific data are not
edited. Its actual-Jupyter guard fails on the original runtime (`499`) and
passes after rebuilding (`503`), now checking backing-buffer collection too,
unchanged independent coordinates and a fresh witness draw. All 443 JS units
pass. The five-cycle corrected repeat `502` stops for shared pressure before
browser receiving and is not passing evidence.

This correction is working source, not integrated or final E2 acceptance.
Focused build/reporting checks, the prolonged campaign and compatibility
removal/expiry documentation remain pending. Diego requested a critical report
after pulling upstream and before publication; no upstream issue/PR is
authorized or published. Retain the current partial state and distinguish
this cause from the separately open consolidated-capture issue #344.

The [pre-publication review](../molstar_component_cache_report_review_20261112.json)
finds that upstream already tracks this exact cause as audit `01/B1 = 04/B1`.
PR #2032 explicitly leaves it pending a forced-GC heap-tier regression, with
later deferrals in #2045/#2046/#2048. The earlier issue-only search did not
establish novelty. Unmodified registry-verified 5.4.1 and current public 5.13.1
tarballs both reproduce the exact draft snippet. Caller/empty-table and
negative/positive ownership controls pass on 5.13.1. Reframe any proposed
contribution as a follow-up to the known audit, preferably a usable regression;
do not publish the earlier draft as a new finding. No upstream write is
authorized or has occurred.

Diego chose uibcdf/molsysviewer#363 for native-resolution monitoring instead
of another upstream report. The
[compatibility contract](../molstar_component_cache_compatibility.md) records
the narrow build repair, ownership, review deadline and removal condition;
the [follow-up](../pending_proposals/molstar_component_cache_upstream_followup.md)
keeps published-native adoption separate from #356's local receiving.

The corrected direct five-cycle control `508` releases all retired molecular
backing buffers and preserves the independent witness and its fresh draw.
Build/refusal controls pass ten cases (`507`); the shared-builder reporting
recovery passes 418 (`510`), and its complete covering quality collection
passes 442 with three explicit live-Jupyter opt-in skips (`512`). Ruff,
formatting, queue and diff checks pass. The original stale-validator failure
`509` and wrong-working-directory invocation `511` remain preserved; neither
is silently counted as a pass. These scopes overlap and do not constitute one
full suite. The thirty-cycle actual-Jupyter attempt `513` passes three cycles,
then fails the fourth popup's unchanged 30-second wait for structure 1 after
the receiver focuses Next and sends Enter. The main trace records no corresponding frame-1
request; the popup still displays 1 / 5000. Readiness, event delivery and cause
remain unestablished. Its 6,156 inputs are unchanged, no resource stop occurs,
and all 26 owned processes retire. Isolate that control before another full
campaign. Do not merge it with #354's recovered-widget observation or #305's
hosted context-menu failure. No prolonged acceptance or original outcome is
credited; the exact cache/backing-buffer guard remains a separate pass.

The [corrected receiver receipt](../jupyter_popup_controls_receiving_20261112.json)
reproduces the hidden-control focus race separately and records actual kernel
imports through MolSysMT PR #721. Its `519` campaign completes thirty scientific
cycles in one kernel over 1,749.912 s. All 10,182 selected inputs are unchanged;
all 25 owned processes retire and no resource stop occurs. The last weak
controller observation contains only the connected 3,983-atom witness.

Keep memory acceptance partial: median Python RSS stays within the observed
block ranges and median cycle time is about 57–59 s, but median browser JS heap
grows from 225.682 to 312.548 to 397.349 MiB. Charged-memory medians also grow
from 1,902.945 to 2,197.049 to 2,429.283 MiB. That is not by itself a retaining
path, a leak diagnosis or evidence of a new Mol* defect. Attribute it with a
small controlled comparison, retaining the original scientific and ownership
checks; do not repeat full heaps or another thirty-cycle run blindly.
