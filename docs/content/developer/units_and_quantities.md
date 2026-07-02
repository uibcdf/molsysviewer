# Units and quantities

MolSysViewer works internally in **nanometers** (the MolSysSuite convention),
while Mol\* and the wire format use **angstroms**. To keep that boundary safe,
physical magnitudes are handled through PyUnitWizard quantities — **never bare
numbers**.

## The rule

Any public argument that is a physical magnitude (length, position, radius,
thickness, …) **must** be a quantity. Bare numbers are rejected with a clear
error. There is no "assume nm" or "assume angstroms" fallback.

```python
# ✅ correct — explicit units
view.shapes.add_sphere(center="[1, 2, 3] angstroms", radius="3.5 angstroms")
view.shapes.add_sphere(center=puw.quantity([1, 2, 3], "nm"), radius=puw.quantity(0.35, "nm"))

# ❌ rejected — bare numbers raise ArgumentError
view.shapes.add_sphere(center=[1, 2, 3], radius=3.5)
```

A unit-bearing **string** (`"3.5 angstroms"`, `"0.35 nm"`) is a quantity as far
as PyUnitWizard is concerned, so it is the most convenient explicit form for
interactive use — barely more typing than a bare number.

Rationale: a naked `radius=3.5` meant as angstroms used to be silently read as
`3.5 nm` (= 35 Å), producing giant, misplaced, or invisible shapes. Requiring
units makes the mistake impossible.

## Writing a public method that takes a magnitude

1. **Validate at the public surface.** Decorate the method that owns the real
   named signature with `@digest()`. Each magnitude argument has a digester in
   `molsysviewer/_private/arg_digestion/argument/<name>.py`:

   ```python
   from .._quantity import digest_length_quantity

   def digest_<name>(<name>, caller=None):
       if <name> is None:        # only if optional
           return None
       return digest_length_quantity(<name>, "<name>", caller=caller)
   ```

   `digest_length_quantity` requires a `[L]` quantity, rejects bare numbers, and
   returns a standardized nm quantity. Default values in the signature may be
   unit strings (e.g. `radius="1.0 nm"`).

2. **Convert to angstroms explicitly in the body**, where you build the payload:

   ```python
   options["radius"] = puw.get_value(radius, to_unit="angstroms", value_type=float)
   options["center"] = puw.get_value(center, to_unit="angstroms", value_type=list, dtype=float)
   ```

   Use `value_type` (`float`, `list`, `np.ndarray`) and `dtype` so you don't
   re-wrap the result by hand.

3. **`skip_digestion`**: public methods default to `skip_digestion=False` (they
   validate). Internal calls to deeper helpers pass `skip_digestion=True` because
   the arguments are already validated.

## Gotchas

- Turning on `@digest()` validates **every** argument of the method, not only the
  magnitudes — make sure each argument's digester accepts the forms your API
  supports (for shapes, `color`/`alpha`/`tag` accept a single value or a batch
  list).
- Directions (`normals`, unit `vectors`) and scale factors (`*_scale`) are
  **dimensionless** — they are not lengths and must not require `[L]` units.
- Standardizing to nm and converting back to angstroms is a round-trip; assert
  coordinate values with `pytest.approx` in tests.

See also the developer guide `devguide/units_and_quantities.md` for the full
policy and the reasoning behind it.
