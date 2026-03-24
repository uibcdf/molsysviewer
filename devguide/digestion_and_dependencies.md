# Digestion and Dependencies

MolSysViewer follows the UIBCDF standards for argument validation and dependency management through **ArgDigest** and **DepDigest**.

## Argument Digestion (ArgDigest)

We use ArgDigest in **package style**. Validation and normalization live outside the public orchestration methods and are discovered from the package digestion config.

### Structure
- **Config**: `molsysviewer/_argdigest.py` defines the source of digesters.
- **Engine**: `molsysviewer/_private/arg_digestion/` contains the adapters and sub-packages.
- **Digesters**: `molsysviewer/_private/arg_digestion/argument/` contains one `.py` file per argument name (e.g., `centers.py`, `radii.py`).

### Current Status

- package-style digestion is active and broadly integrated across the public API;
- core noisy wrappers have now been hardened with explicit digesters;
- thin but real public query wrappers such as `contains(...)`,
  `is_composed_of(...)`, and `extract(...)` are also part of the hardening
  surface when they own a stable contract;
- missing-digester warnings on stable public paths are treated as integration debt;
- shape/detail coverage is broader than before, but not yet exhaustive across every argument of every overlay method.

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
   - if a public method keeps manually coercing booleans, positions, tags, colors, or lists, that is a signal to move the contract into `arg_digestion`.
5. **Treat warnings as migration signals**
   - `STRICTNESS = "warn"` means the integration is still being hardened.
   - do not accept `DigestNotDigestedWarning` on stable public API as normal background noise.

### Standardization

`argument_names_standardization.py` is intentionally narrow.

- use it for stable caller-aware renames and synonym handling;
- do not rely on it as a substitute for writing the missing digester.

### Interaction with PyUnitWizard

Some digesters are unit-aware and must remain aligned with the local `molsysviewer._pyunitwizard.puw` instance.

Current rule:

- `molsysviewer` should use one local PyUnitWizard path;
- do not mix local digestion/config with `molsysmt.pyunitwizard` aliases.

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
