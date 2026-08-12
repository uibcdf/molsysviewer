# Attributing the ArgDigest overhead — 2026-08-12

`devguide/benchmarks/README.md` §4 reports:

| Telemetry Configuration | Mean (ms) | Overhead (ms) | Slowdown (%) |
| :--- | :---: | :---: | :---: |
| `Baseline (None)` | 21.06 | — | — |
| `ArgDigest-only` | 26.30 | +5.25 | 24.9% |

**The number is right. The conclusion drawn from it was not**, and that conclusion is
what produced the `caching_and_skip_digestion` proposal filed against ArgDigest. This
note records where the 5.25 ms actually goes.

## What was measured on the ArgDigest side

| | µs per call |
| --- | ---: |
| Undecorated call | 0.06 |
| `@arg_digest`, nothing declared — **the decorator's own plumbing** | **21.6** |
| `skip_digestion=True` fast path | 1.8 |
| `@arg_digest` + a digester that only checks | 22.3 |
| `@arg_digest` + a coercing digester, 10 atoms | 30.7 |
| `@arg_digest` + a coercing digester, 5000 atoms | **1691.7** |

The plumbing is 21.6 µs and **flat** — independent of payload size. It is 0.4% of the
reported 5.25 ms. Whatever the overhead is, it is not the decorator's machinery.

## Where it goes

One `view.regions.add(selection="atom_index < 3")` on `dialanine` dispatches **587
decorated calls** across 43 distinct callables. 434 of them are MolSysMT's
`has_attribute`:

```
 256x  molsysmt.form.molsysmt_MolSys.has_attribute
 178x  molsysmt.form.molsysmt_Topology.has_attribute
  40x  molsysmt.form.molsysmt_Structures.has_attribute
```

`molsysmt_MolSys.has_attribute` costs 65.6 µs digested and 7.5 µs with
`skip_digestion=True`. So ~58 µs × 434 ≈ **29 ms of argument digestion inside MolSysMT
for one region creation** — which more than accounts for the reported slowdown.

`digest_molecular_system` performs a real form assessment, and it runs 434 times on the
same `MolSys` object.

## Why the proposed fix was wrong

The proposal read the number as "validation is expensive in production, so bypass it in
production". Three objections, in increasing order of weight:

1. **The cost is misplaced digestion, not the cost of validating.** A predicate whose
   body is 7.5 µs is wearing a boundary-grade digester nine times its weight.
2. **Digestion transforms values, it does not only check them.** `to_numpy`,
   `convert(to_unit=...)`, form assessment — skipping them does not skip a check, it
   changes what the function receives. Production would run a different program from the
   one tested.
3. **A bypass would have hidden this.** The number would have dropped, the 434 redundant
   calls and the repeated assessment of an unchanged object would have stayed, and nobody
   would have looked again.

Point 3 is the one worth keeping: the overhead was a **symptom pointing at a real
defect**, and the proposed remedy would have removed the symptom.

Filed against MolSysMT as `devguide/pending_bugs/boundary_digestion_on_internal_predicates.md`.

## A second finding, this one on our side of the line

The 434 calls resolve to **191 distinct `(form, attribute)` pairs** — 2.3x redundancy,
removable by memoising within one operation. But 191 *distinct* attribute queries to
answer "create a region" is a question about what `regions.add` asks MolSysMT for. Even
at the undigested 7.5 µs those are ~3.3 ms, independent of ArgDigest entirely.

## Corrections owed to the benchmark page

1. §4's label `ArgDigest-only` reads as "the cost of ArgDigest". It is the cost of *how
   this codebase and MolSysMT use* ArgDigest. Worth renaming.
2. The standard deviations (2.42 baseline, 5.60 ArgDigest-only) are the same order as the
   differences being reported. With 50 iterations the means carry roughly ±1 ms; the
   table presents them to 0.01 ms.
3. `SMonitor-only` (+4.48) and `ArgDigest-only` (+5.25) are close, and ArgDigest is itself
   instrumented with SMonitor — so the two rows are not independent, which the table does
   not say.

## Reproducing

Counting the fan-out requires patching `argdigest.arg_digest` with a counter *before*
importing `molsysviewer`, so every decoration goes through it:

```python
import argdigest
from argdigest.core import decorator as _d

_real, CALLS = argdigest.arg_digest, {}

def counting(*a, **kw):
    deco = _real(*a, **kw)
    def wrap(fn):
        wrapped = deco(fn)
        def counter(*ca, **ck):
            CALLS[f"{fn.__module__}.{fn.__qualname__}"] = CALLS.get(f"{fn.__module__}.{fn.__qualname__}", 0) + 1
            return wrapped(*ca, **ck)
        counter.digestion_plan = getattr(wrapped, "digestion_plan", None)
        return counter
    return wrap

counting.map = _real.map
argdigest.arg_digest = counting
_d.arg_digest = counting

from molsysviewer.demo import demo   # must come after
```

ArgDigest is adding a runtime mode to `argdigest audit` so this stops requiring a hand
written harness.
