---
summary: Identify why closed notebook controllers retain molecular data during repeated real work.
issue: uibcdf/molsysviewer#356
status: active
opened: 2026-11-10
closed:
severity: medium
verification: measured
area: [jupyter, memory, lifecycle, performance]
guard:
normative:
blocked_by: []
supersedes: []
---

# Retired notebook molecular data — diagnosis active

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

Distinguish notebook output/model ownership from MolSysViewer-owned strong
references. Use weak observation to trace the actual AnyWidget view, target
and model lifetimes alongside the controller before changing the runtime. The
next reduced probe records the lifetime of the model proxy, widget element,
abort signal and returned cleanup in the same samples as the controller. It
remains unexecuted after the resource review refused a new Chromium session
with swap full and recent exchange activity. If
MolSysViewer owns the lifetime, release the retained payload and verify
the cause and actual release, including the still-open witness and popup
independence. A disposed flag or an accessor that stops exposing data is not a
memory correction. Repeat the complete same-kernel gate after that diagnosis,
within the agreed resource stops. This finding does not claim a universal leak,
memory limit or installed/human qualification.
