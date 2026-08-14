# Qt payload copies, and endpoint-scoped scene deferral

**Measured 2026-08-06, linux.** Closes items 7 and 8 of
[`../pending_proposals/transport_popup_audit_followups_2026_08.md`](../audits/transport_popup_audit_followups_2026_08.md).
Both were "measure before deciding" items; neither produces a change here, and
both now have a number instead of an expectation.

## Item 7 — endpoint-scoped scene deferral during popup bootstrap

The question was whether one view-wide S8 barrier makes the embedded host feel
stalled while a large canvas popup is being delivered. Phase 5 replaced that
barrier with one transfer gate and deferred queue **per destination**, so the
measurement is now a confirmation that host traffic does not wait behind a
popup's structure.

```bash
python devtools/benchmarks/endpoint_isolation.py
```

| Quantity | Value |
| --- | --- |
| System | 95,000 atoms, synthetic, physically spaced |
| Popup transfer | deliberately left in flight |
| Threshold, fixed **before** running | 100 ms |
| Embedded-host projection latency | **0.0097 ms** |

Four orders of magnitude under the threshold. The number was already recorded in
the Phase 5 dashboard row and inside the audit item; it was never written where
performance evidence lives, which is why item 7 kept reading as open. It is here
now.

The completed Phase 5 implementation was revalidated on 2026-08-08 after its
endpoint-lifetime generation fix. The same 95,000-atom case measured **0.0111
ms**, still four orders of magnitude below the predeclared threshold. The
benchmark now calls the known `string:pdb_text` converter directly: generic
MolSysMT form detection on a very large in-memory string is not part of endpoint
isolation and had dominated the benchmark before parsing began. A proposal for
bounded detection and a public known-source-form path is recorded in
[`../pending_proposals/molsysmt_known_source_form_and_large_string_detection.md`](../pending_proposals/molsysmt_known_source_form_and_large_string_detection.md).

**This does not measure the browser side.** It measures that Python delivers the
host's projection to its connector without waiting for the popup's stream, which
is the property the item is about.

## Item 8 — copies and peak memory in the Qt binary scheme

Qt's bridge assembles the structural buffers into one Python `bytes` object
before Chromium fetches it:

```python
blob = b"".join(bytes(buffer) for buffer in payload.buffers)
```

AnyWidget hands the same buffers to its connector without joining, so this cost
is specific to Qt and had never been measured.

```bash
python devtools/benchmarks/qt_payload_copies.py
```

Measured with `tracemalloc`, not RSS. RSS cannot answer this: the allocator keeps
freed arenas, so a released transient leaves no trace — the first draft of the
benchmark reported an identical "retained" figure before and after `del blob`,
which is a fact about the allocator, not about the code.

| Case | Payload | Join, peak | Preallocated `bytearray`, peak |
| --- | ---: | ---: | ---: |
| pentalanine, 5,000 structures | 3.76 MB | 7.52 MB | 7.31 MB |
| 4V4Z (ribosome, 149,640 atoms) | 1.71 MB | 3.43 MB | 3.43 MB |
| synthetic | 50 MB | 100 MB | 66.67 MB |
| synthetic | 200 MB | **400 MB** | **266.67 MB** |
| solvated HP35 supercell, 104,856 atoms x 100 structures | **120 MB** | **240 MB** | **240 MB** |
| solvated HP35 supercell, 314,568 atoms x 10 structures | **36 MB** | **72 MB** | **72 MB** |

**The rule is exact: the join peaks at 2× the payload.** `b"".join(...)` over a
generator materialises every per-buffer copy *and* the output simultaneously, so
the transient overhead equals the payload at every size measured. The
preallocated alternative peaks at 1× the payload plus the largest source
buffer — 1.33× when three similarly sized buffers are used, but still 2× when
one coordinate buffer dominates a representative molecular payload.

### Decision: keep the join

The audit's own rule is to change this path only if the peak is release-relevant
*and* a lower-copy path exists. The second half holds; the first does not, today:

- Every system MolSysViewer ships measures **under 4 MB**, where the transient is
  a few megabytes and unobservable.
- It becomes material only for trajectories in the hundreds of megabytes, and
  `DEFAULT_COORDINATE_BUDGET_BYTES` already warns at **256 MB** of coordinates —
  where the join would peak at 512 MB. **That is the number to remember:** a load
  the scale guard merely warns about costs double on Qt, and nothing says so at
  the warning.
- The preallocated alternative only lowers the peak when the payload is split
  across several similarly sized buffers. It does not help representative
  coordinate-dominated payloads. A meaningful improvement near the warning
  budget needs a lower-copy Qt delivery design, not a different join loop.

So this is deferred with a trigger rather than rejected: **if Qt is expected to
carry loads near the scale budget, design and benchmark a lower-copy delivery
path.** Do not adopt the preallocated `bytearray` without an A/B on a real
coordinate-dominated payload. The AnyWidget path needs no equivalent, because it
never joins.
