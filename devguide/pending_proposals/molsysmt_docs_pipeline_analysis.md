---
summary: MolSysMT's documentation pipeline read at the scale it is about to reach.
issue: uibcdf/molsysviewer#41
status: open
opened: 2026-08-04
closed:
verification: measured
area: [docs, molsysmt]
guard:
normative:
blocked_by: []
supersedes: []
---

# MolSysMT's documentation pipeline, read at the scale it is about to reach

**Status:** analysis, 2026-08-04. Offered, not requested — MolSysMT may already
have most of this in hand. Companion to
[`molsysmt_adoption_response_2026_08.md`](../archive/molsysmt_adoption_response_2026_08.md),
which answers their report point by point. This document asks a different
question.

**The question.** The new embedding scheme is implemented in **one** notebook,
`docs/index.ipynb`, as a trial. It works. The next step is applying it to the
rest. Measured in their tree today: **69 notebooks call `msm.view()` from code
cells**, and **13** carry a target variable (`molsysviewer_htmlfile` or the
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
code. It is not hypothetical at 69 notebooks and several years — it is the
default outcome of two files that must be edited together and are not checked
against each other.

The pilot does not show this because one notebook edited last week is trivially
in sync.

## 3. What multiplying by five costs

| | pilot (1 notebook) | migrated (69) |
|---|---|---|
| Generation scripts | 1 | one per view, hundreds |
| Hidden cells | 1 | one per view |
| Committed view HTML | 149 KB | 34 KB to 18 MB each, depending on what is viewed (§4) |
| Files to edit to change one figure | 2 | 2, every time, forever |
| Notebooks that fail pre-execution until migrated | 0 | 56 today |

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

## 4. Measured: the time is cheap, the storage is not

The first version of this document proposed letting the tutorial cell generate
its own view, which would delete the duplication by construction. Diego pushed
back — separate generation gives control and keeps rebuilds light — and asked for
numbers instead of arguments. The numbers settle it against the proposal.

**Marginal cost of adding an export to a notebook run** (1BRS, their own example):

| step | time |
|---|---|
| `import molsysmt` | 0.45 s |
| `msm.convert(1brs, ...)` — paid by the notebook either way | 4.55 s |
| `msm.view(...)` | 1.30 s |
| `export.html(...)` | 0.34 s |
| **marginal cost of the proposal** | **1.64 s** |

And end to end: their generation script takes **7.66 s**; executing
`docs/index.ipynb` through `nbconvert` takes **12.52 s**. So per-run, generating
views from the notebook is not expensive. On time alone the proposal is
affordable.

**Then the size of the artifact, which is where it dies:**

| view | export time | HTML |
|---|---|---|
| dialanine (one structure) | 0.30 s | **34 KB** |
| 1BRS, one molecule | 0.34 s | **146 KB** |
| pentalanine **trajectory** | 2.43 s | **17.9 MB** |

An exported view carries its scene, and a scene with a trajectory carries every
frame. One trajectory view is 18 MB of committed, regenerated-on-every-edit text
— more than a hundred times the static one beside it, and there is no way to know
which kind a given `msm.view()` call is without looking at what it was handed.

That is the argument for keeping generation explicit, and it is a better argument
than the one usually given. It is not about rebuild speed. **It is that only a
person can decide whether a particular view deserves to be an 18 MB interactive
artifact, a 146 KB one, or a static image** — and a scheme that turns every
`msm.view()` in 69 notebooks into a file takes that decision away.

**So: keep the generation scripts.** The proposal is withdrawn.

### What to do about the duplication instead

The defect in §2 is real and survives the withdrawal: two files that must agree,
with nothing checking that they do. But it does not need an architecture to fix,
only a check.

The pairing is already implicit — `1BRS_molecule_index_zero.py` produces
`1BRS_molecule_index_zero.html`, which the hidden cell names. So a test can walk
it: for every notebook cell whose hidden cell declares a view, find the
generation script of the same stem, and compare the `msm.view(...)` call in both.
Normalise whitespace, fail loudly on difference.

```python
def test_every_embedded_view_matches_the_call_shown_beside_it():
    for notebook, htmlfile, shown_call in _tutorial_view_calls():
        script = GENERATED_VIEWS / f"{Path(htmlfile).stem}.py"
        assert _view_call_in(script) == shown_call, (
            f"{notebook} shows a call that did not produce the picture beside it"
        )
```

It will not catch everything: a system built differently in the two files still
slips through. It catches the case that actually happens — someone edits the
selection, the representation or the system in the tutorial and forgets the
script — and it costs an afternoon rather than a migration.

The stronger version, if it is ever worth it: have the generation script record
the call it made (a sidecar, or a comment in the exported HTML) and compare that
against the notebook, so the check no longer depends on the two files looking
alike.

## 4b. The hidden cell stays, and here is why it earns its place

Asked on the same day: could the hidden cell be avoided, so the notebook holds
only the tutorial line? Three answers were considered and the question *"what if
one notebook has several `msm.view()` calls?"* decided between them.

Measured in their source notebooks (excluding `_build` copies):

| | notebooks |
|---|---|
| call `msm.view()` from code cells | 69 |
| of those, more than once | 25 |
| of those, with two **textually identical** calls | **15** |

That last row is the pattern *view → change the system → view again*:
`set_dihedral_angles`, `shift_dihedral_angles`, `move_away`, `make_bioassembly`.
The two calls are the same characters; only the system's content differs between
them.

The options, against that:

- **Derive the view's name from the call itself** — a key built from the system's
  fingerprint plus `selection`, `structure_indices`, `syntax`, registered by the
  generation script. Elegant: it removes the hidden cell *and* makes drift
  impossible, because a changed tutorial call looks for a name that does not
  exist. **It dies on the row above.** Two identical calls give one key, and
  distinguishing them needs a content hash of the coordinates — which would have
  to come out bit-identical from the notebook and from a generation script that
  builds the system with different code. That is not a promise anyone can keep,
  and when it broke it would break constantly.
- **A cell tag** (`"tags": ["view:1BRS_molecule_index_zero"]`) instead of a hidden
  cell. Survives the multi-view case, puts the declaration where Jupyter users
  expect it, and removes a code cell that teaches nothing. Costs a small nbconvert
  preprocessor, and does **not** fix drift. A real option if the hidden cell ever
  becomes a nuisance.
- **Positional naming** (`<notebook>-<n>.html`). Rejected: inserting a view early
  silently renumbers every later one, so an editing slip becomes a page showing
  one call's code beside another call's picture.

**Conclusion: leave it as it is.** The hidden cell is an explicit, per-call
declaration that survives several views in one notebook, several *identical*
views in one notebook, and reordering — which is exactly the set of cases the
alternatives fail. Its cost is one invisible line per view. Diego's judgement on
2026-08-04, and the measurements agree with it.

One improvement is worth taking regardless of this decision, because it is
independent of how the pairing is declared: **`execute_notebooks.py` already
knows which notebook it is running**, since it spawns one subprocess per
notebook. Passing that down —

```python
env["MSM_VIEWS_FROM_HTML_FILES"] = "True"
env["MSM_DOCS_NOTEBOOK"] = str(notebook_path)
```

— lets the adapter stop inferring its own location from `f_locals.get('__file__',
'index.ipynb')`, which is the one thing in the pilot that is right only for
`docs/index.ipynb`. See §2.1 of the reply.

## 5. What is ours to fix, not theirs

Two things in this pipeline are limits of MolSysViewer, not of MolSysMT's design,
and they will hit them either way:

1. **A view exported from a script has no camera framing.** Measured: `camera.zoom()`
   does not survive an export, and a script-generated export carries no camera
   snapshot at all. This is their proposal
   [`tight_initial_camera_framing_for_exported_views.md`](../archive/tight_initial_camera_framing_for_exported_views.md),
   and the measurement moves the fix into the runtime rather than the export.
2. **An exported view does not follow the host page's light/dark theme.** Their
   [`dark_light_theme_synchronization_and_transparent_canvas.md`](../archive/dark_light_theme_synchronization_and_transparent_canvas.md)
   — delivered 2026-08-05 as `export.html(background=...)`.

We are treating both as one piece of work, because they collide on the same
export signature and the same moment in the runtime's boot, and because they are
the same question: *an exported view should adapt to the frame it lands in.*

## 6. Summary

- The pilot is correct and the policies around it are the right ones.
- The one structural weakness is that the code shown and the code that produced
  the picture are two different pieces of code, with nothing checking they agree.
  At one notebook it is invisible; at 69 it is a matter of time.
- The migration as currently designed is all-or-nothing per notebook, and 56
  notebooks are waiting on it. Worth deciding on purpose rather than discovering.
- **Generating views from the notebooks was proposed and withdrawn on
  measurement.** The time is cheap (1.64 s per view) but the artifact is not: a
  trajectory view is 17.9 MB against 146 KB for a static one, and only a person
  can decide which a given call deserves to be. Keep the generation scripts.
- Fix the duplication with a check that the two copies agree, not with an
  architecture. An afternoon instead of a migration.
- Two of their friction points are ours to fix and are already queued: framing a
  view exported from a script, and following the host page's theme.
