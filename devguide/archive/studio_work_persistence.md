---
summary: Complete Studio save and restore workflows for states and sessions.
issue: uibcdf/molsysviewer#224
status: resolved
opened: 2026-10-10
closed: 2026-10-10
verification: inspected
area: [studio, state]
guard: tests/test_studio_work_persistence.py::test_session_file_roundtrip_replaces_system_and_preserves_analysis
normative:
blocked_by: []
supersedes: []
---

## What
Expose the existing public state JSON and experimental session MSV save/restore operations in Studio. The principal maintainer accepts this coverage extension before 1.0.

## How
Reuse view.save_state/load_state, view.save_session and molsysviewer.load_session(..., view=view). Keep the browser filesystem distinct from the running Python filesystem, confirm destructive restoration and existing-file replacement, retain drafts and correlated success/failure feedback, and refuse operations in exported views without Python authority. State files omit molecular data; sessions include the system and remain experimental with trajectory-sized storage.

## Why
Studio currently exports PNG and HTML but cannot save work for later editing. Complete the everyday persistence workflow without duplicating the scene importer or session format. Verify restored objects, camera/frame, scientific analyses and failure behavior through real owners and browser tests.

## Implementation
The real browser guard saves and restores both formats, preserves drafts on
failure, consumes only matching replies and disables offline file actions. MSV
restoration reloads System; the matching requesting panel returns to Export
to display the outcome. Other endpoints do not change their current section.

## Resolution — 2026-10-10
Studio saves/restores JSON state and experimental MSV through the public owners, with Python-host paths, explicit overwrite/restore declarations, persistent drafts and correlated replies.

Guard: `tests/test_studio_work_persistence.py::test_session_file_roundtrip_replaces_system_and_preserves_analysis`. The real Studio browser workflow additionally checks
coordinate focus, layer-hidden wording, JSON/MSV confirmation/retry/correlation,
PNG scale/alpha and unavailable exported-host actions. Focused Python file/action
checks pass 27/27; final figure/image checks pass 40/40. Local full-suite and
experimental Qt limitations remain in `studio_coverage_20261010.md`; no package
is qualified and no 1.0 publication is authorized by this closure.
