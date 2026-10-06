---
summary: Adopt explicit interaction selection mode names before 1.0
issue: uibcdf/molsysviewer#168
status: resolved
opened: 2026-10-06
closed: 2026-10-06
verification: measured
area: [interactions, api, studio, state]
guard: molsysviewer/js/tests/e2e/interactions-calculation.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Adopt explicit interaction selection mode names before 1.0

**Reported:** 2026-10-06, principal-maintainer approval during the human review.

## What

Adopt these explicit query/display filter names in coordination with MolSysMT:

| Current | Accepted target | Meaning |
| --- | --- | --- |
| `incident` | `involving_selection` | At least one participating atom is selected, including internal and crossing interactions. |
| `internal` | `within_selection` | Every participating atom is selected. |
| `cross` | `across_selection_boundary` | Participating atoms occur inside and outside the selection. |
| `between` | `between_selections` | Connects explicit disjoint selections A/B; preserve the current exclusive rule. |

Studio labels: All interactions involving the selection; Only within the
selection; Between the selection and the rest; Between selections A and B.
The provider and consumer implement the canonical-only public query names. The shared sparse
result contract originates in uibcdf/molsysmt#250 and uibcdf/molsysviewer#114.

## How

The requested provider-side coordination is filed in uibcdf/molsysmt#346,
linked to uibcdf/molsysviewer#168 and labelled component:molsysviewer for triage.
Coordinate provider query vocabulary before consumer implementation. The owning
consumer routes are `InteractionsManager.query/_filter`, set creation/editing,
Python/TypeScript messages, Studio controls and state/session filter records.
MolSysMT owns sparse participant semantics, coverage and `between_selections(A, B)`.
Use one consistent public vocabulary rather than adding viewer-only aliases.

Agree migration for existing saved filters, interaction extension versioning and
whether old public arguments are rejected or temporarily supported across both
libraries. Read compatibility is a separate decision from public aliases.
Scientific calculation `selection_mode` and persisted `evaluation_mode` have
their own provider semantics: inspect their compatibility separately rather than
performing a global replacement. Historical qualification receipts retain their
original names and evidence.

Verify unchanged sparse results, occurrence identity, grouped participants,
nonconsecutive structures, disjoint A/B and exclusive behavior with real
analyses. Keep ArgDigest and explicit skip_digestion on public Python routes.
Exercise Studio emission, state/session/history/copy/extract and pre-mutation
validation through owning browser/Python guards. Absorb implemented names into
the scene contract and maintained API/provider guidance after coordination.

## Why

The human review found incident unfamiliar. Proposed intra/inter names mixed
the within-selection category with the combined participation scope. Diego
accepted explicit selection-boundary names after seeing the simple atom-pair
example. The decision and the ongoing review are retained in
`devguide/human_usability_review_20261006.md`.

## What was refuted

Intra/inter alone do not express the combined participating mode. Viewer-only
aliases would leave the consumer and provider with different public vocabularies.
A blind replacement of internal/incident would also change scientific evaluation
coverage metadata, which is outside this query-name decision.

## Resolution

Provider uibcdf/molsysmt#346 is resolved at
`a0ceca86ec99c89377e78fac15cbdf32145a362e` (functional change
`ea10577136fff6ea1d4af7b58346680a267f00d7`). The earlier alias-compatible handoff
was withdrawn. The provider now rejects old query arguments, including trusted
bypass; its separate two-selection method is `between_selections`.

Consumer code, Studio, query tools and examples adopt the canonical vocabulary.
Saved visual filters alone migrate from extension version 1; new exports use
version 2. Scientific coverage metadata and H5MSM are untouched. The source-pair
CI pin is updated to the final provider handoff. Local Linux source-pair
qualification passes; this does not certify a provider package release.

The browser guard exercises all four selector values, verifies exact emitted
selection A/B and mode fields, applies the real provider responses and preserves
20 calculated observations while changing only the display. It also passes the
17 real calculation forms. The scene-module migration guard
`test_legacy_query_filters_migrate_through_state_and_sessions` exercises all
four old names through actual state and H5MSM-backed sessions, preserving signed
scientific content, occurrence identity, evaluated-empty and unevaluated frames.
Additional guards reject old public arguments with digestion enabled or bypassed,
reject invalid version/mode records before mutation and migrate broken filters
without silently repairing their atom selection.

Validation: 37 scene tests; 149 focused API/family/benchmark/dependency/package
tests; full Python once, 2,869 passed/23 skipped/zero failures; 322 Node 22 unit
tests; all three affected real Mol*/Python browser suites; the provider's
previously deselected real Viewer bibliography/session test passes. TypeScript,
runtime rebuild and dependency audit pass. The maintained API guide, tutorial,
scene contract and implementation plan absorb the change.
[The qualification receipt](../interactions_query_modes_20261006.json) retains
commands, provenance and the corrected browser-test response sequencing failure.
Hosted updated-source matrix, installed package qualification and direct human
retest of the renamed controls remain separate evidence. The open sandbox review
notebook is preserved; change its explicit old query argument before rerunning.
