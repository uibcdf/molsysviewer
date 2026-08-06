# Startup baseline — July 2026

## Why this had to be measured

Every startup figure in the devguide measured **Numba JIT compilation**: the
"3–5 second freeze" that
[`../archive/standalone_performance_and_depythonization.md`](../archive/standalone_performance_and_depythonization.md)
was written to solve, and that
[`../standalone_v2_evolution_plan.md`](../standalone_v2_evolution_plan.md) used
as the main argument for the Tauri+WASM target.

**MolSysMT was rewritten in Rust for 1.0 and no longer uses Numba.** Those
numbers do not describe a slower version of today — they describe a mechanism
that no longer exists. Retiring them left the project with *no* idea what
startup costs, while an architecture decision still leaned on the old figure.

## Command

```bash
python devtools/benchmarks/startup_baseline.py
python devtools/benchmarks/startup_baseline.py --case dialanine --repeats 5
```

## Measurements (2026-07-31, linux, `pentalanine`, 62 atoms × 5,000 structures)

| stage | cost | kind |
|---|---:|---|
| `import molsysviewer` | 68 ms | one-time |
| `import molsysmt` | 407 ms | one-time, **MolSysMT** |
| `msm.convert(file)` | 4,694 ms | per file, **MolSysMT** |
| `MolSysView()` first | 1,334 ms | one-time (lazy imports) |
| `MolSysView()` warm | **3 ms** | per viewer |
| `view.load(molsys)` | 2,619 ms | **per load — the one that scales** |
| | | |
| MolSysViewer's share | 3,953 ms | |
| MolSysMT's share | 5,100 ms | |
| **first canvas, total** | **9,053 ms** | |

## What the split actually says

**The empty viewer is not slow.** 1,334 ms on the first construction and **3 ms**
on every one after it. That is the lazy-import chain being paid once, exactly as
the lazy public package intends — the cost is deferred, not removed, and it
lands on whoever constructs the first viewer. It is not a per-viewer cost and
must not be quoted as one.

**Most of the wall clock is upstream.** 5.1 s of the 9.1 s is MolSysMT reading a
5,000-structure trajectory. Reporting a single "startup" number hid that and made
the viewer look responsible for work it does not do.

**The per-load cost is the only part that scales**, and it is ours.

## The defect this surfaced, and the one it did not

`_serialize_molsys_payload` called `viewer_json.to_dict()`, which defaults to
`copy=True` and deep-copies the entire nested structure — ~930,000 floats in
Python lists for this case. The copy protected an object that is a fresh
conversion, local to `load_from_molsysmt`, read once and discarded, while
everything built from it is new (`_column` and `_normalize_bonds` go through
`np.asarray(...).tolist()`, `_extract_structures` builds new dicts). Changed to
`to_dict(copy=False)`.

Measured A/B in one process, three repeats each: **3,894 ms → 2,662 ms, a
1,232 ms saving, 32% of the load.**

> A caution about how that number was obtained. The first estimate was **2,819 ms**,
> from monkeypatching `ViewerJSON.to_dict` globally. That was wrong: it silenced
> *every* caller, not the one being changed, and so measured two defects at once.
> The honest figure came from an A/B of the real edit. A benchmark that patches a
> shared method measures the patch, not the change.

The second half was **upstream and larger**: `MolSys → ViewerJSON` made two more
redundant `to_dict()` deep copies of freshly built local objects
(`molsysmt/form/molsysmt_MolSys/to_molsysmt_ViewerJSON.py`). Reported upstream,
**fixed the same day** in `b63a2f6c5`, with an aliasing test and the mutation
check: restoring `copy=True` keeps the correctness test green and regresses the
time, which is what proves the copy was redundant rather than load-bearing.
MolSysMT measured **1.67 s → 0.32 s** on this case.

> **A methodological warning, recorded because it produced a wrong retraction.**
> This document first cited that upstream cost as "~93% of 5 s", taken from
> cProfile. **That figure is profiler overhead**: 1.35M `deepcopy` calls are
> cheap to run and very expensive to instrument, so cProfile inflated ~1.7 s of
> real work into ~5 s. On noticing, an A/B was run against what was believed to
> be the unfixed upstream — and it showed only 20 ms, prompting a retraction of
> the whole finding. **That retraction was also wrong**: the upstream fix had
> already landed in the working tree, so both arms of the A/B were running
> `copy=False` and the 20 ms was noise.
>
> Two lessons, both cheap to apply. **Never quote a cProfile duration as a wall
> time** when the hot path is millions of tiny calls — profile to find *where*,
> then time unprofiled to find *how much*. And **pin the revision of a sibling
> repository before an A/B against it**; a working tree someone else is editing
> is not a control.

## After both fixes (2026-07-31, same machine and case)

| stage | before | after |
|---|---:|---:|
| `view.load(molsys)` | 2,619 ms | **1,434 ms** |
| MolSysViewer's share | 3,953 ms | 2,729 ms |
| MolSysMT's share | 5,100 ms | 4,949 ms |
| **first canvas, total** | **9,053 ms** | **7,678 ms** |

`msm.convert(file)` — reading the trajectory into a `MolSys` — is now **4,548 ms
and by far the dominant cost**, untouched by either fix. Whatever is optimized
next in this path, that is where the time is.

## Caveats that must travel with these numbers

- **This is the JSON fallback path.** With no frontend there is no capability
  negotiation, so the array-native data plane is not exercised. It is the honest
  worst case, and it is what a cold cell pays before negotiation completes, but
  it is not what a negotiated binary session pays. The array-native serializer
  measured **44.8 ms** for this same 5,000×62 case (see
  [`trajectory_transport_baseline_2026_07.md`](trajectory_transport_baseline_2026_07.md)) —
  which is the point: a 45 ms transport sat inside a multi-second load path, and
  nobody had measured the path.
- **Qt WebEngine initialization and browser-side decode are not here.** They need
  a real window. Do not extrapolate this to standalone launch time.
- One machine, one case. Two axes matter independently: atom count and structure
  count. This case is small in atoms and large in structures.
