# MolSysMT's documentation pipeline, read at the scale it is about to reach

**Status:** analysis, 2026-08-04. Offered, not requested — MolSysMT may already
have most of this in hand. Companion to
[`molsysmt_adoption_response_2026_08.md`](molsysmt_adoption_response_2026_08.md),
which answers their report point by point. This document asks a different
question.

**The question.** The new embedding scheme is implemented in **one** notebook,
`docs/index.ipynb`, as a trial. It works. The next step is applying it to the
rest. Measured in their tree today: **138 notebooks call `msm.view()` from code
cells**, and **26** carry a target variable (`molsysviewer_htmlfile` or the
inherited `nglview_htmlfile`). So the pilot is about to be multiplied by roughly
five, and the useful thing we can do is say what changes when it is.

Everything below was read from their code, not from their report.

---

## 1. What the pilot gets right

Worth stating precisely, because the rest of this document is criticism and the
proportion matters.

- **Views are build artifacts produced by a script, not by hand.** Same policy as
  ours (`docs/generate_static_views/`), and it is the one that makes a view
  reproducible.
- **The runtime is placed at build time and gitignored.** `docs/_static/viewer.js`
  in `.gitignore`, `export_runtime_asset` on `builder-inited`. This is exactly
  the shape the mechanism was designed for, and it keeps a 6.4 MB binary out of
  their history.
- **The failure modes are loud.** The adapter consumes the target variable so a
  later cell cannot inherit an earlier one's view, and it raises when no target
  is in scope rather than falling through to a widget that could never render.
  Both are better than what their own report describes.
- **Tutorial code stays clean.** The reader sees `msm.view(molecular_system,
  selection='molecule_index==0')` and nothing else. That constraint is right and
  worth defending; everything below assumes it.

## 2. The structural problem: two sources of truth per view

This is the finding. Everything else is detail.

The reader sees this, in the notebook:

```python
msm.view(molecular_system, selection='molecule_index==0')
```

The picture beside it was produced by this, in a separate file:

```python
molsys = msm.convert(msm.systems['Barnase-Barstar']['1brs.bcif.gz'],
                     selection='molecule_type=="protein"',
                     to_form='molsysmt.MolSys')
view = msm.view(molsys, selection='molecule_index==0')
view.export.html(...)
```

The same intent, written twice, in two files, with nothing connecting them. The
notebook's `molecular_system` and the script's `molsys` are built by different
code. Change the selection in the tutorial and the picture does not change.
Change the system in the script and the tutorial text no longer describes it.
Nothing fails, nothing warns, and the page still renders.

For a scientific library this is the worst class of documentation defect: a page
that shows code and shows a result, where the result was not produced by that
code. It is not hypothetical at 138 notebooks and several years — it is the
default outcome of two files that must be edited together and are not checked
against each other.

The pilot does not show this because one notebook edited last week is trivially
in sync.

## 3. What multiplying by five costs

| | pilot (1 notebook) | migrated (138) |
|---|---|---|
| Generation scripts | 1 | one per view, hundreds |
| Hidden cells | 1 | one per view |
| Committed view HTML | 149 KB | tens of MB, rewritten on every regeneration |
| Files to edit to change one figure | 2 | 2, every time, forever |
| Notebooks that fail pre-execution until migrated | 0 | 112 today |

Three of those deserve comment.

**The migration is a cliff, not a ramp.** Because the adapter raises whenever
`MSM_VIEWS_FROM_HTML_FILES=True` and no target is in scope, and because
`execute_notebooks.py` sets that variable for every notebook it runs, a notebook
is either fully migrated or it fails. There is no state in which half the corpus
uses the new scheme and the other half still works. That is a defensible choice —
it is loud, which is what we asked for — but it means the migration has to be
completed in one campaign rather than absorbed notebook by notebook. Worth
deciding on purpose.

**The view HTML has to be committed**, because notebooks are pre-executed locally
and their outputs are committed; the site build does not run them. Each view is
150–250 KB of mostly-JSON text. Two hundred views is 30–50 MB, and a full
regeneration after a MolSysViewer upgrade rewrites all of them at once. Git will
compress it, but the history grows in steps of tens of megabytes. The alternative
— generating views in CI — costs running the full scientific stack there, which
is precisely what pre-execution exists to avoid.

**Orphans accumulate silently in one direction.** A view file whose notebook no
longer references it is never detected; a referenced file that was never
generated is detected loudly. That asymmetry is the right way round, but at
hundreds of files a `--prune` pass that lists unreferenced views will earn its
keep.

## 4. The design that removes the duplication

Offered as a direction, not a demand. It follows from §2: if the duplication is
the problem, then the fix is to have **one** piece of code produce both the
picture and the page.

In documentation mode, let `msm.view()` do what it says — build the view from the
system the notebook already has — and then export it instead of displaying it:

```python
def view(molecular_system=None, selection='all', ...):
    if _static_docs_mode():
        from molsysviewer import new_view
        import molsysviewer as msv

        view = new_view(molecular_system, selection=selection, ...)
        target = _view_path_for_this_call()          # deterministic, see below
        view.export.html(str(target), shared_runtime=str(_static_dir()))
        return msv.tools.embed_iframe(str(target), path=_notebook_path())

    return new_view(molecular_system, selection=selection, ...)
```

What this deletes:

- **the generation scripts** — the tutorial cell *is* the generator, so the
  picture cannot disagree with the code that produced it;
- **the hidden cells** — nothing to declare, nothing to forget, nothing to keep
  in sync;
- **the stack traversal** — no variable to find in a caller frame;
- **the cliff** — the other 112 notebooks work unmigrated, because there is
  nothing to migrate;
- **the `nb_path` inference** — `nbconvert` runs each notebook with the working
  directory set to that notebook's folder, so the notebook's location is
  `Path.cwd()`, known exactly rather than guessed.

What it needs:

- **a deterministic view path**, so re-running a notebook overwrites rather than
  accumulates. The notebook's path relative to the docs root plus a per-notebook
  call counter is enough: `_static/views/user/tools/get_dihedral_angles-1.html`.
  Stable across runs, unique across the corpus, and it says where it came from;
- **execution cost**: each `msm.view()` in doc mode now exports an HTML.
  `export.html` is entirely Python-side — no browser, no kernel round trip — so
  the cost is building the scene projection and writing 150–250 KB. Their
  incremental machinery (`.nbconvert.last_run` against mtime and commit time)
  already limits this to notebooks that changed, which is the right granularity:
  **a view is an output of its notebook, regenerated when its notebook changes.**

What it costs, stated plainly:

- **views can no longer be regenerated without executing the notebook.** Today a
  script can be re-run alone; under this design, refreshing a view means
  re-executing its notebook. For a MolSysViewer upgrade that touches every view,
  that is a full pre-execution pass — hours, on their corpus, though it is the
  same pass they already run when notebooks change;
- **a view that needs setup the tutorial does not show** — a specific camera, a
  representation chosen for the figure — has nowhere to live. The generation
  script was also an escape hatch for that. It can be kept for those cases, as an
  exception rather than the rule;
- **less control over which notebooks produce views.** Every `msm.view()` becomes
  a file. On 138 notebooks that is likely several hundred views, where today it
  is a curated set.

The trade is: correctness by construction, paid for with execution time and less
curation. Our judgement is that the trade is worth it at 138 notebooks, and
obviously worth it at 500 — but it is theirs to make, and the escape hatch keeps
the current design available where it is genuinely needed.

## 5. What is ours to fix, not theirs

Two things in this pipeline are limits of MolSysViewer, not of MolSysMT's design,
and they will hit them either way:

1. **A view exported from a script has no camera framing.** Measured: `camera.zoom()`
   does not survive an export, and a script-generated export carries no camera
   snapshot at all. This is their proposal
   [`tight_initial_camera_framing_for_exported_views.md`](tight_initial_camera_framing_for_exported_views.md),
   and the measurement moves the fix into the runtime rather than the export.
2. **An exported view does not follow the host page's light/dark theme.** Their
   [`dark_light_theme_synchronization_and_transparent_canvas.md`](dark_light_theme_synchronization_and_transparent_canvas.md).

We are treating both as one piece of work, because they collide on the same
export signature and the same moment in the runtime's boot, and because they are
the same question: *an exported view should adapt to the frame it lands in.*

## 6. Summary

- The pilot is correct and the policies around it are the right ones.
- The one structural weakness is that the code shown and the code that produced
  the picture are two different pieces of code, with nothing checking they agree.
  At one notebook it is invisible; at 138 it is a matter of time.
- The migration as currently designed is all-or-nothing per notebook, and 112
  notebooks are waiting on it.
- Letting the tutorial cell generate its own view removes the duplication, the
  hidden cells, the stack traversal and the cliff, at the price of execution time
  and curation.
- Two of their friction points are ours to fix and are already queued.
