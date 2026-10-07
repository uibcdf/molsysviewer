# Debugging

Use this page when you need to debug the viewer runtime (Python ↔ JS) or docs-lite exports.

## Python-side checks

- Confirm you are using an editable install when developing: `pip install -e .[dev]`.
- If you hit a MolSysMT/Numba-specific local failure, capture the traceback first and only then decide whether an environment workaround is justified.

## Frontend logs

Enable frontend debug logs:

- In notebooks, pass `debug_js=True` when creating the viewer (or use the relevant config knob).

Then open your browser devtools console and look for:

- `[MolSysViewer docs]` logs in docs-lite exports.
- `js_log` events (if you route them back to Python).

## Message-level debugging

If something “does not apply” in the frontend, debug at the message boundary:

- Inspect the Python message history (`_message_history`) if available.
- Confirm the `op` exists in the TypeScript union type `ViewerMessage`.
- Confirm required option keys match the TS type exactly.

See also

- {doc}`protocol_and_payloads`

## Popup / popout sync

If the popout mirror behaves incorrectly:

- Confirm the host is sending an initial sync (command log + camera snapshot).
- Confirm camera sync does not run while both sides are actively interacting.
- Confirm runtime injection uses the correct path:
  - Blob import in notebooks
  - `moduleUrl` in docs-lite exports

## Placeholder

Add concrete “symptom → cause → fix” entries here as issues recur.
