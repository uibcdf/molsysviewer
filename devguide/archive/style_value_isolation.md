---
summary: Style parameter dictionaries alias inputs, registries and global builtins
issue: uibcdf/molsysviewer#149
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: medium
verification: reproduced
area: [styles, state]
guard: tests/test_design_review_closure.py::test_styles_are_detached_at_input_registry_and_builtin_boundaries
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Style parameter dictionaries alias inputs, registries and global builtins

**Resolved — 2026-10-07:** the remaining applied nested recipe alias is corrected
in `027374ed`, with formatted guard/docs checkpoint `bd824ea1`. Installed
development-wheel and exact hosted-source guards pass. This follow-up has not
replaced the published 0.24.0 package. Earlier dated sections retain their scope.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

Frozen Style instances retain mutable parameter dictionaries. Styles.add/get/get_builtin return or retain the same objects, allowing callers to mutate a registry or the global builtin catalog through a returned value.

## How

Inspected styles.py constructor and registry/builtin/focus accessors. Existing detached info/records guards do not cover these object boundaries.

## Why

Style recipes should behave as values and remain isolated across viewers. Preserve familiar dictionary parameter access while copying at ownership boundaries.

## Acceptance

Guards for nested input mutation, returned registry values and both scene/focus builtins; applying a style must not expose shared mutable configuration.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

Style copies nested input parameters; registry add/get and scene/focus builtin getters return detached values. Applying/focusing copies recipes at the ownership boundary. params remains an editable dictionary on the caller-owned value; changing a returned recipe does not modify another viewer or the stored registry.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).

## Remaining applied-recipe boundary — 2026-10-07

Review finds a boundary not covered by the original scalar applied-style check.
Styles.apply copies its input, then expands that copy's params into Whole and
returns the same Style. Whole retains the nested dictionaries received through
keyword arguments. Mutating the returned nested color-theme recipe therefore
changes the canonical scene without applying a new recipe. A real dialanine
probe observes `element-symbol` becoming `caller-mutation` in styles.current();
the original input remains detached. The published 0.24.0 baseline still has
this remaining boundary; its earlier qualification does not prove it corrected.

Styles.apply now transfers a deep copy of params to Whole, keeping its returned
recipe caller-owned. The existing guard additionally mutates both the nested
theme and a leaf in its params, then checks unchanged canonical state, current
style and registered recipe. Exact-source and installed-candidate qualification
for this follow-up is completed below. No published package is replaced by this
source correction.

## Remaining-boundary qualification and closure — 2026-10-07

A fresh isolated probe reproduces the remaining alias in the original promoted
Viewer 0.24.0 file: changing the returned nested theme changes styles.current(),
while the original input recipe remains unchanged. That published defect is
preserved explicitly; initial registry/scalar guards did not cover it.

The reviewed follow-up commit `bd824ea146b678dce763bb88a39e332227f7beab` carries
the one-line ownership-copy fix from `027374ed` and the strengthened existing
guard. A controlled development wheel `0.24.0+19.gbd824ea1.dirty` has matching
Python/runtime versions and exact style/plot source bytes. Its dirty suffix
records generated runtime refresh in the isolated packaging copy. It passes
pip check and all 13 real-system design guards against the original MolSysMT
0.23.0 ABI3 build-0 file promoted unchanged. Isolated imports are verified
before/after collection; the original public qualification environment is preserved.

Exact-source pair `37685753081` passes on all three Python 3.14 hosts with fixed
MolSysMT `46ef28eb`: Linux 2,876 passed/27 skipped, macOS 2,849/54, Windows
2,850/53, zero failures/errors. Linux additionally passes 39 core suites and
25 notebooks. Independent core `37685752799` passes 39/39. Policy `37685753835`
and independent documented notebooks pass. Standard CI `37685752885` passes
six scientific Python 3.11–3.13 cells; its experimental Qt startup failure
remains under uibcdf/molsysviewer#35. No complete standard-CI pass is claimed.

The first follow-up policy check `37685072608` fails on formatting the new
dictionary assertion; line splitting corrects it without a behavior change.
The once-run local full suite also retains failure: 22 socket/browser/Qt cases
cannot run successfully in this restricted executor, alongside 2,860 passed and
23 skipped cases. Native tracebacks/logs distinguish this execution limit from
the successful hosted gate. Neither failed verdict is discarded or called green.

The guard now mutates both the returned nested theme and its nested params leaf,
then checks unchanged canonical state, current style and registered recipe.
The public guide explains explicit recipe editing/application; its new example
executes against the installed public pair and Sphinx passes with warnings as
errors. [Exact record and preserved verdicts](../styles_plot_closure_20261007.json).

This source correction is queued for the next qualified release. Final 1.0
artifact/publication qualification remains in the release plan; the published
0.24.0 tag and files stay immutable.
