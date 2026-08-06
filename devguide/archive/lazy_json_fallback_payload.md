# Remove ViewerJSON and build portable JSON only on demand

**DONE, and the header was the last thing that did not know it.** It said
"implemented in the Phase 3 working tree; validation and measurement pending" —
all three parts have existed for some time.

- **Implemented**: `_new_lazy_molecular_projection` and `is_lazy_molecular_message`
  in `viewer/core.py`.
- **Validated**: `tests/test_lazy_molecular_projection.py`, including that the
  projection materialises once, returns defensive copies, and refuses a stale
  molecular revision before building.
- **Measured**: [`../performance/pre_1_0_rework_baseline_2026_08.md`](../performance/pre_1_0_rework_baseline_2026_08.md)
  — registering the generation-bound lazy projection before the frontend is
  ready takes **32 ms**, against **1,459 ms** for a direct portable-JSON load,
  and the successful binary path builds portable JSON zero times, so that cost is
  absent rather than hidden.

Archived 2026-08-06 during a sweep for reports that outlived their subject.

---
**Status:** implemented in the Phase 3 working tree; validation and measurement
pending.

## Decision

MolSysViewer no longer uses `molsysmt.ViewerJSON` as an internal representation.
The authoritative scientific object remains `molsysmt.MolSys`.

The two delivery encoders read that object directly:

- the normal array-native path emits topology metadata plus typed structural
  buffers;
- the compatibility/static path emits the existing `load_molsys_payload` JSON
  schema only when a non-binary consumer, fallback, popup snapshot or static
  export actually needs it.

This removes an intermediate model without removing the portable JSON boundary.
The latter is still required for compatibility and self-contained exports.

## Previous defect

Every load used to convert `MolSys -> ViewerJSON`, normalize it into nested
Python lists, and retain that complete message before binary capability
negotiation. Successful binary delivery therefore paid for a JSON payload that
was never sent and temporarily retained both representations.

Historical timings in this document were useful to locate the defect but are
not acceptance evidence: profiler overhead and an upstream MolSysMT deep-copy
fix changed their magnitude. Phase 3 uses current wall-clock measurements.

## Implemented design

`load_from_molsysmt` converts the input once to `molsysmt.MolSys` and records a
`LazyMolecularMessage`. Its producer is:

- memoized;
- bound to a molecular revision;
- rejected if that revision is no longer current;
- deliberately non-JSON-serializable until an explicit transport/export seam
  materializes it.

`StructureTransfer` owns a fallback factory bound to its exact transfer
generation. Binary completion never invokes it. Refusal, timeout and connector
failure invoke it once and deliver direct JSON with the same target identity.

Both encoders share one static topology extractor. The JSON encoder reads
coordinates and optional box/time from `MolSys.structures`, converts units at
the boundary (angstrom and ps), and never invents missing box or time.

## Acceptance

- Product Python contains no request for `molsysmt.ViewerJSON`.
- A complete negotiated-binary load performs zero JSON builds.
- A non-binary load and a failed/timed-out stream build JSON exactly once.
- A fallback cannot serialize a newer molecular revision under an older
  transfer generation.
- Popup and export seams return ordinary serializable dictionaries; the lazy
  marker never crosses the wire.
- Direct JSON and array-native encoders expose the same topology and preserve
  optional structure metadata.
- Wall-clock and retained-memory measurements are repeated after the change.

## Mutation evidence required

- Remove the molecular-revision guard: the stale-projection test fails.
- Bind fallback to the manager's current generation: the exact-generation test
  fails.
- Force JSON construction on binary success: the zero-build test fails.
- Return the lazy marker from export: JSON serialization of the export fails.
