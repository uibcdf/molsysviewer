# Digestion and Dependencies

MolSysViewer follows the UIBCDF standards for argument validation and dependency management through **ArgDigest** and **DepDigest**.

## Argument Digestion (ArgDigest)

We use ArgDigest in **package style**. Validation and normalization live outside the public orchestration methods and are discovered from the package digestion config.

### Structure
- **Config**: `molsysviewer/_argdigest.py` defines the source of digesters.
- **Engine**: `molsysviewer/_private/argdigest/` contains the adapters and sub-packages.
- **Digesters**: `molsysviewer/_private/argdigest/argument/` contains one `.py` file per argument name (e.g., `centers.py`, `radii.py`).

### Current contract (2026-09-30)

Every ordinary supported public function has `@digest()` and an explicit
`skip_digestion=False` parameter, including queries, delegating constructors,
scene-handle methods and experimental hosts. There are no inventory exemptions.
The inventory covers 699 reachable routes and reports missing decorators,
missing bypass parameters and missing named digesters separately. Exported class
methods are included, as well as handles returned by managers.

Delegating constructors expose the complete named signature. They validate at
the public boundary and pass `skip_digestion=True` to an already validated inner
call. Do not introduce opaque `*args` wrappers or `args`/`kwargs` placeholder
digesters. `view.annotations.add` is the single general annotation constructor.

Public color normalization is decorated. Its digesters use private normalization
primitives so validation does not recursively re-enter the public function.
Whole and region molecular queries use a strict registry derived from public
MolSysMT attribute metadata for boolean request flags, plus the local scope
validators. MolSysMT remains responsible for the scientific query.

Shape quantities accept real unit strings and Quantity objects. See
[units_and_quantities.md](units_and_quantities.md). Activating digestion means
checking every named argument, including tags, batches and optional values.

### Rules

1. **Decorate every ordinary public function**
   - use `@digest()` even when the function delegates, reads state or has no inputs.
   - expose full named parameters rather than a variadic-only public signature.
   - properties, constructors and Python protocol methods are outside this callable inventory.
2. **Declare `skip_digestion=False` explicitly**
   - internal replay/rebuild flows bypass digestion once state is normalized.
   - the bypass does not bypass lifecycle checks or scientific invariants.
3. **Encode caller-aware semantics in digesters**
   - if `None` is valid only for specific callables, that belongs in the digester, not in ad hoc bypass code.
   - when MolSysViewer exposes both method-style and module/helper-style public routes, caller-aware digesters should accept both aliases; do not rely on one exact caller string if the API intentionally exposes more than one public entry path.
4. **Prefer normalization over scattering coercion**
   - if a public method keeps manually coercing booleans, positions, tags, colors, or lists, that is a signal to move the contract into `argdigest`.
5. **Treat warnings as migration signals**
   - `STRICTNESS = "warn"` means the integration is still being hardened.
   - do not accept `DigestNotDigestedWarning` on stable public API as normal background noise.
6. **Argument names are one namespace for the whole package**
   - a digester is resolved by argument name alone (`decorator.py`: `plan.digesters.get(argname)`), so naming a public parameter selects a contract that may already exist. `arg_digest.map` does not change this: mapped pipelines run **after** the by-name loop, not instead of it.
   - reusing a name is normal and often right. Rule 3 already says caller-aware semantics belong in the digester, and that is the tool when **the argument means the same thing with different admissible values per caller** — `atom_name` accepts a `bool` from `get` and a string from `molsysmt.form.*`, and one idea stays in one file.
   - it is the wrong tool when the argument means **an unrelated thing**. Then a caller branch unifies nothing: it puts two domains in one file and makes the newcomer's correctness depend on edits to the other. Give it its own name instead, and its own contract.
   - know which dispatchers end in a bare `raise`. `value.py` is MolSysMT's, 566 lines keyed on caller suffixes, and a caller it does not recognise raises on **every** call the moment the function is decorated — the cost is paid by whoever debugs the explosion, not by whoever chose the name. `molsysviewer.remote`'s packet validators hit exactly this and were renamed to `packet` (`uibcdf/molsysviewer#83`).

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

The query wrappers validate request flags and scope in MolSysViewer and delegate
the scientific operation to MolSysMT. They build their caller-scoped `AliasTable` objects from
the versioned plain-data contract returned by
`molsysmt.attribute.get_argument_aliases()`. No MolSysMT private alias module is a
consumer interface.

Wheel and Conda metadata require `argdigest>=0.13.0` and `molsysmt>=0.22.0`; the latter
introduces this public provider. ArgDigest 0.12.1 first rejected alias-target
collisions, but 0.13.0 is the minimum compatible with SMonitor 0.16.0's
read-only catalog-error properties. Both manifests, the public contract and
the resulting viewer calls are guarded by tests. Do not relax either floor or
silently filter malformed upstream aliases to accommodate an old release.
Canonical and alias keywords are alternatives; simultaneous use raises
`ArgumentConsistencyError`. The original dependency defect and migration history are
recorded by `uibcdf/molsysviewer#62` and `uibcdf/molsysmt#157`.

The read-only [dependency contract audit](dependency_contract.md) derives all
runtime requirements and Python bounds from `pyproject.toml`. Its inventory
classifies recipe, environments and controlled source workflows without
duplicating versions. It checks metadata before release builds and installed
source-provider floors/provenance before CI consumes them. Installed API
compatibility remains a separate qualification.

### Interaction with PyUnitWizard

Some digesters are unit-aware and must remain aligned with the local `molsysviewer._pyunitwizard.puw` instance.

Current rule:

- `molsysviewer` should use one local PyUnitWizard path;
- do not mix local digestion/config with `molsysmt.pyunitwizard` aliases.

Both components call `puw.configure.has_active_policy()` during package
initialization. That API first appears in PyUnitWizard 0.25.0, so the wheel
and Conda minimum must be at least 0.25.0; declaring an unconstrained
PyUnitWizard dependency would permit a clean-install import failure.

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
  - delegating public constructors: expose named signatures and validate them;
  - private normalization primitives: keep them private to avoid validation cycles.

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

## Retained digester quarantine — 2026-10-07

Keep the 219 modules in `devtools/quarantine/argdigest_argument/` as developer
history for 1.0. They remain outside the installed package and the configured
runtime digester directory. This resolves the retain-or-delete decision in
`uibcdf/molsysviewer#78` without deleting evidence or changing argument validation.
Their batch counts and reachability measurements belong to their dated records;
do not confuse them with the current live digester inventory. Restore a module
only for a demonstrated public input, with its owning contract and regression
coverage. A later deletion requires a separate reviewed cleanup; it is not a
1.0 release obligation.
