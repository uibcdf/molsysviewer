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

Distinguish notebook output history from Viewer-owned strong references and
identify the retainer before changing the runtime. Prefer small actual-host
lifetime controls over another full heap snapshot on the scale fixture. If
Viewer owns the lifetime, release the retained payload and verify
the cause and actual release, including the still-open witness and popup
independence. A disposed flag or an accessor that stops exposing data is not a
memory correction. Repeat the complete same-kernel gate after that diagnosis,
within the agreed resource stops. This finding does not claim a universal leak,
memory limit or installed/human qualification.
