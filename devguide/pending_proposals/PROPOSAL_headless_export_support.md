# PROPOSAL: Headless / Offline Export Support

## Problem Statement
Currently, `view.export.image()` and `view.export.html()` require the viewer widget to be explicitly displayed and rendered in a live Jupyter notebook session before any export can take place. If the user attempts to export before calling `view`, the operation fails because the Mol* engine (which lives in the browser's JavaScript environment) is not initialized. This prevents the library from being used in:
1. Pure Python scripts (no notebook environment).
2. Automated pipelines/batch processing.
3. "Run All" notebook scenarios where export cells precede visualization cells.

## Proposed Solution: Headless Rendering Mode
Implement a mechanism to trigger exports without a human-facing browser window.

### Option A: Internal Headless Browser (Advanced)
Use a library like `playwright` or `puppeteer` (via a python wrapper) to launch a hidden browser instance in the background, load the viewer, and perform the export.
```python
view.export.image('out.png', headless=True) # Launches background browser if needed
```

### Option B: Improved State Serialization
Allow `view.export.html()` to work purely from the `_message_history` and Python state, without requesting a "camera snapshot" from a live frontend. This is already partially possible for HTML, but fails if the frontend is not "ready".

### Option C: CLI Tooling
Provide a command-line utility that takes a PDB/CIF and a script of viewer commands and outputs the requested media using a headless runtime.

## Benefits
- **Automation:** Allows scientists to generate thousands of images overnight without manual intervention.
- **Robustness:** Makes the library independent of the specific Jupyter environment's rendering state.
- **Workflow Flexibility:** Users can write scripts that prepare data and export results without ever seeing the 3D window.

## Implementation Path
- Investigate the use of a lightweight headless JS runtime for Mol*.
- Update `MolSysView` to allow "best-effort" exports when `self._ready` is `False`.
- Refactor camera management so that camera state can be defined in Python and sent to the export engine, rather than always being "captured" from the live view.
