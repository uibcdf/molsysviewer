# Digestion and Dependencies

MolSysViewer follows the UIBCDF standards for argument validation and dependency management through **ArgDigest** and **DepDigest**.

## Argument Digestion (ArgDigest)

We use ArgDigest in **package style**. Validation and normalization live outside the public orchestration methods and are discovered from the package digestion config.

### Structure
- **Config**: `molsysviewer/_argdigest.py` defines the source of digesters.
- **Engine**: `molsysviewer/_private/argdigest/` contains the adapters and sub-packages.
- **Digesters**: `molsysviewer/_private/argdigest/argument/` contains one `.py` file per argument name (e.g., `centers.py`, `radii.py`).

### Current Status

- package-style digestion is active and broadly integrated across the public API;
- core noisy wrappers have now been hardened with explicit digesters;
- thin but real public query wrappers such as `contains(...)`,
  `is_composed_of(...)`, and `extract(...)` are also part of the hardening
  surface when they own a stable contract;
- missing-digester warnings on stable public paths are treated as integration debt;
- shape-overlay digestion is now active end to end, including strict length-unit
  validation (see below and [units_and_quantities.md](units_and_quantities.md)).

### Resolved: shape-overlay digestion is now active end to end

This was previously bypassed: the `ShapesManager.add_*` wrappers forced
`skip_digestion=True` on delegation, and several shape digesters rejected the
`Quantity` values that callers actually pass. Both have been fixed (see
[units_and_quantities.md](units_and_quantities.md) for the full quantity policy):

- **Full-signature public methods** (e.g. `ShapesManager.add_sphere`) carry
  `@digest()` and delegate to their submodule helper with `skip_digestion=True`
  (the inner is an internal, already-validated call).
- **Thin `*args/**kwargs` forwarders** delegate **without** forcing skip, so the
  submodule helper (which owns the real named signature and `@digest()`)
  validates on the public path. They are still not decorated themselves (Rule 1).
- **Every length digester** now accepts the real input forms (unit strings,
  `Quantity`, pint/…) and rejects bare numbers, via
  `puw.ensure_quantity(..., dimensionality={'[L]': 1})` wrapped by
  `_private/argdigest/_quantity.py::digest_length_quantity`.
- Digesting the *whole* public argument set means non-length digesters must also
  accept the shape forms: `color`, `alpha`, and `tag` are now batch-aware
  (single **or** a per-object list).

Lesson: turning on argdigest for a public method digests **all** its arguments —
budget for making every argument's digester accept the real forms, not only the
one you came for.

### Rules

1. **Decorate real public entry points**
   - use `@digest()` on public methods that own a stable argument contract.
   - do not decorate thin variadic forwarders that only pass `*args/**kwargs` to a deeper method; that creates fake digestion surfaces and noisy warnings.
   - public wrappers such as `contains(...)`, `is_composed_of(...)`, or `extract(...)` should still carry `@digest()` when they expose a real named contract, even if they delegate later.
2. **Keep `skip_digestion=True` available**
   - internal replay/rebuild flows depend on bypassing digestion once state is already normalized.
3. **Encode caller-aware semantics in digesters**
   - if `None` is valid only for specific callables, that belongs in the digester, not in ad hoc bypass code.
   - when MolSysViewer exposes both method-style and module/helper-style public routes, caller-aware digesters should accept both aliases; do not rely on one exact caller string if the API intentionally exposes more than one public entry path.
4. **Prefer normalization over scattering coercion**
   - if a public method keeps manually coercing booleans, positions, tags, colors, or lists, that is a signal to move the contract into `argdigest`.
5. **Treat warnings as migration signals**
   - `STRICTNESS = "warn"` means the integration is still being hardened.
   - do not accept `DigestNotDigestedWarning` on stable public API as normal background noise.

### Standardization

Argument-name renames are **declared as data**, in
`molsysviewer/_private/argdigest/normalization/`, one module per family of rules. Each
declares `AliasTable` instances; ArgDigest discovers them and applies them before both the
function contract and the digesters. `describe_normalization` can then list what a
function accepts.

- scope every table to the callers that need it. A rename declared for `*` is almost
  always wrong: `atom_indices` is a synonym in three methods and a real argument
  everywhere else, and declaring it globally fails 132 tests;
- a rename is not a substitute for the missing digester;
- there is exactly one mechanism. The imperative `argument_names_standardization.py` it
  replaced tested a caller string the code never produces, so all four of its branches
  were dead and `view.get(element='group', index=True)` raised `KeyError`. Two mechanisms
  deciding the same rename is how that goes unnoticed — see
  [`archive/migrate_the_standardizer_to_alias_tables.md`](archive/migrate_the_standardizer_to_alias_tables.md).

#### Cross-package alias contract

The query wrappers validate arguments in MolSysViewer and then delegate to MolSysMT with
`skip_digestion=True`. They therefore build their caller-scoped `AliasTable` objects from
the versioned plain-data contract returned by
`molsysmt.attribute.get_argument_aliases()`. No MolSysMT private alias module is a
consumer interface.

Wheel and Conda metadata require `argdigest>=0.12.1` and `molsysmt>=0.22.0`; the latter
introduces this public provider, while the former is the first ArgDigest release that
rejects alias-target collisions before a value can be discarded. Both manifests, the
public contract and the resulting viewer calls are guarded by tests. Do not relax either
floor or silently filter malformed upstream aliases to accommodate an old release.
Canonical and alias keywords are alternatives; simultaneous use raises
`ArgumentConsistencyError`. The original dependency defect and migration history are
recorded by `uibcdf/molsysviewer#62` and `uibcdf/molsysmt#157`.

### Interaction with PyUnitWizard

Some digesters are unit-aware and must remain aligned with the local `molsysviewer._pyunitwizard.puw` instance.

Current rule:

- `molsysviewer` should use one local PyUnitWizard path;
- do not mix local digestion/config with `molsysmt.pyunitwizard` aliases.

**Physical magnitudes (lengths, positions, …) must be quantities, never bare
numbers.** This is a hard policy with its own document —
[units_and_quantities.md](units_and_quantities.md) — covering how to write a
length digester (`digest_length_quantity` / `puw.ensure_quantity`), how to
convert to the Mol\* wire unit (`puw.get_value(..., to_unit="angstroms")`), and
the `skip_digestion` contract.

### Practical Audit Standard

When auditing public API digestion:

- check for missing-digester warnings on real demo viewers;
- check for valid public calls rejected by overly strict digesters;
- prefer regression tests that assert warning-free use of core wrappers.
- distinguish between:
  - public contract wrappers: digest and then delegate with `skip_digestion=True`;
  - pure variadic forwarders: keep `@signal()`, but avoid fake `@digest()` layers.

## Dependency Management (DepDigest)

DepDigest manages both hard and soft dependencies to ensure environmental robustness.

### Configuration
- **File**: `molsysviewer/_depdigest.py` lists all required libraries and their types.
- **Initialization**: `molsysviewer/__init__.py` calls `check_dependency(__name__)` on import before pulling in heavier public submodules.

### Rule of Use
- Decorate classes or methods requiring specific libraries with `@dep_digest('library_name')`.
- This ensures that if a dependency is missing, a professional `LibraryNotFoundError` is emitted via SMonitor instead of a generic Python `ImportError`.

### Current Decision

Bootstrap ordering matters.

- `depdigest` only adds real value if it runs before heavyweight imports fail.
- late dependency checks are treated as an integration defect.

Current local rule:

- the support stack itself should be explicit in `molsysviewer/_depdigest.py`;
- `argdigest`, `depdigest`, `pyunitwizard`, and `smonitor` are treated as hard
  dependencies, not incidental transitive imports.
- `MAPPING` should start small and concrete:
  - use it first for MolSysMT-owned object/file forms that MolSysViewer really
    accepts in public entry points;
  - do not pre-fill speculative add-on or standalone capability maps before the
    runtime actually needs them.
