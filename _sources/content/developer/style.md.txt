# Coding style & conventions

Python
- Docstrings: short, user-facing, and accurate. Use type hints. Keep them in English.
- Avoid editing generated artifacts (`viewer.js`/`.map`); edit TS sources instead.
- Normalize inputs in shape APIs (length checks, type casting) and raise clear errors.
- Keep public APIs thin; delegate to helpers for heavy lifting.

TypeScript/JS
- Keep Mol* imports using existing patterns; avoid adding external deps.
- Use the existing folder structure: `managers/`, `shapes/`, `plugin/`, `messages/`, `index.ts`.
- Track shape refs and tags consistently via helper functions; register before returning.
- Don’t auto-run `npm run build` in CI/tests; build only when needed manually.

Docs
- Tone: second person, concise, “why” before “how”, scannable headings/lists.
- Assets in `_static/`, layouts in `_templates/`. Notebooks off by default for builds.
- Export docs-light views with `write_html(..., mode="lite")` and embed via `molsysviewer.thirds.jupyter.load_html_in_notebook` for showcases.

General
- Avoid touching unrelated changes; keep diffs focused.
- Use tags to group/clear shapes deterministically.
- Be cautious with localization: keep code/docstrings in English; user-facing docs may include Spanish, but keep style consistent.

See also
- {doc}`type_annotations_guidelines`
- {doc}`string_style`
- {doc}`documentation/web/editorial_guidelines`
