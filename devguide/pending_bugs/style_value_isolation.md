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
