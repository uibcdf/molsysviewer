# SMonitor integration

This repo uses SMonitor for warnings, errors, and developer diagnostics.

## Files

- `molsysviewer/_smonitor.py`
- `molsysviewer/_private/smonitor/catalog.py`
- `molsysviewer/_private/smonitor/meta.py`
- `molsysviewer/_private/smonitor_emit.py`

## Rules

- Emit through `emit_from_catalog` using the catalog entry.
- Keep user messages explicit and actionable.
- Keep URLs in `meta.py` so hints remain consistent.
