# Automating the Qt render check on a GPU runner

**Status:** post-1.0. Infrastructure, not code.

## Why this is not a 1.0 gate

The render gate itself is **closed**. The standalone was launched on a real GPU
(aleph, 2026-07-04) and renders: dialanine in 3D, mouse zoom and rotation, native
context menu. See
[`../../standalone_qt_ci_and_gl_decisions.md`](../../standalone_qt_ci_and_gl_decisions.md),
whose Decision 1 already classifies this work as **level 2: a separate,
non-blocking job**. Scheduling it after 1.0 follows that decision rather than
reopening it.

What is missing is not confidence that Qt renders. It is a machine that can
prove it again automatically, so a future regression is caught by CI instead of
by a person.

## What it needs

**Infrastructure (not something the repository can provide):**

1. A machine with a working GPU **and a graphical session**. This is the part
   that is easy to get wrong: the test needs a real WebGL context, so a GPU
   alone is not enough. A runner started as a headless service with no X11
   session lands back in the software-GL problem that Decision 1 already ruled
   out. It has to run inside an active graphical session.
2. Registration as a self-hosted runner in the `uibcdf` organization, labelled
   so a workflow can target it (`self-hosted`, `gpu`).
3. A decision on the conda stack: preinstalled on the runner (fast, drifts) or
   built per run (slow, reproducible). For an infrequent non-blocking job,
   building per run is the safer trade.

**Workflow (a few lines, once the runner exists):**

```yaml
runs-on: [self-hosted, gpu]
continue-on-error: true          # level 2 never blocks
env:
  MOLSYSVIEWER_QT_GPU_TEST: "1"
run: pytest tests/test_standalone.py -k full_render_gpu
```

No software-GL flags. With a real GPU the decision is explicit that it goes
straight through.

Still to decide: trigger (nightly plus manual is likely enough for a ~1 minute
test on a dedicated machine) and scope (running the whole `test_standalone.py`
on real GPU covers more than the render test alone, since the non-GL part
already runs in the ordinary CI).

## Do not retry Plan C

Mesa llvmpipe under `xvfb` was re-tried on 2026-07-31 and reproduced the
documented fragility: the render test passed when launched alone with one
specific flag combination and failed inside the full suite without it, with
`Could not create a WebGL rendering context`. That evidence is recorded in the
GL decisions document. A single passing run is not a refutation.

Also note that the docstring of `test_qt_live_model_full_render_gpu` recommends
`--use-gl=angle --use-angle=swiftshader`, but SwiftShader is **not** present in
the `PySide6_uibcdf` build, so those flags do not apply.

## Acceptance

- A non-blocking job renders the standalone on a real GPU and reports failure
  visibly.
- A regression in the Qt render path is found by CI, not by a person opening the
  application.
