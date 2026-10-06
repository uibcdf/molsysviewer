---
summary: Adopt explicit interaction selection mode names before 1.0
issue: uibcdf/molsysviewer#168
status: open
opened: 2026-10-06
closed:
verification: inspected
area: [interactions, api, studio, state]
guard:
normative:
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
Names are approved; executable APIs still use the old values. The shared sparse
result contract originates in uibcdf/molsysmt#250 and uibcdf/molsysviewer#114.

## How

Coordinate provider query vocabulary before consumer implementation. The owning
consumer routes are `InteractionsManager.query/_filter`, set creation/editing,
Python/TypeScript messages, Studio controls and state/session filter records.
MolSysMT owns sparse participant semantics, coverage and `between(A, B)`.
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

Implementation and provider agreement pending. Continue the human review with
current executable names; the approved names become callable when the coordinated
change and persistence migration are verified.
