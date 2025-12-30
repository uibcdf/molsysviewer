# Web documentation editorial guidelines

Use this page as the source of truth when you write or review MolSysViewer web documentation.
It applies to humans and AI agents.

## Why this exists

You want consistent pages across the docs.
You also want diffs that are reviewable and a site that builds without running notebooks.

## Writing style (always)

- Write in the second person (“you”).
- Keep a warm, helpful tone.
- Prefer clear, complete explanations over telegraphic bullet lists.
- Keep sentences short when it helps readability, but do not optimize for brevity.
- Explain “why” before “how”.
- Prefer headings and lists to support scanning, but do not replace narrative with lists.
- Keep API names exact.
- Keep all repository text in English (including docs). Conversations can be in any language, but committed content must be English.

## Page anchors (labels)

Every substantial page should define a top-level label so other pages can link to it
without relying on filenames.

Put the label immediately above the top-level heading:

```markdown
(User_Intro_What)=
# What is MolSysViewer?
```

See {doc}`references` for the full cross-linking conventions.

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

### Paths for embeds in notebooks

When you embed an HTML lite file from a notebook under `docs/content/**`, use a
**relative path** from the notebook location to `docs/_static/views/`.

This keeps the embed working when you open the built documentation locally
(`google-chrome docs/_build/html/index.html`) without running a web server.

Examples:

- From `docs/content/user/introduction/*.ipynb`:

  ```python
  load_html_in_notebook("../../../_static/views/demo_1TCD.html")
  ```

- From `docs/content/showcase/*.ipynb`:

  ```python
  load_html_in_notebook("../../_static/views/quickstart.html")
  ```

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

## Section index pages (toctrees)

Many sections have an `index.md` page that exists mainly to introduce the section and list its pages.

Preferred pattern:

- 1–2 short paragraphs of warm orientation text (what the section is for, who should read it, how to approach it).
- A visible `toctree` with `:maxdepth: 1`.

Avoid duplicating the navigation by writing a manual bullet list of pages that mirrors the `toctree`. If you need extra guidance,
add a single sentence above the `toctree` (for example “Read these pages in order.”).

If you truly need a short description per page, use a small narrative paragraph with inline `{doc}` links instead of a second list.

## User-facing API naming (avoid unit suffixes)

Prefer parameter names that describe meaning, not internal representation.

- Avoid encoding units in parameter names (for example prefer `duration` over `duration_ms`).
- Convert and standardize units internally (PyUnitWizard).
- When renaming a public parameter, keep a backward-compatible alias for at least one release and document it in the docstring.

## Experimental features

If an API is user-facing but still evolving, label it clearly as experimental in both:

- the docstring, and
- the User Guide page where it is introduced.

## Cross-links and references

- Use `docs/content/developer/documentation/web/references.md` for linking patterns (`{doc}`, `{ref}`, `{class}`, `{func}`).
- Use `docs/content/developer/documentation/web/myst.ipynb` for MyST examples and admonitions.

## External links (avoid repetition)

External links are useful, but repeated URLs make pages harder to read.

- Link to an external project the first time you introduce it on a page.
- After that, use the project name without repeating the URL, unless you are pointing
  to a different resource (for example “Mol* docs” vs “Mol* homepage”).

## API-link density (readability first)

Not every mention of code should become a hyperlink.

- Use inline code (backticks) for light references inside narrative text.
- Use Sphinx roles (`{class}`, `{func}`, `{meth}`, `{attr}`) when a link genuinely helps:
  - the first time you introduce a key entrypoint,
  - when you want the reader to jump to the reference for details,
  - when a name might otherwise be ambiguous.
- In introduction pages, keep API links sparse. In technical pages (Viewer/Loading/Export),
  increase linking where it helps comprehension and navigation.

## Code conventions in user-facing docs

- In User Guide, Cookbook, and Showcase examples, import the package as:

  ```python
  import molsysviewer as viewer
  ```

  Keep this consistent across pages. Avoid using multiple aliases (`mv`, `msv`, etc.).

See also

- {doc}`references`
- {doc}`myst`
