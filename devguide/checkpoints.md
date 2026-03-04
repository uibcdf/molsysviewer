# Development Checkpoints

This file is the running development log for the repository.
It is intentionally concise and operational.

## Entry Format

- `Date`: YYYY-MM-DD
- `ID`: stable checkpoint identifier
- `Scope`: what was addressed
- `Decisions`: explicit choices made
- `Status`: current project status for that scope
- `Plan`: next concrete actions
- `Criteria`: invariants/rules to preserve
- `Perspectives`: medium-term direction
- `Ideas`: optional backlog notes

---

## 2026-03-04 — CP-2026-03-04-A

- `Scope`: Establish dev workflow governance and align development truth source.
- `Decisions`:
  - `devguide/` is the source of truth for development status and planning.
  - Progress will be tracked via explicit checkpoints in this file.
  - `devguide/roadmap.md` must reflect real implementation status (not only aspirational phases).
- `Status`:
  - Checkpoint process established.
  - `devguide/README.md` updated to include source-of-truth policy and checkpoints index.
  - Roadmap alignment completed in the current cycle (`devguide/roadmap.md` status-aligned).
- `Plan`:
  - Keep checkpoints updated after each substantial step.
  - Use checkpoints to drive prioritization step-by-step.
- `Criteria`:
  - Do not treat generated JS artifacts as implementation source.
  - Preserve Python <-> TypeScript message contract stability.
  - Keep region/layer/tag semantics stable unless explicitly versioned.
- `Perspectives`:
  - Use checkpoint history as release-quality technical memory.
  - Increase traceability between decisions, status, and executed changes.
- `Ideas`:
  - Add a lightweight checkpoint index by topic (protocol, tests, docs, release).
  - Add checkpoint references in PR descriptions for auditability.

## 2026-03-04 — CP-2026-03-04-B

- `Scope`: Start roadmap block "Testing and Quality Gates" for JS unit tests.
- `Decisions`:
  - Replace fragile unit test coupled to obsolete controller internals.
  - Focus initial JS coverage on stable handler-level behavior (`trajectory`, `state`).
- `Status`:
  - Existing JS unit test suite was red due to stale assumptions.
  - `molsysviewer/js/tests/unit/region-hide.test.ts` updated with handler-focused tests.
  - `npm run test:js` is now green in current workspace.
- `Plan`:
  - Continue adding handler-level tests (`loader`, `scene`, additional `state` and `trajectory` paths).
  - Add one more E2E path beyond region hide.
- `Criteria`:
  - Tests must avoid brittle coupling to private controller internals.
  - Prefer deterministic mocks and explicit assertions on contract-relevant behavior.
- `Perspectives`:
  - Incremental JS test expansion should reduce regression risk in protocol/state changes.
- `Ideas`:
  - Split `tests/unit/region-hide.test.ts` into themed files as coverage grows.
