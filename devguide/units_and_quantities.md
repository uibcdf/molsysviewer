# Units and Quantities Policy

Authoritative policy for how MolSysViewer handles physical magnitudes (lengths,
positions, radii, thicknesses, …). Read this before adding or touching any public
method or argument digester that takes a physical magnitude.

Related: [digestion_and_dependencies.md](digestion_and_dependencies.md),
[guiding_principles.md](guiding_principles.md), and the root `PYUNITWIZARD_GUIDE.md`.

## The policy (non-negotiable)

**Physical magnitudes must be PyUnitWizard quantities. Bare numbers are
rejected.** There is **no** "interpret a naked number" policy — not "assume nm",
not "assume angstroms", not a configurable default. A magnitude without units is
an error, surfaced immediately with a teaching message.

Accepted at the public API for a length argument:

```python
view.shapes.add_sphere(center="[1, 2, 3] angstroms", radius="3.5 angstroms")
view.shapes.add_sphere(center=puw.quantity([1, 2, 3], "nm"), radius=puw.quantity(0.35, "nm"))
```

Rejected (raises `ArgumentError`):

```python
view.shapes.add_sphere(center=[1, 2, 3], radius=3.5)   # bare numbers → error
```

## Why (the friction we fixed)

The internal suite unit is **nm** (MolSysMT convention); Mol\* and the wire are
**angstroms**. The old boundary helper `to_wire_angstroms` silently multiplied
bare numbers by 10 ("assume nm"). A user thinking in angstroms who wrote
`radius=3.5` got a 35 Å sphere — a silent ×10 scale error that produced invisible
or giant objects and phantom bug reports. Rejecting bare numbers turns that
silent footgun into an immediate, self-explaining error.

This is **the suite convention**, not a MolSysViewer invention: `molsysmt`'s
`digest_distance`/`digest_coordinates` reject bare numbers the same way, and
`topomt` always feeds the viewer `puw.quantity(...)` and converts explicitly.
MolSysViewer was the outlier; it now conforms.

## How to write it (developer recipe)

### 1. Validate at the public surface with argdigest

A public method that owns a real named signature carries `@digest()`; every
physical-magnitude argument gets a **length digester** in
`molsysviewer/_private/argdigest/argument/<name>.py`:

```python
from .._quantity import digest_length_quantity

def digest_<name>(<name>, caller=None):
    if <name> is None:          # only if the argument is optional
        return None
    return digest_length_quantity(<name>, "<name>", caller=caller)
```

`digest_length_quantity` (in `_private/argdigest/_quantity.py`) delegates the
logic to `puw.ensure_quantity(value, dimensionality={'[L]': 1})` — parse strings,
accept any recognized quantity form, reject bare numbers, require `[L]`
dimensionality, standardize to nm — and re-raises MolSysViewer's own
`ArgumentError` (a `ValueError`) with the argument name and a teaching message.
The digester returns a **standardized nm quantity**.

`ensure_quantity()` already recognizes a quantity in the configured canonical
unit through PyUnitWizard's cheap metadata path. Do not add a `has_unit()` guard
around every use of this helper. An explicit canonical branch belongs only in a
measured hot path that also performs viewer-owned shape or dtype normalization.

Do **not** hand-roll `parse → is_quantity → check → standardize → raise` in each
digester; that is exactly what `puw.ensure_quantity` centralizes.

### 2. Convert to the wire unit explicitly, in the function body

After digestion the value is an nm quantity. Mol\* wants angstroms, so convert
**explicitly and locally** (the topomt pattern) where you build the payload:

```python
options["radius"] = puw.get_value(radius, to_unit="angstroms", value_type=float)
options["center"] = puw.get_value(center, to_unit="angstroms", value_type=list, dtype=float)
```

Use `value_type` / `dtype` (float, list, `np.ndarray`) so you never re-wrap with
`float(...)` or `np.asarray(...)` by hand. There is **no** shared
`to_wire_angstroms` helper any more — it was deleted; do not reintroduce a module
that "assumes nm".

### 3. Respect the `skip_digestion` contract

- Public / surface methods: `skip_digestion=False` (default) → they validate.
- Internal calls to a deeper helper pass `skip_digestion=True` — the arguments
  are already validated/standardized, so re-digesting is wasted work. This mirrors
  molsysmt (public functions default False; internal calls pass True explicitly).
- Full-signature public methods (e.g. `add_sphere`) carry `@digest()` and
  delegate inward with `skip_digestion=True`.
- Thin `*args/**kwargs` forwarders are **not** decorated; they delegate *without*
  forcing skip, so the deeper helper (which owns the real signature + `@digest()`)
  validates on the public path.

## Hard-won lessons

- **Turning on argdigest digests *all* arguments, not just the one you care
  about.** When you make a public method validate, non-length arguments also flow
  through their digesters. `color`, `alpha` and `tag` therefore had to become
  batch-aware (accept a single value **or** a per-object list). Budget for the
  whole argument set.
- **A strict digester and its body conversion are coupled.** Once a digester
  standardizes an argument to a quantity, any body code that consumed it as a raw
  number (`float(center[0])`, iterating for `.tolist()`) breaks — it must first
  `puw.get_value(..., to_unit="angstroms")`. Change both together.
- **Directions are not lengths.** Arguments like `normals`, unit `vectors`, and
  `*_scale` factors are dimensionless — do **not** give them `[L]` digesters. The
  reliable signal for "this is a length" is: it used to be converted to angstroms
  for the wire.
- **The suite standard is nm, the wire is angstroms — so round-trips lose
  float precision** (angstroms → nm on standardize → angstroms on the wire).
  Tests that assert exact coordinate values should use `pytest.approx`.
- **Error type matters.** `puw.ensure_quantity` raises pyunitwizard's
  `ArgumentError`, which is **not** a `ValueError`. MolSysViewer digesters must
  re-raise the viewer's own `ArgumentError` (a `ValueError`) so
  `pytest.raises(ValueError)` and the local error contract keep working — that
  translation is what `digest_length_quantity` does.

## Upstream helpers (pyunitwizard)

Three helpers were added to PyUnitWizard to support this policy and de-duplicate
the pattern across the whole suite:

- `puw.ensure_quantity(value, dimensionality=None, to_unit=None, standardized=True,
  parser=None, caller=None)` — parse/validate/standardize a quantity; reject bare.
- `puw.has_unit(value, unit)` — return `True`, `False`, or `None` for a cheap
  exact-unit query without extracting the magnitude. `False` does not prove
  dimensional compatibility; `False` and `None` return to general validation at
  an untrusted boundary.
- `puw.get_value(..., value_type=float|int)` — extract a Python scalar (with a
  clear error for non-scalar input), closing the `float(get_value(...))` idiom.

The classification and migration of older quantity digesters is tracked in
[`pending_proposals/consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md`](pending_proposals/consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md).
