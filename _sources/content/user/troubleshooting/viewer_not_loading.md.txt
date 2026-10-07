(User_Troubleshooting_ViewerNotLoading)=
# Viewer not loading

The viewer output cell stays blank or shows a loading spinner that never resolves.

## 1. Check WebGL availability

Open your browser's developer console (`F12` → Console tab). Look for errors like:

- `WebGL: CONTEXT_LOST_WEBGL`
- `Failed to create WebGL context`
- `THREE.WebGLRenderer: Error creating WebGL context`

If WebGL is unavailable:

- **Chrome/Edge**: go to `chrome://flags` and enable *Override software rendering list*.
- **Firefox**: go to `about:config` and set `webgl.force-enabled = true`.
- **Headless servers**: WebGL is not available without a display. Use the headless
  export path (`view.export.image()` with Qt or Playwright backend) instead of
  trying to display the widget.

## 2. Check the browser console for JS errors

Any uncaught exception during boot will prevent the viewer from rendering.
Common patterns:

- `Cannot read properties of undefined` — usually a version mismatch between
  the installed Python package and the bundled `viewer.js`. Run
  `pip install --upgrade molsysviewer` and hard-refresh the page (`Ctrl+Shift+R`).
- `Content Security Policy` violations — some JupyterHub deployments restrict
  inline scripts. Contact your hub administrator.

## 3. JupyterLab vs Classic Notebook

- **JupyterLab ≥ 4**: the widget renders via anywidget. Ensure
  `pip install anywidget` is installed in the same environment.
- **Classic Notebook**: ipywidgets ≥ 7 is required.
- **VS Code Jupyter**: supported; if the cell output is blank, try
  *Restart Kernel and Run All Cells*.

## 4. Kernel / widget state mismatch

If a previously running cell's output stays frozen after a kernel restart:

```python
# Force a fresh view — don't reuse a stale view object
view = mv.MolSysView()
view
```

## 5. Still stuck

Run this diagnostic snippet and paste the output in your bug report:

```python
import molsysviewer as mv
print(mv.__version__)

import anywidget
print("anywidget:", anywidget.__version__)

import sys
print("Python:", sys.version)
```
