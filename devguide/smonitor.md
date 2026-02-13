# SMonitor Integration

MolSysViewer utilizes **SMonitor** as its primary diagnostics and telemetry engine. It ensures consistent messaging and execution traceability across the UIBCDF ecosystem.

## Key Components

- **Runtime Configuration**: `molsysviewer/_smonitor.py` defines execution profiles (`user`, `dev`, `qa`, etc.) and binds message templates.
- **Authoritative Catalog**: `molsysviewer/_private/smonitor/catalog.py` contains all signal metadata and user-facing `CODES`.
- **Diagnostic Bundle**: `molsysviewer/_private/smonitor/emitter.py` provides standardized `warn` and `warn_once` helpers.

## Developer Rules

### 1. Zero String Hardcoding
Never use plain strings for warnings or errors in the scientific logic. Always add an entry to the `CATALOG` and a corresponding template in `CODES`, then emit via the catalog key.

### 2. Telemetry with `@signal`
All major API entry points in `MolSysView` must be decorated with `@signal(tags=[...])`. This allows SMonitor to build a "breadcrumb trail" of the user's session, which is invaluable for debugging and AI agent context.

### 3. Catalog-Powered Exceptions
Custom exceptions must inherit from `CatalogException` (and typically `ValueError` or `TypeError` for Python compatibility). This ensures that error messages are automatically hydrated from the catalog metadata.

Example:
```python
from molsysviewer._private.arg_digestion.exceptions import ArgumentError
# This exception automatically pulls its message from CATALOG['argument_error']
```

## Traceability
DepDigest and ArgDigest are also instrumented with SMonitor signals. A typical operation like `view.load()` will generate a chain of signals:
`[molsysviewer.load] -> [dependency_check] -> [digestion] -> [SUCCESS/ERROR]`
