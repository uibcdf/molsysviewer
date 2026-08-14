# Pre-1.0 rework baseline - August 2026

## Purpose and status

This document is the Phase 0b measurement record for
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md).

**Status:** measured on 2026-08-02. Required automated gates are green. The
real-window Qt check and direct visual inspection of the generated static HTML
artifact remain explicitly unavailable/uncovered; neither is counted as a pass.

The baseline has two jobs:

1. prove that the starting point is green on every required surface;
2. fix the comparison method before later architecture work produces numbers.

An unavailable browser, display or GPU is reported as unavailable. It is never
counted as a pass. Times from profilers are not wall-clock evidence.

## Environment to record

Every result records:

- MolSysViewer `HEAD` and dirty-worktree exclusions;
- Python, Node, npm, Chrome/Chromium, Playwright and Mol* versions;
- operating system, logical processors and total memory;
- browser executable and WebGL renderer;
- command wall time and maximum resident set size where the host exposes them.

## Required green gates

The following gates permit zero failures:

```bash
pytest --receptor=llm -n 12 tests/
cd molsysviewer/js
npm run test:js
npx tsc --noEmit
npm run build:runtime
npm run test:perf
npm run test:e2e
```

The three documented Python skips that require optional imageio, a real X11
display and an explicitly enabled Qt GPU test are recorded separately. The E2E
runner itself must not skip browser or WebGL initialization.

## Predeclared performance rules

### Existing message-path budgets

The budgets already encoded in the performance harness remain authoritative:

| Gate | Historical comparison point | Hard failure threshold |
|---|---:|---:|
| unknown message, 95,000 atoms | 0.3-0.4 ms | 5 ms |
| `hide_region`, 95,000 atoms | about 0.1 ms | 20 ms |
| dynamic-region request gate | about 0.0008 ms/frame | 0.05 ms/frame |
| hierarchy nodes, 95,000 atoms | 9,500 | 9,500 |

A later value is considered a material regression before the hard ceiling when
it is both more than 20% slower than this Phase 0b baseline and outside the
Phase 0b observed run-to-run range. Functional correctness and the hard ceiling
still win over statistical interpretation.

### Cold startup and transport

Cold-process timing cases are run five times. The baseline is the median and its
noise band is the median absolute deviation (MAD). A later result is a material
regression when it exceeds:

```text
baseline median + max(20% of the median, 3 * MAD)
```

This rule is applied independently to MolSysViewer-owned stages. MolSysMT
conversion is recorded but not charged to MolSysViewer; an upstream regression
is reported to MolSysMT instead of being hidden in a viewer total.

### Memory

Peak and retained RSS are separate metrics. A later result is material when it
exceeds the Phase 0b value by both 15% and 64 MiB. A lower peak does not excuse
retained growth, and `ru_maxrss` is never used to claim that memory was freed.

### Suite duration

Suite wall time and maximum RSS are diagnostic baselines, not release budgets.
A change above 25% wall time or above both 15% and 64 MiB RSS requires
investigation and an explanation; it does not fail solely from one noisy run.

## Real-surface matrix

| Surface | Required observation | Phase 0b result |
|---|---|---|
| shared-browser E2E | every suite passes against real Mol* and WebGL2 | **pass:** 28/28, no browser/WebGL skips |
| static HTML export | framing and representation replacement remain valid | **partial:** standalone-like replay and camera restoration pass; the generated HTML artifact itself was not opened and visually inspected |
| panel popup | hierarchy remains valid after a second load | **partial:** panel-only hierarchy relay passes after a load; a second-load panel-popup case is not isolated by the current suite |
| load/reload | hide/show remains valid and browser console stays clean | **pass by combined evidence:** second-load representation refs are live, scene-contract scenarios finish with no page/console errors, and the full runner stays green |
| Qt real window | framing and zoom on a real display/GPU | **unavailable:** headless Qt protocol tests pass, but this run did not provide the required real display/GPU window |

## Results

### Revision and environment

- Git baseline: `6362914c65596458774668d97a547fa372326d18` plus the
  uncommitted Phase 0 work. `sandbox/Smoke_Test.ipynb` is developer-owned and
  excluded from the phase.
- Python 3.13.14; Node 24.11.1; npm 11.11.0.
- Mol* 5.4.1; Playwright 1.57.0; TypeScript 5.9.3; esbuild 0.27.0.
- Linux 7.0.0-28-generic; 20 logical processors; 31.2 GiB RAM; 8 GiB swap.
- Chrome 149.0.7827.53; WebGL2 through ANGLE, Vulkan 1.3.0 and SwiftShader.

### Green gates

| Gate | Observed result | Wall time | Peak RSS |
|---|---:|---:|---:|
| `pytest --receptor=llm -n 12 tests/` | 1,160 passed, 3 documented skips | 84.97 s | 1,080,700 KB |
| `npm run test:js` | 262 passed | 8.45 s | 289,572 KB |
| `npx tsc --noEmit` | exit 0 | 5.41 s | 543,528 KB |
| `npm run build:runtime` | exit 0 | 0.55 s | 67,848 KB |
| `npm run test:perf` | exit 0 | 12.06 s | 289,412 KB |
| `npm run test:e2e` | 28/28 suites | 291.60 s | 666,912 KB |

The Python run inside the restricted agent sandbox first produced three
environmental failures: two Qt/Chromium subprocesses were denied by the Linux
sandbox and one fixture download had no network. The three exact tests passed
outside that sandbox, followed by the complete green run above. The restricted
failure is not counted as a product failure or as a pass.

### Existing performance gates

At 95,000 atoms, the message benchmark observed:

| Gate | Result | Hard threshold |
|---|---:|---:|
| unknown message | 0.30 ms | 5 ms |
| `hide_region` | 0.20 ms | 20 ms |
| hierarchy nodes | 9,500 | 9,500 |
| load fixture | 3,197.7 ms | diagnostic |

The dynamic-region gate observed 0.000685129 ms/frame over 1,000 messages,
against the 0.05 ms/frame hard threshold.

### Cold startup

Five independent processes loaded pentalanine with 62 atoms and 5,000
structures. Each process reported the median of five warm-view and load
operations; the table below then reports the median and MAD across the five
processes.

| Stage | Median | MAD | Ownership |
|---|---:|---:|---|
| import MolSysViewer | 58 ms | 0 ms | MolSysViewer, one-time |
| import MolSysMT | 372 ms | 7 ms | MolSysMT, one-time |
| `msm.convert(file)` | 7,736 ms | 29 ms | MolSysMT, per file |
| first `MolSysView()` | 1,277 ms | 10 ms | MolSysViewer, one-time |
| warm `MolSysView()` | 2 ms | 0 ms | MolSysViewer, per viewer |
| `view.load(molsys)` JSON fallback | 1,299 ms | 44 ms | MolSysViewer, per load |
| MolSysViewer share | 2,529 ms | 48 ms | first view plus load |
| MolSysMT share | 8,102 ms | 35 ms | import plus conversion |
| first canvas total | 10,630 ms | 38 ms | combined diagnostic |

The first conversion process was a 10,608 ms outlier. The median/MAD rule was
declared before observing it and therefore remains the comparison authority.

### Python JSON-fallback preparation

Each case was measured in a fresh worker, repeated across five independent
benchmark runs. Values are median across runs; parenthesized values are MAD.

| Case | Payload | prewarmed MolSysMT convert | ViewerJSON | hierarchy | list normalization | JSON encode | peak RSS growth | retained growth |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dialanine, 22 x 1 | 3.4 KB | 3,186 (27) ms | 1.37 (0.01) ms | 13.73 (0.15) ms | 0.26 (0.01) ms | 0.11 (0.00) ms | 354.2 (0.2) MiB | 357.2 (0.0) MiB |
| pentalanine, 62 x 100 | 0.37 MB | 3,180 (13) ms | 3.72 (0.07) ms | 14.02 (0.07) ms | 11.75 (0.42) ms | 12.74 (0.14) ms | 358.4 (0.2) MiB | 361.1 (0.1) MiB |
| pentalanine, 62 x 1,000 | 3.68 MB | 3,243 (3) ms | 22.03 (0.79) ms | 14.45 (0.23) ms | 332.72 (7.00) ms | 130.94 (1.22) ms | 393.7 (0.2) MiB | 393.5 (0.4) MiB |
| pentalanine, 62 x 5,000 | 18.37 MB | 3,496 (29) ms | 303.40 (1.78) ms | 14.54 (0.29) ms | 1,091.82 (3.91) ms | 655.09 (11.61) ms | 535.5 (0.4) MiB | 520.9 (0.2) MiB |
| villin, 4,369 x 1 | 0.58 MB | 3,222 (55) ms | 15.59 (0.10) ms | 15.83 (0.11) ms | 12.96 (0.09) ms | 12.38 (0.05) ms | 363.6 (0.1) MiB | 366.5 (0.0) MiB |

The memory figures include the process import baseline and therefore are
comparison points, not a claim that the payload alone retains that memory.

### Phase 3 direct-encoder measurement (2026-08-02)

Phase 3 removed the ViewerJSON intermediate and made portable JSON an on-demand
compatibility/export product. Wall-clock measurements used `perf_counter`, not
`cProfile`. The startup case was measured with three repetitions after one
MolSysMT conversion; the JSON memory case used three fresh worker processes.

`pentalanine`, 62 atoms x 5,000 structures:

| Live load path | Median |
|---|---:|
| register generation-bound lazy projection before frontend `ready` | 32 ms |
| negotiated array-native load | 66 ms |
| direct portable-JSON load | 1,459 ms |

The successful binary path is also guarded structurally: its complete transfer
builds portable JSON zero times. Therefore the roughly 1.4 s compatibility
cost is absent rather than merely hidden inside the binary timing.

The direct-JSON worker produced an 18,370,953-byte message. Across three fresh
processes:

| Metric | Median | Observed range |
|---|---:|---:|
| direct JSON serialization | 335.4 ms | 332.2-336.3 ms |
| JSON text encoding | 637.5 ms | 634.7-640.8 ms |
| peak RSS growth, including MolSys load | 474.2 MiB | 473.4-475.9 MiB |
| retained RSS growth, including MolSys + returned message | 456.7 MiB | 455.8-458.4 MiB |
| transient part of peak | 17.6 MiB | 17.4-17.7 MiB |

These memory figures intentionally retain the returned JSON message and loaded
MolSys; they characterize the compatibility path, not binary-transfer retained
memory. Compared with the original row above, the encoder removes ViewerJSON
and the second list-normalization stage. Dependency and host variance means the
current ranges, not a subtraction against July's run, are the acceptance
evidence.

### Chrome JSON/Mol* path

Five independent Chrome runs consumed the 18.37 MB pentalanine payload.

| Stage | Median | MAD |
|---|---:|---:|
| Node control parse | 129.49 ms | 0.16 ms |
| browser fetch as text | 166.60 ms | 2.20 ms |
| browser `JSON.parse` | 182.00 ms | 4.60 ms |
| Mol* trajectory construction | 205.80 ms | 2.10 ms |
| structure change, per-run median | 6.20 ms | 0.50 ms |
| structure change, per-run maximum | 13.40 ms | 0.70 ms |

V8 heap medians were 78.10 MiB before the load, 122.43 MiB at the sampled
Mol* peak and 98.70 MiB after load. They exclude native Mol*, WebGL and GPU
allocations.

### Real-runtime probes

- representation replacement retained one live global representation and
  observed a 0 ms empty interval in both measured swaps;
- camera authority framed the fixture in 1,723 ms and remained stable while
  representations changed;
- these probes exercise the same runtime against real Mol*, but do **not**
  substitute for opening the generated static HTML artifact or a real Qt
  window.

### Baseline repair found during execution

`RegionsPanel.setSavedSelections()` and `setCurrentSelection()` scheduled a
normal render while a continuous region-style edit was open. A Python summary
refresh could replace the active opacity slider before `pointerup`, losing the
history-coalescing end event. Both setters now use the panel's existing
external-render suppression path. The history E2E fails when that guard is
mutated back and passes after restoration.

Three other E2E files were aligned with intentional current UI behavior:
Selection and Regions now use the active-selection workflow, and Shape style
controls are opened through the collapsed `Edit` surface. No corresponding
public Python API was removed.

### Conversion-stage accounting

The startup harness measures `msm.convert(file)` at 7,736 ms median, while the
transport workers report the same named pentalanine stage near 3,496 ms. An A/B
isolated the difference:

- implicit versus explicit `structure_indices` did not explain it;
- a cold conversion after importing only MolSysMT took about 6,420 ms;
- importing `molsysviewer.loaders.load_molsysmt` before starting the conversion
  timer reduced the timed conversion to about 3,460 ms;
- timing the complete import-plus-conversion path removed the apparent gain:
  about 6,860 ms without the viewer loader versus 7,220 ms with it.

The transport benchmark therefore reports a **prewarmed conversion stage**, not
a cold MolSysMT conversion. This is a benchmark-accounting limitation in this
repository, not evidence of a MolSysMT defect. A future cross-project claim
must use the same timing boundary in both arms. Any subsequently confirmed
conversion improvement belongs in the MolSysMT devguide rather than being
hidden inside a MolSysViewer optimization claim.
