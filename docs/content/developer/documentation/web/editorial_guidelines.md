# Web documentation editorial guidelines

Use this page as the source of truth when you write or review MolSysViewer web documentation.
It applies to humans and AI agents.

## Why this exists

You want consistent pages across the docs.
You also want diffs that are reviewable and a site that builds without running notebooks.

## Writing style (always)

- Write in the second person (“you”).
- Keep sentences short.
- Explain “why” before “how”.
- Prefer headings and lists over long paragraphs.
- Keep API names exact.
- Keep code and docstrings in English.

## File types

Choose the file type based on what you need to show.

Decision rule
- If you must show **code and its output**, use `.ipynb`.
- If you only show **code without output** (or pure text), use `.md`.
- Use `.rst` only when you need Sphinx machinery (usually API/autosummary).

Use `.ipynb`
- For tutorial pages that must show code *and* the output of that code.
- Freeze outputs with `docs/execute_notebooks.py` (we do not execute notebooks during Sphinx builds).

Use `.md`
- For concepts, reference, and index pages.
- When you show code snippets without outputs.
- When you embed pre-rendered HTML lite views via iframe.

Use `.rst` (rare)
- Only when needed by Sphinx machinery (typically API/autosummary pages).

## Page roles (what goes where)

Keep these sections distinct so readers do not get mixed signals.

User guide
- Use it for complete “units” focused on one concept.
- Make it reproducible.
- Mix short reference blocks (options/arguments) inside the tutorial narrative.

Cookbook
- Use it for practical, transversal workflows.
- Be didactic.
- End with export/embedding when it makes sense.

Showcase
- Use it to show what is possible.
- Be narrative, not didactic.
- Prefer `.ipynb` plus HTML lite embeds for the 3D view.

Troubleshooting (User)
- Start with the issues board guidance (yes, it is duplicated on purpose).
- Link to About → Support for contact details.

About → Support
- Keep the contact details here.
- Repeat the issues board guidance here too.

## HTML lite (preferred for 3D visuals)

Prefer docs-light “HTML lite” exports over widget outputs.
It keeps notebooks small and makes embeds stable.

- Export with `MolSysView.write_html(..., mode="lite")`.
- Store exported HTML under `docs/_static/views/`.
- Do not edit the exported HTML by hand.
- Do not read `docs/_static/views/*.html` when you work on logic or text. Treat them as build artifacts.

Embed patterns
- In `.md` pages, use an `<iframe>` pointing to the HTML file in `_static/views/`.
- In notebooks, use `molsysviewer.thirds.jupyter.load_html_in_notebook(...)` when you want a quick iframe output cell.

## Notebook execution and widget state

Sphinx builds do not execute notebooks (`nb_execution_mode = "off"`).
If you want frozen outputs in `.ipynb`, execute them manually:

```bash
python docs/execute_notebooks.py -f -r docs/content/
```

The executor strips ipywidgets/AnyWidget state by default to keep `.ipynb` files small.
If you truly need a widget-based output to survive, tag the output cell with:

- `keep-widget-state`

Use MyST-NB cell tags to control what is visible in the rendered docs:

- `remove-input` to hide “how the iframe is embedded”.
- `remove-output` to hide widget outputs (prefer HTML lite instead).

## Avoid accidental style drift

- Keep headings and naming consistent across units.
- Avoid duplicate page titles for different concepts.
- If you split one concept into two pages, make titles unambiguous (for example “Atom masking” vs “Visibility”).

## Cross-links and references

- Use `docs/content/developer/documentation/web/references.md` for linking patterns (`{doc}`, `{ref}`, `{class}`, `{func}`).
- Use `docs/content/developer/documentation/web/myst.ipynb` for MyST examples and admonitions.

See also

- {doc}`references`
- {doc}`myst`
