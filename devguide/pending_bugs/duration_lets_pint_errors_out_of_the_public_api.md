---
summary: digest_duration lets pint's UndefinedUnitError out of twelve public callables.
issue: uibcdf/molsysviewer#86
status: open
opened: 2026-09-06
closed:
severity: low
verification: reproduced
area: [argdigest, units]
guard:
normative:
blocked_by: []
supersedes: []
---

# An unparseable duration escapes as pint's error, not as ours

**Reported:** 2026-09-06, auditing the magnitude families `uibcdf/molsysviewer#33` named
and never reached. That proposal was archived the same day; this is the part of its scope
that turned out to be live.

## What happens

```
>>> digest_duration("banana")
'banana'
>>> quantity_value_in_unit("banana", "ms")
UndefinedUnitError: 'banana' is not defined in the unit registry
```

The digester passes it through, and it fails a layer later on the way to the frontend. So
`view.focus_region(region, duration="250 milisegundos")` raises **pint's** exception out of
a MolSysViewer call, naming neither the argument nor the caller.

Every length argument in this package raises `ArgumentError` naming both. `#33` recorded
that as a deliberate divergence from MolSysMT, who do let `UndefinedUnitError` out of
`puw.parse.parse`. We let it out too, one layer further down.

`duration` is a keyword of twelve public callables: `focus_region`, `focus_selection`,
`focus_on_object`, `zoom` and `set_snapshot` on `CameraManager` and `SceneMixin`, and
`focus` on `Region`, `Selection`, `ActiveSelection` and `Whole`.

## Severity is low, and what is *not* wrong

The same twelve take `duration_ms` as a backward-compatible alias, and the two digesters
disagree on a bare number:

| input | `digest_duration` | `digest_duration_ms` |
| --- | --- | --- |
| `"250 ms"` | `2.5e+11 picosecond` | `2.5e+11 picosecond` |
| `5` | **`5`** — no unit | `5e+09 picosecond` |
| `"banana"` | **`"banana"`** | `"banana"` |

The bare number is a **policy gap, not a defect**. `quantity_value_in_unit` accepts plain
numbers and reads them as the unit asked for, so `duration=5` and `duration_ms=5` both
arrive as 5 ms. Recorded because the table looks alarming and the behaviour is not, and
somebody will otherwise "fix" a row that is already right.

Low, then: a wrong duration still fails, loudly and immediately. What it fails with is the
wrong exception from the wrong library.

## The half that is not a patch

`digest_length_quantity` is `[L]` only. `force` hand-rolls its own check against
`{'[L]':1, '[M]':1, '[T]':-2, '[mol]':-1}`, and a time boundary does not exist at all.
This is not a migration somebody forgot; it is a piece that was never built.

Patching `duration` alone leaves the next magnitude to hand-roll the same
`parse -> is_quantity -> check -> standardize -> raise` sequence and drift the same way,
which is the drift `#33` set out to stop. The shape worth considering is a boundary taking
the dimensionality, with `digest_length_quantity` becoming its `[L]` case.

## Acceptance

1. An unparseable duration raises `ArgumentError` naming the argument and the caller, from
   the digester, rather than `UndefinedUnitError` from pint.
2. `duration` and `duration_ms` agree on every input they share, or the disagreement is
   stated where a reader meets it.
3. Mutation-verified: a digester that accepts an unparseable string fails the guard.
4. Whatever `force` gets is the same instrument, not a second hand-rolled sequence.

## Audited with it, and out of scope

None of the other hand-rolling digesters is a missed migration. Six have no public callable
declaring the name — `angles`, `angle_threshold`, `bond_length`, `distance_threshold`,
`threshold`, `value`. `coordinates`, `vectors`, `values` and `point` are the array and
union family `#33` itself refuted. `width` carries three caller-decided meanings — CSS,
pixels, physical length — and its `[L]` branch accepts bare numbers, so consolidating it
would change behaviour rather than share an implementation.

Evidence in
[`../archive/consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md`](../archive/consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md).
