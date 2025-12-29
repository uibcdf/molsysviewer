# References and Cross-links in Documentation

This page defines how to create **robust, consistent cross-references** in the
MolSysViewer documentation using MyST and Sphinx. The goal is to avoid fragile
filename-based links and make it easy to reorganize pages without breaking
links.

The rules here apply to:

- User Guide notebooks and pages (`docs/content/user/**`).
- Showcase examples (`docs/content/showcase/**`).
- Developer documentation (`docs/content/developer/**`).

API references follow the same conventions but use dedicated roles (see below).

## Section labels and `{ref}` roles

### Defining labels

Every important page or section that might be linked from elsewhere should have
a **label**. In MyST, labels are written as:

```markdown
(User_Intro_MolecularSystems)=
# Molecular systems
```

Guidelines:

- Place the label **immediately above** the heading it refers to.
- For most pages, define a **top-level label** immediately above the H1 title.
- Use a descriptive, stable name:
  - Existing patterns include `Tutorial_Get_attributes`, `User_Intro_*`,
    `Showcase_Quickstart`, etc.
  - Prefer labels that encode the role of the page (User, Tutorial, Showcase,
    Dev) and the topic, rather than directory structure.
- Avoid renaming labels unless strictly necessary; labels are the stable
anchors for cross-references.

### Linking with `{ref}`

To link to a labeled section or page, use the `{ref}` role:

```markdown
See {ref}`User_Intro_MolecularSystems` for an overview of how molecular
systems are represented in MolSysViewer.
```

This is preferred over hard-coding filenames such as
`[Molecular systems](../../intro/molecular_systems/index.md)` because:

- It continues to work if files are moved or reorganized.
- It keeps link targets consistent between `.md` and `.ipynb` sources.

Use `{ref}` for:

- Links between pages in the User Guide (Introduction ↔ Tools ↔ Cookbook).
- Links from Showcase or Cookbook recipes back to conceptual pages.
- Links between developer documentation pages.

## Page-level labels for tutorials and recipes

Tutorial notebooks and recipes should define a top-level label to make them
easy to reference:

```markdown
(Tutorial_Get_attributes)=
# Get attributes
```

Examples of good patterns:

- `Tutorial_Get_attributes`
- `Tutorial_Select`
- `Cookbook_OpenMM`
- `Showcase_Quickstart`

When linking from another page:

```markdown
For a step-by-step example, see {ref}`Tutorial_Get_attributes`.
```

Avoid linking directly to filenames (for example, `get_attributes.ipynb`) when a
label exists or can easily be added.

## API references: `{func}`, `{class}`, and friends

When referring to API objects, use the appropriate Sphinx roles through MyST.
In most cases you will use `{func}` and `{class}`:

```markdown
Use {class}`molsysviewer.viewer.MolSysView` as the main user-facing entrypoint.
```

Guidelines:

- Use `{func}` for functions and methods.
- Use `{class}` for classes.
- Do not wrap `{func}` or `{class}` links inside extra Markdown link syntax.
- In tutorials, place API links in an `API documentation` admonition when
  possible, as described in the Developer Guide.

### API-link density

Use API links intentionally:

- Prefer backticks for casual mentions in narrative text.
- Add `{class}` / `{func}` / `{meth}` links when you want to invite the reader to
  inspect the reference, especially on first introduction of a key entrypoint.
- Avoid linking every symbol on a page; too many links reduce readability.

## File-based links (when they are acceptable)

There are still cases where plain Markdown links to files are appropriate:

- Linking to **non-Sphinx content** (for example, external websites, PDFs,
  external GitHub repositories).
- Temporary links inside experimental notebooks that are not part of the main
  navigation and are not meant to be long-lived.

In these cases, use standard Markdown:

```markdown
See the MolSysViewer GitHub repository for more details:
[uibcdf/molsysviewer](https://github.com/uibcdf/molsysviewer).
```

Avoid using file-based links to internal pages when a label and `{ref}` can be
used instead.

## External links (first-mention rule)

External links are part of good documentation, but repeating URLs makes pages noisy.

- Link to an external project the first time you mention it on a page.
- Do not repeat the URL for every subsequent mention of the same project on the same page.
- Repeat only when you are pointing to a different destination (for example a specific guide page).

## Cross-linking between major sections

### User Guide ↔ Showcase ↔ Cookbook

Preferred patterns:

- From the User Guide Introduction to Showcase Quickstart:

  ```markdown
  We strongly recommend starting with the Quickstart tutorial in the Showcase
  section: {ref}`Showcase_Quickstart`.
  ```

- From Showcase Quickstart back to the User Guide:

  ```markdown
  If you want to go deeper, the {ref}`User_Intro_Index` page explains the main
  concepts used throughout the User Guide.
  ```

- From Cookbooks to Tools:

  ```markdown
  This recipe makes heavy use of {ref}`Tutorial_Get_attributes` and
  {ref}`Tutorial_Select`, which you may want to review first.
  ```

Use `{ref}` consistently for these cross-links; avoid direct references to
`../user/index.ipynb` or `index.md` when a label exists or can be added.

### Developer docs and API guides

- Developer documentation under `docs/content/developer` should use `{ref}` to
  point to other developer pages and to the User Guide when relevant.
- When pointing to API content, prefer `{func}` / `{class}` roles instead of
  linking to generated HTML in `docs/api`.

## Migration notes and legacy links

Existing documentation still contains many links of the form:

- `../showcase/quickstart.ipynb`
- `../../intro/molecular_systems/attributes.ipynb`
- `index.md`

These links work but are fragile if files move. When updating a page:

- If you touch a section that already has a label, consider replacing filename
  links with `{ref}`.
- When creating or substantially editing a tutorial, add a label at the top and
  use `{ref}` for cross-links.

There is no need to migrate all links at once, but **new or updated content**
should follow the conventions in this document. Over time, legacy links can be
cleaned up as pages are revisited.
