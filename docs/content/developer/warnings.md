# Warnings

MolSysViewer routes warnings through **SMonitor**. The warning catalog lives in
`molsysviewer/_private/smonitor/catalog.py` and messages are configured through
`molsysviewer/_smonitor.py`.

## How it works

- Python code emits warnings via `smonitor.integrations.emit_from_catalog`.
- The catalog entry defines code, category, and level.
- Messages are rendered by SMonitor using the catalog code templates.

## Where warnings are emitted (current)

- Undigested arguments in the digestion layer.
- Frontend initialization failures (`viewer_init_failed`).

## Adding a new warning

1. Add a catalog entry in `molsysviewer/_private/smonitor/catalog.py`.
2. Define the corresponding code in `molsysviewer/_smonitor.py`.
3. Emit with `emit_from_catalog(...)` from the relevant module.
4. Add a focused test in `tests/`.
