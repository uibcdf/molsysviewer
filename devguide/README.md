# Developer Guide

Welcome to the technical documentation for **MolSysViewer**. This guide is intended for developers who wish to contribute to the library or understand its inner workings.

## Source of Truth

For development work in this repository, `devguide/` is the source of truth.
The purpose of `devguide/checkpoints.md` is not to duplicate git history.
Git already records the historical sequence of changes.

`devguide/checkpoints.md` should instead be maintained as the current working
checkpoint for the next developer session. It should make clear:

- where we are now,
- what is already decided,
- what we think should happen next,
- why that is the right next step,
- and what criteria/invariants must be preserved.

## Contents

1. [**Architecture**](architecture.md)
   - The Python/JS bridge, Mol* integration, and messaging protocol.
2. [**Digestion and Dependencies**](digestion_and_dependencies.md)
   - Using ArgDigest for validation and DepDigest for environment robustness.
3. [**SMonitor Integration**](smonitor.md)
   - Diagnostics, catalog rules, and telemetry signals.
4. [**Interaction Overview**](interaction_overview.md)
   - Entry point for interaction design, decisions already closed, and implementation order.
5. [**Interaction Targets and Selection**](interaction_targets_and_selection.md)
   - Target taxonomy, picking levels, `active_selection`, mixed selection, and group metadata.
6. [**Interaction Gestures and Menus**](interaction_gestures_and_menus.md)
   - Hover/click/double-click semantics, context menus, and measurement/tool-mode behavior.
7. [**Interaction Modifiers and Future**](interaction_modifiers_and_future.md)
   - Reserved modifiers, future ideas, borrowed patterns, and deferred questions.
8. [**Strips**](strips.md)
   - GroupStrip direction, alternatives not chosen, first implementation scope, and future strip ideas.
9. [**Roadmap**](roadmap.md)
   - Strategic goals and upcoming development phases.
10. [**Checkpoints**](checkpoints.md)
   - Current handoff checkpoint: active status, decisions, next steps, and constraints.

## Standards and Conventions

This project strictly adheres to the UIBCDF software engineering standards. Please refer to the root `*_GUIDE.md` files for the canonical documentation of each infrastructure tool.
