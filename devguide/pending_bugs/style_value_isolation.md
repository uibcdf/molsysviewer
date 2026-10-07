---
summary: Style parameter dictionaries alias inputs, registries and global builtins
issue: uibcdf/molsysviewer#149
status: partial
opened: 2026-10-03
closed:
severity: medium
verification: measured
area: [styles, state]
guard: tests/test_design_review_closure.py::test_styles_are_detached_at_input_registry_and_builtin_boundaries
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Style parameter dictionaries alias inputs, registries and global builtins

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
for this follow-up remains pending. No published package is replaced by this
source correction.
