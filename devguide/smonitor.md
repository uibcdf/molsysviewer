# SMonitor Integration

MolSysViewer utilizes **SMonitor** as its primary diagnostics and telemetry engine. It ensures consistent messaging and execution traceability across the UIBCDF ecosystem.

## Key Components

- **Runtime Configuration**: `molsysviewer/_smonitor.py` defines execution profiles (`user`, `dev`, `qa`, etc.) and binds message templates.
- **Authoritative Catalog**: `molsysviewer/_private/smonitor/catalog.py` contains all signal metadata and user-facing `CODES`.
- **Diagnostic Bundle**: `molsysviewer/_private/smonitor/emitter.py` provides standardized `warn` and `warn_once` helpers.

## What It Is Used For Here

SMonitor is not only for end-user diagnostics.
In this repository it is also part of the developer and QA workflow:

- breadcrumbing cross-library execution paths;
- making missing context visible in `dev` and `qa` profiles;
- profiling wrapper flows through `Manager.report()["timeline"]`;
- enforcing `SIGNALS` contracts on important orchestration methods.

## Developer Rules

### 1. Zero String Hardcoding
Never use plain strings for warnings or errors in the scientific logic. Always add an entry to the `CATALOG` and a corresponding template in `CODES`, then emit via the catalog key.

### 2. Telemetry with `@signal`
All major public orchestration entry points should be decorated with `@signal(tags=[...])`.

Current project rule:

- if a public entry point carries `@digest()`, it should generally also carry `@signal()`;
- this is now checked structurally in tests for the main public surface.

Use `extra_factory` when structured context materially improves debugging or QA triage.
Good examples in the current codebase include:

- camera snapshot methods,
- controls visibility methods,
- export methods,
- representation-setting wrappers.
- panel/workspace notebook helpers should also use structured context when they
  become part of QA or interactive support workflows.

### 3. Catalog-Powered Exceptions
Custom exceptions must inherit from `CatalogException` (and typically `ValueError` or `TypeError` for Python compatibility). This ensures that error messages are automatically hydrated from the catalog metadata.

Example:
```python
from molsysviewer._private.arg_digestion.exceptions import ArgumentError
# This exception automatically pulls its message from CATALOG['argument_error']
```

### 4. Signal Contracts

Important orchestration signals should define `extra_required` fields in `catalog.py`.

This matters because:

- `dev` / `qa` profiles can surface missing structured context,
- timeline events become more useful for support and debugging,
- the repo can test not just "was a signal emitted?" but also "was enough context emitted?".

### 5. Do Not Use It Superficially

Avoid adding `@signal` just to increase counts.
Signals should exist where they help us answer:

- what public operation was attempted,
- with what relevant context,
- and where in the orchestration path it failed or became slow.

## Current Status

- package init is configured through SMonitor;
- catalog-backed exceptions/warnings are in place;
- public wrapper coverage is much broader than before;
- timeline regressions exist for camera, shape, region, whole, and export wrappers;
- structural tests enforce that the main public `@digest()` surface also carries `@signal()`.

Remaining work should be selective:

- add context to new orchestration paths when they are introduced;
- expand contracts only when they improve real QA/dev workflows.

Current example of that rule:

- the notebook-facing panel/workspace control surface now carries structured
  signal context for:
  - `set_panel_mode(...)`
  - `set_workspace(...)`
  - `set_workspace_panel(...)`
  - `workspace_catalog(...)`
  - `workspace_panels(...)`
  - `workspace_runtime(...)`
  - `get_panel_mode_state(...)`

This is intentional because these calls are now part of the fast QA loop for
shared runtime behavior.

- the same structural rule also applies to small but real public config entry
  points such as the local PyUnitWizard defaults in `molsysviewer.config`.

## Traceability

ArgDigest and DepDigest are also instrumented through SMonitor.

A typical successful public call can look like:

`[molsysviewer.viewer.load] -> [dependency_check] -> [digestion] -> [loader/replay/state ops]`

And when profiling is enabled, those wrapper calls should appear in `Manager.report()["timeline"]` with useful tags and structured metadata.
