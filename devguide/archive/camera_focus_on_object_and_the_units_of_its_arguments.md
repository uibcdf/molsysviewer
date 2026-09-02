---
summary: camera.focus_on_object raises DimensionalityError on shapes, with its own default argument
issue: uibcdf/molsysviewer#69
status: resolved
opened: 2026-09-02
closed: 2026-09-02
severity: high
verification: reproduced
area: [camera, units, api]
guard: tests/test_zoom.py::test_focus_on_object_agrees_with_the_object_s_own_focus
normative: devguide/digestion_and_dependencies.md
blocked_by: []
supersedes: []
---

# One argument name, three readings of what it meant

**Reported:** 2026-09-02, while auditing the quantity digesters for #33. The audit was
meant to be a consolidation; it found a public method that could not run.

## 1. What

```python
view.shapes.add("sphere", center=..., radius=..., tag="s1")
view.camera.focus_on_object("s1", kind="shape")
```

```
DimensionalityError: Cannot convert from 'nanometer' to 'dimensionless'
```

With the method's **own default**. Passing `extra_radius=0.5` or `"0.5 nanometers"` failed
the same way. The method was unusable for shapes and measurements.

## 2. How

Three layers disagreed about `extra_radius`:

| | contract | unit |
| --- | --- | --- |
| `digest_extra_radius` | quantity | bare numbers read as **angstroms** |
| `camera.focus_on_object` docstring | number | said **nm** |
| `ShapeLayer.focus` / `MeasurementLayer.focus` | plain `float` | added to `radius_nm`, so **nm** |

`focus_on_object` is digested, so its argument arrived as a standardized quantity. It then
handed that quantity to `obj.focus(...)`, which is not digested and did
`float(extra_radius)` — and `float()` of a dimensional quantity raises.

`duration_ms` had the identical shape one layer down: digested into a time quantity, then
`int(duration_ms)` in the same undigested methods.

## 3. Why it matters beyond the crash

The crash was the lucky half. On the paths that did not raise, the same argument name
carried a silent factor of ten: a bare `0.5` digested to 0.5 Å = 0.05 nm, while
`ShapeLayer.focus(0.5)` meant 0.5 nm. That is exactly the failure the units policy is
written about, in our own code, with the documentation asserting a third answer.

The digesters were worse than undeclared. `digest_extra_radius` and `digest_min_radius`
accepted a quantity of **any** dimensionality — seconds were standardized to picoseconds —
turned the string `"4.0"` into **four radians**, because PyUnitWizard reads a bare numeric
string as dimensionless, and returned a non-numeric string such as `"hola"` unchanged.

## 4. What was refuted

**That this was a naming question.** The first reading was that `duration_ms` should be
`duration`, and it should — but the codebase already agreed: `zoom`, `focus_selection`,
`focus_region` and `selections.focus` had carried `duration` with `duration_ms` as a
backward-compatible alias for some time. Four call sites had simply been left behind. The
defect was not a missing decision; it was an unfinished migration.

**That the fix was to loosen the digesters.** The tempting repair for the crash is to make
`float()` tolerant. That keeps three readings of one argument and hides the factor of ten.

## 5. Resolution

`extra_radius` and `min_radius` are lengths and now say so: both digesters go through
`digest_length_quantity`, keeping `None`. Bare numbers, wrong dimensionalities, bare
numeric strings and garbage are all refused with a message naming the unit to add.

The four call sites left behind finish the `duration_ms` → `duration` migration, matching
the established pattern exactly: `duration: Any = "250 ms"` with `duration_ms` kept as an
overriding alias. `ShapeLayer.focus`, `MeasurementLayer.focus`, `camera.focus_on_object`
and `camera.set_snapshot`. The movie keyframe API keeps plain milliseconds, deliberately
and as documented in its digester: those values are serialized to JSON, where a quantity
cannot travel.

Both undigested `focus` methods now convert through `quantity_value_in_unit`, which accepts
a plain number or a quantity, so calling them directly still works.

Two tests passed bare numbers and were updated to state the unit they had always meant —
angstroms on the digested path, nanometres on the undigested one. That difference is the
defect, written down.

Guards: `test_focus_on_object_agrees_with_the_object_s_own_focus` asserts the two paths
produce the same message, which is how to state "these agree" without restating the
arithmetic; `test_a_camera_padding_without_units_is_refused` pins the four refusals. Both
mutation-verified.
