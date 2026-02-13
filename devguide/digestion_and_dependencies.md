# Digestion and Dependencies

MolSysViewer follows the UIBCDF standards for argument validation and dependency management through **ArgDigest** and **DepDigest**.

## Argument Digestion (ArgDigest)

We use the "Package Style" digestion. All validation logic is decoupled from the main classes and resides in a specialized private package.

### Structure
- **Config**: `molsysviewer/_argdigest.py` defines the source of digesters.
- **Engine**: `molsysviewer/_private/arg_digestion/` contains the adapters and sub-packages.
- **Digesters**: `molsysviewer/_private/arg_digestion/argument/` contains one `.py` file per argument name (e.g., `centers.py`, `radii.py`).

### Best Practices
1. **Decorate Entry Points**: Use `@digest()` on public methods. It automatically handles `skip_digestion=True` calls.
2. **Standardize Names**: Use the `argument_names_standardization.py` helper to maintain API consistency (e.g., aliasing `selection` based on `element`).
3. **Handle Numpy Arrays**: Digesters typically return `numpy.ndarray` for coordinates or indices. Ensure the receiving code in `MolSysView` or `shapes/` can handle both lists and arrays.

## Dependency Management (DepDigest)

DepDigest manages both hard and soft dependencies to ensure environmental robustness.

### Configuration
- **File**: `molsysviewer/_depdigest.py` lists all required libraries and their types.
- **Initialization**: `molsysviewer/__init__.py` calls `check_dependency(__name__)` on import.

### Rule of Use
- Decorate classes or methods requiring specific libraries with `@dep_digest('library_name')`.
- This ensures that if a dependency is missing, a professional `LibraryNotFoundError` is emitted via SMonitor instead of a generic python `ImportError`.
