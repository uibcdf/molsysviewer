---
summary: digest_duration lets pint's UndefinedUnitError out of twelve public callables.
issue: uibcdf/molsysviewer#86
status: resolved
opened: 2026-09-06
closed: 2026-09-06
severity: low
verification: reproduced
area: [argdigest, units]
guard: tests/test_time_and_force_digesters.py
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

## Resolved 2026-09-06

### Two more leaks, found while fixing the one that was filed

`"banana"` was not alone. `"250"` parsed as **250 radians** and died on
`DimensionalityError` on its way to the frontend, and `True` was accepted by `duration` as
**one millisecond** while `duration_ms` threw PyUnitWizard's `NotImplementedMethodError`.
Three foreign exceptions and a boolean hole, from an issue filed about one.

### What changed

`digest_length_quantity` became the `[L]` case of `digest_quantity`, which takes the
dimensionality. `duration` and `duration_ms` are `[T]` through it, and `force` is
`[L][M][T]^-2[mol]^-1` through it. Nothing hand-rolls
`is_quantity -> check -> standardize -> raise` any more, and every refusal is
`ArgumentError` naming the argument and the caller, with the original exception kept as
`__cause__`.

| input | `duration` before | `duration` after | `duration_ms` before | `duration_ms` after |
| --- | --- | --- | --- | --- |
| `"250 ms"` | 2.5e+11 ps | unchanged | 2.5e+11 ps | unchanged |
| `5` | `5`, bare | **`ArgumentError`** | 5e+09 ps | unchanged |
| `True` | `True` → 1 ms | **`ArgumentError`** | `NotImplementedMethodError` | **`ArgumentError`** |
| `"250"` | 250 **radian** | **`ArgumentError`** | 250 **radian** | **`ArgumentError`** |
| `"banana"` | `UndefinedUnitError` | **`ArgumentError`** | `UndefinedUnitError` | **`ArgumentError`** |

### The one deliberate behaviour change

`duration=5` used to reach the frontend as 5 ms, by way of `quantity_value_in_unit`
reading bare numbers as the unit asked for. It now raises. That is a **tightening of a
public argument**, chosen rather than inherited: `duration=2` cannot be told from two
seconds by anyone reading the call, which is the silent scale error the units policy
exists to prevent, and the same policy already refuses a bare number for every length.

The refusal is actionable — the message names both `"250 ms"` and `duration_ms=250` — and
`duration_ms` still takes a bare number, because its name carries the unit. Nothing in the
repository, the tests, or the documentation passed a bare `duration`; every call site
already wrote the units. `docs/content/user/introduction/units.md` now says so where a
reader meets it.

So the two names disagree in exactly one place, and that is the answer to acceptance
criterion 2: not that they agree everywhere, but that where they differ, one of them names
its unit and the other does not.

### The bare-number row that was already right

The report warned that the `5` row looked alarming and was not a defect, because both
paths arrived as 5 ms. That held: the change is not a bug fix, it is a policy being
applied where it had been skipped.

### Verification

`tests/test_time_and_force_digesters.py`, 46 assertions. The type of every refusal is
asserted **exactly** — `pytest.raises(ArgumentError)` alone would not pin this, because
`ArgumentError` is a `ValueError` and so is pint's `UndefinedUnitError`, so a subclass
check passes while the caller still meets pint.

Six mutations, each caught:

| mutation | test that falls |
| --- | --- |
| the boundary stops translating foreign exceptions | `test_one_boundary_serves_every_magnitude` |
| `duration` passes strings through again | `test_the_two_names_agree_wherever_they_overlap` |
| `duration` accepts bare numbers | `test_the_refusal_of_a_bare_number_points_at_the_name_that_accepts_one` |
| `duration_ms` stops treating `bool` as an error | `test_a_duration_that_is_not_a_time_raises_this_packages_error` |
| `force` loses the `show` carve-out | `test_force_is_a_boolean_where_show_asks_it` |
| the movie timeline loses its plain milliseconds | `test_the_movie_timeline_refuses_what_it_cannot_serialise` |

Full suite: 2052 passed, 13 skipped.
