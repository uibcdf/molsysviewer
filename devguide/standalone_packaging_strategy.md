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

This option now needs to be split into two more concrete variants.

#### Option A1. Conda-native recipe using standard package names

This would mean shipping a conda-native Qt/PySide6/WebEngine stack under the
usual names expected by the ecosystem.

Pros:

- cleanest user story
- closest to the normal conda-forge/UIBCDF packaging model
- no special naming in MolSysViewer runtime or install docs

Current issue:

- it implicitly promises that the stack is a safe substitute for the standard
  Qt/PySide6 route in the rest of the supported environment
- version drift becomes harder to control:
  - a later solver choice may replace one curated piece with a standard one
  - or pull the environment toward a newer upstream stack before the
    standalone host has been revalidated there
- this is attractive only if UIBCDF is willing to stand behind that stack as a
  broader ecosystem-compatible substitute, not just as a standalone enabler

#### Option A2. Conda-native standalone runtime with specific package names

This would mean shipping a curated Qt/WebEngine runtime in the UIBCDF channel
with package names that make its scope explicit and keep it isolated from the
standard PySide6 route.

Pros:

- lowers the risk of colliding with standard conda-forge Qt/PySide6 usage
- lowers pressure to promise broader equivalence than the standalone host
  actually needs
- gives tighter control over version drift and solver upgrades
- makes it easier to treat the solution as provisional and replaceable later

Current issue:

- the standalone stack becomes more clearly product-specific
- some packaging/runtime indirection may be needed in MolSysViewer when that
  runtime is present
- migration back to a future upstream standard route would still require a
  cleanup pass

Current reading:

- if UIBCDF needs to cover the Qt/WebEngine gap temporarily before conda-forge
  offers a satisfactory route, A2 currently looks safer than A1
- A1 only becomes preferable if the team is willing to maintain and validate
  the Qt/PySide6 stack as a broadly compatible substitute for the normal
  ecosystem path

#### A2 naming direction

If A2 is pursued, the package naming should stay close to the standard stack
and differ by a suffix rather than by a completely different product name.

Preferred direction:

- keep the upstream/root identity visible
- append a suffix that makes the scope explicit

Examples of the shape, not final names:

- `pyside6-standalone`
- `qt6-webengine-standalone`
- `shiboken6-standalone`

Why this is preferable to a totally different name:

- it stays legible to maintainers
- it keeps the future migration path back toward upstream naming clearer
- it still avoids pretending that the package is the standard ecosystem route

What the suffix should communicate:

- standalone/runtime-scoped
- UIBCDF-curated
- provisional if upstream later becomes sufficient

What it should avoid:

- branding-heavy names unrelated to Qt/PySide6
- names that suggest a fully general replacement for the standard packages
- names so different that later cleanup/migration becomes harder to read

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

1. treat the Qt host itself as materially sufficient and stop polishing it by
   inertia
2. keep the supported standalone environment recipe explicit
3. evaluate whether `1.0.0` can land on a conda-native route before accepting a
   hybrid fallback
4. inside that conda-native evaluation, distinguish explicitly between:
   - A1: standard package names
   - A2: standalone-specific package names
5. only fall back to a hybrid or more app-like route if the conda-native path
   cannot be made supportable in time

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

## Current Recommendation

For the current decision point:

- the desirable final direction remains a conda-native route
- if UIBCDF must temporarily cover the Qt/WebEngine gap itself, the safer
  provisional form currently looks like:
  - A2: a standalone-specific curated runtime in the UIBCDF channel
- that recommendation is driven by:
  - lower collision risk with standard conda-forge Qt/PySide6 environments
  - lower pressure to promise broad ecosystem equivalence too early
  - tighter control over version drift while the stack is still provisional

This should still be treated as a provisional recommendation, not as a final
packaging commitment.

The current naming preference inside that provisional recommendation is:

- if A2 is chosen, prefer a suffix-based naming scheme over a completely new
  root package name

## Minimal Addon-First Hypothesis

The latest environment comparison now suggests a narrower first attempt than a
full Qt/PySide6 fork.

Observed in the restored conda-forge environment:

- `pyside6` imports correctly
- `qt6-main` is present
- `PySide6.QtWebEngineWidgets` is missing
- no `QtWebEngine*` artifacts are present inside `site-packages/PySide6`

Observed in the working pip-based environment:

- `QtWebEngineCore.abi3.so`
- `QtWebEngineWidgets.abi3.so`
- `QtWebEngineQuick.abi3.so`
- `Qt/libexec/QtWebEngineProcess`
- `Qt/qml/QtWebEngine`
- `Qt/resources/qtwebengine*.pak`
- `Qt/translations/qtwebengine_locales`
- `Qt/translations/qtwebengine_*`

Upstream `pyside-setup` packaging also treats that same group as the
`QtWebEngineCore` / `QtWebEngineWidgets` / `QtWebEngineQuick` slice.

This makes the following first experiment plausible:

- try a minimal WebEngine add-on package first
- only fork more of the Qt/PySide6 stack if that first attempt proves
  insufficient

### Minimal addon contents

The first add-on attempt should aim to provide at least:

- `PySide6/QtWebEngineCore.abi3.so`
- `PySide6/QtWebEngineCore.pyi`
- `PySide6/QtWebEngineWidgets.abi3.so`
- `PySide6/QtWebEngineWidgets.pyi`
- `PySide6/QtWebEngineQuick.abi3.so`
- `PySide6/QtWebEngineQuick.pyi`
- `PySide6/Qt/libexec/QtWebEngineProcess`
- `PySide6/Qt/qml/QtWebEngine`
- `PySide6/Qt/resources/qtwebengine*.pak`
- `PySide6/Qt/translations/qtwebengine_locales`
- `PySide6/Qt/translations/qtwebengine_*`

### Provisional naming direction for the addon-first attempt

If this add-on route is attempted before a broader A2 fork, the current naming
preference is:

- keep the root identity visible
- use a suffix

Example shape:

- `pyside6-webengine-uibcdf`

This is still only a working hypothesis, not yet a packaging commitment.
