# Standalone Packaging Strategy

This document records the packaging/distribution position for the standalone host.

It should be read together with:

- `devguide/standalone_host_plan.md`
- `devguide/archive/standalone_qt_prototype_plan.md`
- `devguide/standalone_supported_environment.md`

## Decision Made (2026-04-04)

**Option A2 was chosen and is complete.** A curated, source-built, suffix-named
conda family is now published in the `uibcdf` channel:

| Package |
|---------|
| `shiboken6-uibcdf` |
| `pyside6-essentials-uibcdf` |
| `pyside6-addons-uibcdf` |
| `qt6-positioning-uibcdf` |
| `qt6-webengine-uibcdf` |

**Build numbers deliberately live in one place only:**
[`standalone_supported_environment.md`](standalone_supported_environment.md),
which is the supported recipe. *(This table used to pin `6.9.2=*_3` for all
three binding packages and drifted: `pyside6-addons-uibcdf` was rebuilt past it,
and a reader following this table would have installed a build too old to expose
`QWebEngineUrlScheme.setFlags`, which MolSysViewer needs for fetchable custom
schemes. Two documents stating the same build numbers with nothing forcing them
to agree is the same failure this repo has hit in digesters, in the Qt action
manifest and in the popup summaries.)*

The Python import namespace is `PySide6_uibcdf` / `shiboken6_uibcdf`.
`QFileDialog`, `QMessageBox`, `QWebEngineView` all work correctly.
`molsysviewer.standalone_qt` imports from `PySide6_uibcdf` directly.

The rest of this document is the **historical investigation record** that led
to this decision. It is kept as context for future decisions (e.g. 6.10.x,
multi-platform) but should not be read as open questions.

---

## Historical Record: Investigation and Decision Process

### Former Current Position

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

**Checked 2026-08-06: the conditions below appear met, and the decision they gate
has not been made.** The Qt host is recorded as *technically complete and
packaging-validated* in
[`standalone_supported_environment.md`](standalone_supported_environment.md),
whose conda-native recipe names five packages — and all five are on the `uibcdf`
channel at `6.9.2` with builds at or above the ones it requires
(`shiboken6-uibcdf _4`, `pyside6-essentials-uibcdf _4`, `pyside6-addons-uibcdf _6`,
`qt6-positioning-uibcdf _1`, `qt6-webengine-uibcdf _2`). So the recipe is
installable without compiling, which was the second condition.

What remains is the third one — whether the open question is now distribution
polish rather than host viability — and that is a judgement, not a measurement.
Whoever makes it should start from
`standalone_supported_environment.md`'s *What Still Remains Open*, which lists
the three surviving questions: conda-only or conda+pip, how the recipe is
distributed, and environment-driven versus app-like release packaging.

*Recorded because a decision rule ages like any other deferral: its conditions
were written to be re-read, and nothing re-reads them.*

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

## Repo Split

The packaging investigation is now split more cleanly by responsibility.

`molsysviewer` should keep:

- the evidence trail
- the host-side integration reading
- the packaging rationale in `devguide`

The actual experimental package work should move into sibling repos:

- `../shiboken6-uibcdf`
- `../pyside6-essentials-uibcdf`
- `../pyside6-addons-uibcdf`

This keeps the Qt-family packaging logic out of the main MolSysViewer repo
while preserving the reasoning that led to that split.

## Minimal Addon-First Hypothesis

The latest environment comparison now suggests a narrower first attempt than a
full Qt/PySide6 fork.

Observed in the restored conda-forge environment:

- `pyside6` imports correctly
- `qt6-main` is present
- `PySide6.QtWebEngineWidgets` is missing
- no `QtWebEngine*` artifacts are present inside `site-packages/PySide6`
- no WebEngine runtime/resources are present under `site-packages/PySide6/Qt`

Observed in the working pip-based environment:

- `QtWebEngineCore.abi3.so`
- `QtWebEngineWidgets.abi3.so`
- `QtWebEngineQuick.abi3.so`
- `Qt/lib/libQt6WebEngineCore.so.6`
- `Qt/lib/libQt6WebEngineWidgets.so.6`
- `Qt/lib/libQt6WebEngineQuick.so.6`
- `Qt/lib/libQt6WebEngineQuickDelegatesQml.so.6`
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
- `PySide6/Qt/lib/libQt6WebEngineCore.so.6`
- `PySide6/Qt/lib/libQt6WebEngineWidgets.so.6`
- `PySide6/Qt/lib/libQt6WebEngineQuick.so.6`
- `PySide6/Qt/lib/libQt6WebEngineQuickDelegatesQml.so.6`
- `PySide6/Qt/libexec/QtWebEngineProcess`
- `PySide6/Qt/qml/QtWebEngine`
  - including `ControlsDelegates`
  - including the QML WebEngine plugins
- `PySide6/Qt/resources/qtwebengine*.pak`
- `PySide6/Qt/translations/qtwebengine_locales`
- `PySide6/Qt/translations/qtwebengine_*`

That is now the minimum viable Linux inventory hypothesis for the first
experiment. It also suggests the add-on is unlikely to work if it ships only
the top-level PySide6 `.abi3.so` modules without the matching native Qt
WebEngine runtime under `PySide6/Qt`.

### First scratch-overlay result

The first reversible overlay experiment in `sandbox/` was informative:

- adding only the WebEngine slice made `PySide6.QtWebEngineWidgets`
  discoverable
- loading then failed first on missing `abi3` bridge libraries:
  - `libpyside6.abi3.so.6.9`
  - `libshiboken6.abi3.so.6.9`
- after adding those, loading then failed on:
  - `libQt6Positioning.so.6`
- inspection of the validated `pip` environment showed that both:
  - `QtPositioning`
  - and the WebEngine runtime
  belong to `PySide6_Addons`
- after extending the overlay with that first Addons slice, the process moved
  past the earlier loader errors but segfaulted

Current reading after that experiment:

- a pure `webengine-only` add-on is probably too narrow
- a naive mix of:
  - conda-forge base `pyside6`
  - plus copied `pip` Addons files
  is not stable enough to treat as the packaging boundary
- the most plausible next boundary is now:
  - an ABI-aligned `PySide6_Addons`-style package
  - and possibly the matching bridge/runtime pieces it expects
- this is still narrower than forking the entire Qt/PySide6 stack, but broader
  than a tiny WebEngine-only drop-in

### Addons-only overlay result

A second scratch overlay then copied the full `PySide6_Addons` file set from
the validated `pip` environment onto the current conda-forge base, plus the two
`abi3` bridge libraries:

- `PySide6/libpyside6.abi3.so.6.9`
- `shiboken6/libshiboken6.abi3.so.6.9`

Result:

- `QtWebEngineWidgets` still did not become stably usable
- the process segfaulted during import / `QWebEngineView` construction

What that now means:

- the packaging boundary does continue to point toward `PySide6_Addons`
- but the result is strong evidence that:
  - a manual overlay of `pip` Addons on top of the current conda-forge
    `pyside6` base is not ABI-safe enough
- the likely next serious route is therefore:
  - a curated `PySide6_Addons`-style package built/aligned for the target conda
    base
  - not a direct file transplant between the current two environments

### Runtime boundary after the pip-family comparison

The next comparison step answered a more structural question:

- can the natural Qt-for-Python family
  - `shiboken6`
  - `PySide6_Essentials`
  - `PySide6_Addons`
  sit cleanly on top of `qt6-main` from conda-forge?
- or does that family effectively carry its own Qt runtime?

Current reading:

- the validated `pip` family appears to carry and prefer its own Qt runtime
- `PySide6_Essentials` resolves core Qt from:
  - `site-packages/PySide6/Qt/lib`
  not from `$CONDA_PREFIX/lib`
- `PySide6_Addons` does the same for:
  - `QtPositioning`
  - `QtWebChannel`
  - `QtWebEngine*`
  - `QtWebEngineProcess`
  - WebEngine QML/resources/translations
- the `pip` family also carries its own ICU runtime:
  - `libicui18n.so.73`
  - `libicuuc.so.73`
  - `libicudata.so.73`
- the current conda-forge base environment uses ICU 75 in `$CONDA_PREFIX/lib`

Implication:

- the provisional standalone route should no longer be modeled as:
  - a `qt6-main`-based conda-forge runtime plus a few extra Python bindings
- it is better modeled as:
  - a self-aligned Qt-for-Python family
  - with its own matching Qt runtime payload

That does not yet prove the final UIBCDF packaging shape.
But it does make one conclusion much stronger:

- a clean provisional route is more likely to look like:
  - `shiboken6-uibcdf`
  - `pyside6-essentials-uibcdf`
  - `pyside6-addons-uibcdf`
- and less likely to look like:
  - `qt6-main` from conda-forge plus a thin WebEngine extension layer

### Provisional naming direction for the addon-first attempt

If this add-on route is attempted before a broader A2 fork, the current naming
preference is:

- keep the root identity visible
- use a suffix

Example shape:

- `pyside6-webengine-uibcdf`

This is still only a working hypothesis, not yet a packaging commitment.
