# SMonitor integration

MolSysViewer routes warnings and errors through **SMonitor** so that user-facing
messages, developer diagnostics, and QA traces remain consistent across the
MolSys ecosystem.

## Integration surface

- Configuration: `molsysviewer/_smonitor.py`.
- Catalog: `molsysviewer/_private/smonitor/catalog.py`.
- Metadata (docs/issues/API URLs): `molsysviewer/_private/smonitor/meta.py`.
- Emission helper: `molsysviewer/_private/smonitor_emit.py`.

## How to emit

Use `smonitor.integrations.emit_from_catalog(...)` with the catalog entry and
`PACKAGE_ROOT`/`META` from `molsysviewer._private.smonitor`.

## Adding a new signal

1. Add a new entry in `catalog.py` with code/category/level.
2. Add the code template in `_smonitor.py`.
3. Emit it from the relevant module.
4. Add a focused test in `tests/`.
