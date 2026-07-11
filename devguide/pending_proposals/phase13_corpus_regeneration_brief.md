# Phase 13 — Corpus regeneration · design brief

**Author:** backend contract owner · **For:** the collaborator implementing Phase 13.
**Size:** M · **Depends on:** P12 (done, `656cc515`).
**Normative source:** `region_contracts.md` §Migration — that table *is* the checklist.

---

## 0. Scope — read this first

**In scope:** `docs/` (source only) and `bloques.md`.

**Out of scope, do not touch:** `sandbox/` — including `sandbox/Curso/`. The master plan lists it
under this phase; it is **carved out**. It is the maintainer's working area and has uncommitted
work in it. Ignore it entirely, even if a grep points there.

Also out of scope: `docs/_build/` (build artefacts — never hand-edit; a grep for the old API will
hit hundreds of lines in `_build/html` and `_build/doctrees`. They regenerate. Ignore them).

---

## 1. Why this phase is not a find-and-replace

Two of the three problems are invisible to `grep`.

**Problem 1 — dead API (grep finds these).** `view.new_region()` **no longer exists**. Verified:

```python
>>> hasattr(MolSysView, "new_region")
False
```

Only `active_selection.new_region()` and `selections.new_region()` (saved selection → region)
survive. The top-level one is gone; its replacement is `view.regions.add(...)`. There are **15**
`view.new_region(` call sites in `docs/` source. Every one of them raises `AttributeError` today.

**Problem 2 — semantic change with no syntactic change (grep cannot find these).** This is the
dangerous half, and the reason the phase exists:

> `reset_colors()` still exists. It still takes no arguments. It still returns `None`.
> **And it now means something different.** A notebook calling it stays green and quietly does the
> wrong thing.

The full list is `region_contracts.md` §Migration. The ones that bite the corpus:

| Call | Was | Is now |
|---|---|---|
| `Region.reset_colors()` | wiped the whole canvas | clears **that region's layer** only |
| `Whole.reset_colors()` | wiped the whole canvas | clears **the base layer** only |
| a canvas-wide wipe | either of the above | `view.reset_all_colors()` — **new method** |
| any `reset_colors()` | painted the system grey (`0xaaaaaa`) | **restores the structural theme** |
| colouring one region | greyed out every other atom | leaves the rest on its structural theme |
| `Region.reset_representation()` | rendered `cartoon` | **removes the region's own visual** |
| `set_representation(None, **params)` | rendered `cartoon` | state **None**; params ignored — use `"inherit"` |
| `Region.set_color_by_values(replace=True)` | replaced the canvas map | replaces **within the region's layer** |
| whole's colour scheme | a frontend dropdown in **System** | `whole.set_color_scheme()`, serialised (P12) |
| `export_state` | `version: 1`, identity only | `version: 2`, full state (still reads v1) |

So a passage that says *"reset_colors() clears all the colours in the scene"* is now **false prose
around still-executing code**. The text is as much of a deliverable as the code.

**Problem 3 — the safety net does not exist.** `docs/conf.py:83` sets:

```python
nb_execution_mode = "off"
```

**Sphinx does not execute the notebooks.** A notebook whose every cell raises `AttributeError`
builds green and ships. Do not mistake a clean `make html` for a working corpus. The only real
check is `docs/execute_notebooks.py` (§4).

---

## 2. Verified inventory (source only; `_build/` and `sandbox/` excluded)

225 source files under `docs/` (`.md`, `.rst`, `.ipynb`), of which **26 notebooks**. Call sites:

| Pattern | docs/ | bloques.md |
|---|---|---|
| `view.new_region` | 15 | 0 |
| `MolSysView.new_region` (autosummary) | 4 | 0 |
| `whole.set_representation` | 12 | 1 |
| `view.regions[` | 7 | 0 |
| `whole.hide` | 7 | 0 |
| `set_color_by_values` | 3 | 0 |
| `reset_colors` | 2 | 0 |
| `set_color_by_attribute` | 1 | 0 |

Files that contain at least one of these (24), grouped by how they must be treated:

**(a) Rewrite — user-facing documentation of current behaviour:**
`content/user/scene_management/{regions,whole,visibility,tags}.md`,
`content/user/representations/{types,presets,styles,user_presets}.md`,
`content/user/introduction/what.md`, `content/user/tools/basic/merge.md`,
`content/user/cookbook/workbench_scientific_workflow.md`,
`content/user/cookbook/tutorial_trajectory_analysis.ipynb`, `index.ipynb`,
`content/developer/{public_api,regions_layers,modules_overview,configuration}.md`.

**(b) Regenerate, do not hand-edit — `docs/api/public/autosummary/*.rst`.**
`conf.py:97` sets `autosummary_generate = True`; these stubs are generated from the code. If they
still list `MolSysView.new_region`, the fix is to regenerate (and check `docs/clean_api.py`), not
to edit the stub.

**(c) DO NOT REWRITE — historical records:**
`content/developer/architecture_snapshot_2025_11.md`,
`content/developer/architecture_snapshot_2026_01.md`,
`content/developer/changes_notes.md`.

A dated snapshot describes the codebase **as it was on that date**. Rewriting it to use the new API
does not fix a stale document, it falsifies a record — and destroys the only account of why the
change was made. Leave the code samples in them exactly as they are. If a snapshot is actively
misleading, add a dated banner at the top pointing at the migration table. **Nothing else.**
The same goes for the changelog: it records what happened, not what is currently true.

---

## 3. What to do

1. **Audit every call site against the migration table, one by one.** Not a sweep. For each site
   record: file, the old call, the verdict — *dead* / *semantically changed* / *still correct* —
   and the replacement. `view.regions["tag"]` (7 sites) is very likely **still correct**: check it,
   don't "fix" what isn't broken. Land this table in the PR description or a scratch file; it is
   the artefact that proves the audit happened rather than a regex ran.
2. **Rewrite the (a) files** against the current API: `view.regions.add(...)`, the `"inherit"`
   sentinel, layered colour, `view.reset_all_colors()`, recipes (`mode="dynamic"`), and the P12
   whole surface (`whole.set_color_scheme`, `whole.reset_representation`, `whole.visible`).
   **The prose is part of the fix.** A corrected code cell under a paragraph that still says
   "clears every colour in the scene" is a half-done file.
3. **`bloques.md`:** the plan's instruction is *delete it or bring it in line*. It has a single
   stale call. Read it and make a call — if it is superseded by `docs/`, deleting it is the right
   answer and the honest one. Say which you chose and why.
4. **Regenerate the autosummary stubs (b).**
5. **Leave (c) alone**, per §2.

---

## 4. How this phase is verified

There are no unit tests here. The verification is that the corpus **runs**:

```bash
python docs/execute_notebooks.py -r -f          # executes every notebook; check notebook_errors.log
cd docs && make html                            # must not warn on the pages you touched
```

`execute_notebooks.py` is the only thing that will catch a dead API call, because Sphinx will not
(§1, Problem 3). **A notebook that has not been executed has not been migrated.** Report the
executed count and the contents of `notebook_errors.log`.

Mechanical acceptance (greppable, excluding `_build/`, `sandbox/` and the (c) historical files):

```bash
grep -rn "view\.new_region\|MolSysView\.new_region" docs bloques.md   # → 0
```

And a judgement one, which is the real point of the phase: **for every surviving `reset_colors()`,
`reset_representation()` and `set_representation(None, …)` in the corpus, the surrounding prose
describes the new semantics.** If you cannot say that sentence about a file, it is not done.

---

## 5. Reminders

* **Do not touch `sandbox/`** — not `sandbox/Curso/`, not `sandbox/Test.ipynb`. Nor
  `devguide/course/`.
* Do not hand-edit `docs/_build/` or `molsysviewer/viewer.js`.
* Python + JS suites must stay green (this phase should not touch them at all — if a source file
  under `molsysviewer/` changes, something has gone wrong; say so rather than adapting the docs
  around a bug you found. **A doc bug that turns out to be a code bug gets reported, not
  papered over.**)
* **Do not commit.** Leave the tree for audit, with a written statement of what you did **not** do.
