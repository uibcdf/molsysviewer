# Standalone Packaging Strategy

This document records the current packaging/distribution position for the final
standalone host.

It should be read together with:

- `devguide/standalone_host_plan.md`
- `devguide/standalone_qt_prototype_plan.md`
- `devguide/standalone_supported_environment.md`

## Current Position

The host direction is now much clearer than the packaging direction.

What is already established:

- the preferred final host direction remains:
  - `PySide6 + Qt WebEngine`
- the host can already run as a real Qt shell
- the supported prototype/development recipe is explicit

What is **not** yet fixed:

- final conda-only packaging
- final hybrid conda+pip recipe
- whether release distribution should remain environment-driven
  or evolve toward a more app-like installer/distribution path

## What Is Already Good Enough

At this stage, development should continue on top of:

- the shared runtime/workbench already validated in notebook/popup/browser
- the Qt host already validated as a thin shell
- the supported standalone spike environment recipe

That means packaging uncertainty should not block host improvement now.

## What Must Remain True

The final standalone should still be:

- one MolSysViewer runtime
- one workbench model
- one add-on/workspace model
- one environment story that is explicit and supportable

Packaging must not turn standalone into:

- a separate product
- a forked runtime
- or a second extension system

## Packaging Options Still Open

### Option A. Supported conda-only recipe

Pros:

- consistent with the broader ecosystem story
- cleanest story for users already living in conda environments

Current issue:

- the tested Qt WebEngine path was not yet reliable enough there

### Option B. Supported conda+pip recipe

Pros:

- already has a validated prototype path
- pragmatic and unblocker-friendly

Current issue:

- must be made explicit and supportable, not left as an ad hoc workaround

### Option C. More app-like distribution later

Examples could include:

- curated environment installers
- a more application-shaped packaging path

Pros:

- stronger end-user story

Current issue:

- premature until the host and supported environment recipe are both stable

## Recommended Near-Term Strategy

For the current pre-`1.0.0` stage:

1. keep improving the thin Qt host
2. keep the supported standalone environment recipe explicit
3. delay final packaging closure until the host itself feels sufficiently
   finished
4. only then decide whether `1.0.0` should ship on:
   - a supported conda-only recipe
   - a supported conda+pip recipe
   - or a more app-like distribution wrapper

## Decision Rule

The next standalone packaging decision should be made when:

- the Qt host no longer feels prototype-fragile
- the supported environment recipe is reproducible enough for routine QA
- the main remaining uncertainty is user-facing installation/distribution
  polish, not host viability

Until then, standalone packaging should be treated as:

- important
- explicit
- but not yet the driver of implementation priorities
