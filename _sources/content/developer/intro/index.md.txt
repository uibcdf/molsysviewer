# Getting started

Start here if you want to contribute or you want to understand the codebase quickly.

Typical steps
- Clone or fork the repository.
- Set up the dev environment (Python + Node.js), per {doc}`../dev_setup`.
- Install editable: `pip install -e .[dev]`.
- Run tests before pushing changes, per {doc}`../testing`.
- Follow the web docs editorial rules when writing docs, per {doc}`../documentation/web/editorial_guidelines`.

Typical dev loop
- Python change → reload module (editable install).
- TS change → optional `npm run build` if you need to test the bundle locally; otherwise leave it for maintainers.
- Tests: prefer unit-level checks (see {doc}`../testing`).
- Docs: update markdown/notebooks; build with `make html` locally when reviewing.

```{toctree}
:hidden:
:maxdepth: 1

contributing.md
```
