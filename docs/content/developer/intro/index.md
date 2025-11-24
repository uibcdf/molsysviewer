# Getting started

- Clone or fork the repository.
- Set up the dev environment (conda + Node for TypeScript), per `README_DEVELOPERS.md`.
- Build JS once: `cd js && npm install && npm run build` (produces `molsysviewer/viewer.js`; do not edit it manually).
- Editable install: `pip install -e .` in the repo root.
- Iterate in notebooks with anywidget (the bundle is already present).
- When touching TS/JS, you may rebuild manually if needed; never auto-rebuild in tests/CI.
- Doc demos: export static views (`write_html`) into `_static/views/` and embed with `molsysviewer.thirds.load_html_in_jupyter_notebook`.

Typical dev loop
- Python change → reload module (editable install).
- TS change → optional `npm run build` if you need to test the bundle locally; otherwise leave it for maintainers.
- Tests: prefer unit-level checks (see Testing section).
- Docs: update markdown/notebooks; build with `make html` locally when reviewing.

```{toctree}
:hidden:
:maxdepth: 1
```
