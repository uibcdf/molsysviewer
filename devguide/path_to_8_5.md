# Path to 8.5

This document records an honest competitive assessment of MolSysViewer
and the concrete gaps that separate the current state (6.5/10) from a
convincing 1.0 release (8.5/10).

It is not a roadmap.
It is a gap document — what is missing and why it matters.

## Current competitive position

Scoring against the Jupyter/Python molecular viewer landscape (April 2026):

| Tool | Score | Notes |
|---|---|---|
| nglview | 7 | Standard today. Easy, adopted, but no reproducible state, limited overlays, stagnant. |
| py3Dmol | 5.5 | Popular for quick use. Shallow API, low ceiling. |
| MolSysViewer (now) | 6.5 | Architecturally superior to both. But pre-1.0, docs partial, no external users. |
| MolSysViewer (1.0 target) | 8.5 | Achievable without architectural changes. |

For context, general-purpose viewers:

| Tool | Score | Notes |
|---|---|---|
| Mol\* (web) | 9 | Best-in-class web structure renderer. MolSysViewer uses it internally. |
| PyMOL / ChimeraX | 8.5 | Professional desktop tools. Not Jupyter-native. |
| VMD | 7 | Indispensable for long MD trajectories but aging. |

## Why 6.5 and not higher today

The architecture is not the problem.
The reproducibility model, the shape overlay system, the add-on framework,
and the Mol*-backed rendering are all genuinely stronger than the
competition in the Jupyter space.

The gap is that none of this is visible in the first five minutes.

A scientist who tries nglview and MolSysViewer side by side for five
minutes will choose nglview because it works immediately and has examples
everywhere. The advantages of MolSysViewer become visible after five
months — when they need to reproduce a figure, orchestrate overlays, or
build a workflow that mixes analysis and visualization.

That is the right user to target. But it is also the hardest to reach
without documentation oriented toward real scientific cases.

## What must change to reach 8.5

The following gaps are listed in order of impact. None require
architectural changes.

### Gap 1: Scientific tutorials (highest impact)

**Current state**: API reference exists. Conceptual docs exist.
No end-to-end tutorials that show a scientist solving a real problem.

**What is needed**: 3-5 notebook-style tutorials that start from a real
scientific question and use MolSysViewer as the natural tool to answer it.
Good candidates:

- "Visualize a binding site and export a publication figure"
  (uses: load, regions, shapes, FigureSpec, export.html)
- "Compare two conformations of the same protein"
  (uses: load with mode="add", regions, displacement_vectors)
- "Annotate a pocket and measure key distances"
  (uses: pocket_surface, annotations, measurements, export)
- "Build a pharmacophore model and focus on features"
  (uses: pharmacophore_features, Shape.focus, export)
- "Replay a trajectory and capture key frames"
  (uses: set_structure, play/pause, export.image headless)

These tutorials should be the first thing a new user finds.
They should not be API showcases. They should answer a question
that a structural biologist or drug designer actually has.

**Why this matters**: nglview has 100+ example notebooks scattered
across the internet. MolSysViewer has none outside the UIBCDF ecosystem.
Adoption is driven by "I found a notebook that does what I need."

### Gap 2: First-contact onboarding

**Current state**: The relationship between MolSysViewer and MolSysMT is
architecturally clean but not explained at the entry point.
A user who lands on the project page does not immediately understand
the "MolSysMT is the universal adapter" model.

**What is needed**: A single short entry-point page (or README section)
that shows the complete flow from a PDB file / RDKit molecule /
MDAnalysis Universe to a visualization, in 10 lines of code.
Something like:

```python
import molsysmt as msm
import molsysviewer as msv

mol = msm.convert("1tsr.pdb", to_form="molsysmt.MolSys")
view = msv.new_view(mol)
view
```

That is the entire onboarding message: MolSysMT reads anything,
MolSysViewer shows it. Once that is clear, the richer API becomes
accessible.

**Why this matters**: the dependency on MolSysMT is a strength
(universal adapter), but it currently reads as a barrier because it is
not explained as such at the first entry point.

### Gap 3: E2E test coverage

**Current state**: one E2E path tested (region hide).
The project's core value proposition is reproducibility, and the
reproducibility pipeline has minimal automated end-to-end verification.

**What is needed**: at minimum, 5-8 E2E paths covering the mature
product stories:

- load → set representation → export HTML → verify replay
- load → add region → hide region → export → verify state
- load → add shape → Shape.focus → export image headless
- load → add annotation + measurement → export → replay
- load → export.html(mode='lite') → open in browser → verify render

These should be runnable in CI without a display (headless backends exist).

**Why this matters**: a viewer that claims reproducibility as its
differentiator but cannot automatically verify that claim is vulnerable.
One regression in the replay pipeline and the core value proposition
breaks silently.

### Gap 4: One real external add-on

**Current state**: the add-on system is real and tested with reference
templates. No real downstream team has built against it under real domain
pressure.

**What is needed**: ElasNetMT as a first real add-on.
Not a full integration — a minimal working slice:
- loads ElasNetMT results into the viewer
- shows displacement vectors or anisotropy ellipsoids
- uses the workspace panel host
- is documented as a real addon in the standards/ contract

This is the only way to know whether the add-on contract is actually
correct, and whether the overlay primitives that were built with ElasNetMT
in mind actually serve the domain.

**Why this matters**: the add-on system is currently an architecture
looking for users. One real add-on, however minimal, turns it into
evidence. Without it, the claim "MolSysViewer supports domain add-ons"
is a promise, not a fact.

### Gap 5: Standalone multiplataform

**Current state**: Linux standalone exists via custom PySide6/Qt build.
Mac and Windows are not supported. The installation story is complex
(custom conda channel, 5 packages).

**What is needed for 8.5**: at minimum, a documented and tested
path for Mac. Windows is a lower priority.

The complexity of the current Linux packaging approach is a long-term
technical debt. The right answer depends on whether upstream PySide6
eventually ships QtWebEngine reliably on conda-forge. Until then, the
standalone story is limited to Linux.

**Why this matters for the score**: a "standalone molecular viewer"
that only runs on Linux covers maybe 20% of the scientific computing
desktop. This limits the narrative of the product even for users who
only need Jupyter mode.

Note: the Jupyter widget mode works cross-platform without any of
this complexity. The standalone gap is real but does not affect the
primary usage path.

### Gap 6: Surface polish

**Current state**: the GroupStrip, context menu, and panel mode are
functional but not yet as smooth as nglview's simple interaction model.

**What is needed**: no major new features — just closing the known
rough edges in the mature surfaces:
- GroupStrip needs independent scroll per chain and a cleaner visual
  when many chains exist
- context menu actions need more consistent feedback (toast / status)
- first-load experience (empty viewer state) needs to feel less blank

**Why this matters**: this is the last gap because it is the one with
the least leverage. A well-documented tool with a slightly rough UX
gets adopted. A polished tool with no documentation does not.

## What does NOT need to change to reach 8.5

- The architecture. The message history / replay model is correct.
- The rendering engine. Mol* is the right choice and is already mature.
- The shape overlay system. The primitives are rich enough.
- The reproducibility model. It works. It just needs to be demonstrated.
- The MolSysMT integration. The "universal adapter" model is the right
  answer to the format compatibility question.
- The add-on contract. It may need small adjustments under real pressure
  but the current structure is sound.

## Summary

The 6.5 → 8.5 gap is not technical. It is:

1. **Tutorials** — show real scientific workflows, not API demos
2. **Onboarding** — make the MolSysMT+MolSysViewer duo obvious at first contact
3. **E2E tests** — verify the reproducibility claims automatically
4. **One real add-on** — prove the add-on system under real domain pressure
5. **Mac standalone** — widen the reach of the standalone story
6. **Surface polish** — close the known UX rough edges in mature surfaces

None of these require touching the architecture.
All of them require sustained attention to the user's first experience,
not continued investment in internal infrastructure.
