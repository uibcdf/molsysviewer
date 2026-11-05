---
summary: Extraction crashes on numeric region selection recipes.
issue: uibcdf/molsysviewer#296
status: resolved
opened: 2026-11-05
closed: 2026-11-05
severity: high
verification: reproduced
area: [regions, extract, scene]
guard: tests/test_extract_numeric_region_recipes.py::test_numeric_query_is_transferred_without_replaying_source_indices
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Numeric region recipes during extraction

## What

A region created with `selection=[2, 4]` retains a query recipe whose expression
is a numeric selector. Extracting atoms `[1, 2, 4]` raises TypeError while
transferring that recipe. This is separate from closed #119's lost objects.

## How

Reproduced on Viewer 136221e2 with explicit MolSysMT contribution c0149a2d6,
native owner 8486ea59c and immutable public PyUnitWizard 02d0015, Python 3.14.
Bundled TcTIM 1TCD first exposed it during the planned addon system flow;
the dialanine regression isolates the same path. `_transfer_state` passes the
numeric expression to `re.search` whenever atom indices change. Avoiding only
the exception would still leave a source-universe selector replayable in the
new atom universe, potentially choosing different atoms.

## Why

Extraction must preserve selected identities, colors and source evidence.
Source-relative numeric selectors become transferred static recipes when the
atom universe changes. Identity atom extraction keeps its original recipe;
textual index queries retain the existing transfer behavior. No native
scientific implementation or expert addon API change is needed.

## Verification

Guard admitted numeric list, tuple, array and scalar query selectors, and
retain explicit rejection of currently unsupported Boolean masks; cover
static/dynamic source regions, nonconsecutive structures, identity extraction,
source ownership, colors, state reconstruction and session round trips. Keep
the complete original failing JUnit separately from corrected results.

## Resolution

The transfer classifies non-text query expressions as source-relative when the
atom universe changes. It preserves mapped atoms/colors and the source recipe,
then freezes the result using the existing transferred/static contract. The
original implementation fails the new list regression with the reported
TypeError; corrected source passes 15 new guards, 33 scoped migration checks
and 119 related scene/region/session/source/edit checks, without omissions.
The wider 119 count includes the scoped guards; these are not disjoint totals.

The bundled 1TCD exercise now constructs an independent extracted View and
removes 165 stored water atoms from all three explicitly replicated structures,
preserving retained coordinates and saved references. Its initial probe/test
assumptions about mode setting, read-only provenance, selector admission,
saved-selection container type and no-op operation IDs were corrected without
widening public contracts. The original failing product regression and initial
authored-test failures remain separate from final green results.

This is source receiving in the explicit development profile, not an installed
artifact, real GUI click or visible Qt qualification. Exact-head CI remains
pending. No native science or addon expert signatures change.
