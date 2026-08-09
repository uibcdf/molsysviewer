# Representative performance and memory gate - August 2026

## Purpose and status

This is the Phase 8 measurement record for
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md).
It measures atom count and structure count independently, using real molecular
systems. It is a baseline, not a claim that every cell is interactive at 60 FPS.

**Status:** measured on 2026-08-09 from `3a2aaaf3`; the Phase 8 implementation
and this evidence were committed as `15d86a8a` and await independent audit.
Python results are medians of three fresh processes. Browser cells are
single measurements unless a range is shown. Hardware-GPU VRAM was unavailable;
browser rendering used SwiftShader and process RSS is therefore not VRAM.

## Environment

- Python 3.13.14; Node 24.11.1; npm 11.11.0.
- Mol* 5.4.1; Chrome 149.0.7827.53.
- Linux 7.0.0-28-generic; 20 logical processors; 31.2 GiB RAM.
- WebGL2 through ANGLE and SwiftShader.
- `sandbox/Smoke_Test.ipynb` was developer-owned and excluded.

## Reproducible fixtures

The atom axis uses intact, translated molecular cells rather than coordinate
clouds:

| Case | Source | Construction | Atoms |
|---|---|---:|---:|
| small | 181L crystal (protein, water, ion, ligand) | 2 cells | 2,882 |
| medium | solvated HP35 | 6 cells | 26,214 |
| large | solvated HP35 | 24 cells | 104,856 |
| xlarge | solvated HP35 | 72 cells | 314,568 |

Cell-vector translations preserve molecular geometry and periodic spacing. Box
vectors are retained. Structure sequences contain a small deterministic rigid
drift, but no time is invented: `time` remains absent. Fixture reading, merging
and replication are MolSysMT work and are timed separately.

The durable entry points are:

```bash
python devtools/benchmarks/representative_scale_gate.py \
  --case large --structures 100 --repeats 3 --table-row
cd molsysviewer/js
MOLSYSVIEWER_SCALE_MATRIX=small:1,small:10,small:100,medium:1,medium:10,medium:100,large:1,large:10,large:100,xlarge:1,xlarge:10 \
  npm run bench:representative-scale
```

## Python data-plane results

Times are milliseconds. `Peak growth` is the whole fresh worker, including the
separately reported MolSysMT fixture, payload and view; it must not be attributed
to MolSysViewer alone. `View-cycle delta` is RSS after closing and deleting the
view minus RSS immediately after serialization while fixture and payload remain.
Allocator reuse can make lifecycle deltas noisy or negative, so only their
absence of scale-proportional retained growth is used as evidence.

| Atoms | Structures | Binary MiB | Metadata MiB | MSV serialization | MSV registration | Worker peak growth MiB | View-cycle delta MiB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,882 | 1 | 0.033 | 0.268 | 30.57 | 30.14 | 355.77 | 0.344 |
| 2,882 | 10 | 0.330 | 0.268 | 30.44 | 29.41 | 359.89 | 0.008 |
| 2,882 | 100 | 3.302 | 0.268 | 32.51 | 30.69 | 387.93 | 0.012 |
| 26,214 | 1 | 0.300 | 1.964 | 143.62 | 30.61 | 366.81 | 2.758 |
| 26,214 | 10 | 3.000 | 1.964 | 145.22 | 34.76 | 397.81 | 0.574 |
| 26,214 | 100 | 30.003 | 1.964 | 177.02 | 43.49 | 563.99 | 0.043 |
| 104,856 | 1 | 1.200 | 8.186 | 538.44 | 34.27 | 443.34 | 15.805 |
| 104,856 | 10 | 12.000 | 8.186 | 544.53 | 48.37 | 547.63 | 5.238 |
| 104,856 | 100 | 120.002 | 8.186 | 669.78 | 84.35 | 1,175.41 | 0.039 |
| 314,568 | 1 | 3.600 | 25.298 | 1,627.36 | 42.56 | 642.89 | 27.395 |
| 314,568 | 10 | 36.000 | 25.298 | 1,647.68 | 55.21 | 906.17 | 24.898 |

The key result is structural. Coordinates scale in typed buffers and add little
serialization CPU as the structure count grows. Topology is still JSON metadata:
at 314k atoms it is 25.3 MiB and the per-atom serialization costs 1.63 s even for
one structure. The next data-plane optimization should therefore dictionary-
encode or type topology columns. Changing `view.molsys` away from
`molsysmt.MolSys` would move the scientific authority without fixing this wire
representation.

## Real Mol* browser results

`first visible` waits for non-empty Mol* geometry, not merely state-tree commit.
Frame and representation times include a two-`requestAnimationFrame`
presentation barrier. The benchmark records the target indices and separates
first visits to a structure from revisits; it does not assume that the first
requested index is always the slowest.

| Atoms | Structures | First visible | Slowest observed switch | Later-sample median (legacy mixed set) | Representation visible |
|---:|---:|---:|---:|---:|---:|
| 2,882 | 1 | 2.04-2.37 s | n/a | n/a | diagnostic only |
| 2,882 | 10 | 1.09-2.14 s | 1.25-1.36 s | 0.35-0.40 s | diagnostic only |
| 2,882 | 100 | 0.98 s | diagnostic only | about 0.37 s | diagnostic only |
| 26,214 | 1 | 4.45 s | n/a | n/a | 0.41 s |
| 26,214 | 10 | 3.99 s | 1.13 s | 0.55 s | 0.58 s |
| 26,214 | 100 | 3.87 s | 1.09 s | 0.52 s | 0.55 s |
| 104,856 | 1 | 14.50 s | n/a | n/a | 1.34 s |
| 104,856 | 10 | 10.80-15.23 s | 1.24-5.58 s | about 0.57 s | 0.56-0.71 s |
| 104,856 | 100 | 10.80 s | 4.76 s | about 0.55 s | 0.71 s |
| 314,568 | 1 | 32.74 s | n/a | n/a | 11.58 s |
| 314,568 | 10 | 31.28-31.45 s | 13.02-13.29 s | 0.78-0.82 s | 1.51-1.60 s |

The original full-matrix run retained the ordered samples but summarized all
later targets together; that column can include both first visits and revisits.
The durable benchmark now emits the target indices plus separate unvisited and
revisited medians. The repeated small/10 anchor below is the first result under
that stricter classifier.

The slow unvisited-structure cases are not transport or presentation overhead.
At the 314k/10 anchor, almost all the worst observed 13.0 s was inside Mol*'s
state-tree update and only about 12 ms was the presentation barrier. Mol* creates
trajectory models eagerly but computes dynamic model/structure and
representation data lazily. The cost is variable rather than a deterministic
"first click" tax. Across two repeated small/10 anchors, unvisited targets
ranged from 154 to 1,087 ms. The final classified run reported a 416.5 ms
unvisited median, 1,067 ms maximum and 416.8 ms revisit median.
Prewarming every structure is not adopted: it would transfer work to startup and
can multiply memory. Profile-guided selective prewarming or caching needs an A/B
of startup, unvisited visits, revisits and peak memory before it can become
production policy.

### Browser memory

The benchmark samples Chrome's full process tree from `/proc`, in addition to
`performance.memory`:

| Case | Peak process RSS | Peak renderer RSS | Peak GPU-process RSS | After page close |
|---|---:|---:|---:|---:|
| 104,856 x 10 | 2,693 MiB | 1,882 MiB | 439 MiB | 597 MiB, renderer gone |
| 314,568 x 10 | 5,668 MiB | 4,786 MiB | 508 MiB | 602 MiB, renderer gone |

Closing the page releases the scale-proportional renderer process. The peak is
nevertheless the principal 300k-atom limitation. SwiftShader process RSS is not
hardware VRAM and no hardware-GPU claim is made.

## Endpoint and Qt transport

The endpoint-isolation benchmark now accepts the same real fixtures. With the
314,568-atom case and a canvas-popup transfer deliberately left pending, host
projection latency was 0.0088 ms against the predeclared 100 ms threshold.

Qt still materializes one contiguous blob. Real representative payloads confirm
the 2x transient:

| Case | Payload | Traced peak |
|---|---:|---:|
| 104,856 atoms x 100 | 120 MiB | 240 MiB |
| 314,568 atoms x 10 | 36 MiB | 72 MiB |

Preallocating a `bytearray` does not help these cases because coordinates are
already one dominant buffer. The existing join remains acceptable below the
documented coordinate warning, but Qt near that budget requires a lower-copy
delivery design rather than a different Python join loop.

## Scene-history memory and hardening

The original snapshot store retained Python object graphs. At 100k atoms with a
literal whole color overlay, 25 checkpoints occupied 42.68 MB serialized but
retained about 212.0 MiB RSS; recording all 25 took about 2.55 s.

Phase 8 changes the internal representation to deterministic compact JSON bytes
and adds a 64 MiB combined undo/redo budget. Oldest checkpoints are evicted with
an observable `RuntimeWarning`; the current scene and newest available
checkpoint are preserved. On the same literal-overlay case, retained history RSS
dropped to 52.66 MiB (75% lower) and recording all 25 took 3.14 s. The operation
remains expensive because
`export_state()` still serializes a 100k-entry literal map on every checkpoint;
coalescing remains mandatory and structural sharing is the longer-term answer.

The byte-budget guard was mutation-tested: replacing `_enforce_byte_limit()`
with a no-op makes
`test_history_byte_budget_discards_oldest_checkpoints_observably` fail for a
missing warning; restoring it makes the test pass.

## Startup and artifact

Five comparable prewarmed processes measured import at 59-61 ms, first view at
1.145-1.160 s and warm views at about 2 ms. Array-native load preparation was
47-48 ms; direct JSON fallback remained 1.434-1.463 s. These are within the
Phase 0 median/MAD thresholds and improve the comparable first-view result from
1.277 s.

A built wheel is 2.01 MiB compressed and 8.17 MiB installed; `viewer.js` is
6.41 MiB and dominates. Five truly cold imports from the installed artifact
measured 62-65 ms and first view 1.673-1.696 s. That first-view number is not
compared to the prewarmed Phase 0 case as if they were identical experiments.

## Decisions and follow-ups

1. Keep `molsysmt.MolSys` as the Python scientific authority.
2. Preserve the array-native coordinate plane; optimize topology metadata next.
3. Do not globally prewarm structure representations. Profile and A/B any
   selective cache against startup and peak memory.
4. Keep endpoint-scoped transfer; the host remains responsive at 314k atoms.
5. Treat SwiftShader 300k rendering peak and cold first-visit latency as the
   principal scale limitations. Hardware-GPU validation remains a separate
   release environment task.
6. Keep snapshot correctness, compact byte storage and the byte budget for 1.0;
   structural sharing or command deltas are post-1.0 candidates.
