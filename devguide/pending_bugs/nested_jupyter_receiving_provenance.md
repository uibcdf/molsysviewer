---
summary: Qualify the molecular sources actually imported by nested Jupyter receiving.
issue: uibcdf/molsysviewer#364
status: partial
opened: 2026-11-12
closed:
severity: medium
verification: reproduced
area: [jupyter, testing, provenance]
guard:
normative:
blocked_by: []
supersedes: []
---

# Nested Jupyter receiving provenance

## What

The E2 supervisor declares archived MolSysMT `aee7aa65`, but the nested owner
launcher replaces kernel PYTHONPATH and asserts another copied provider root.
The retained `513` notebook identifies that working source as
`0.23.0+757.g08f0afdb8.dirty`; 24 tracked Python files differ from `aee7aa65`.
Its compiled extension matches the qualified `4ffb82e4…` bytes. The unchanged
outer manifest does not cover that complete inner source. Diagnostic `515`
uses the same route. Do not label either exact-`aee7aa65` receiving.

The original failed reports remain preserved. The captured real focus/key/
click observations reproduce a receiver-readiness mechanism; they establish
neither wrong scientific values nor exact-provider qualification. The
opening of uibcdf/molsysmt#718 is explicitly corrected for this distinction.
This finding does not automatically invalidate differently routed direct,
headless or actual-Jupyter controls.

## How

Prepare a declared receiving tree with exact reviewed scientific/addon bytes,
the unchanged canonical extension and the proposed receiver-only changes.
Record imports from inside the actual notebook kernel, including support
modules and extension origins/hashes. Freeze the actual inputs before and
after execution and compare those records before attributing a source commit.
Keep generated version metadata and receiver modifications explicit.

First receive the scoped hidden-controls guard for #718, then repeat the
thirty-cycle campaign. Preserve copied-source, exact-source, hosted, installed
and postponed human scopes separately. The owner correction is delivered as
a PR; no MolSysMT main write or molecular algorithm change is authorized.

## Why

An outer process identity is insufficient when a launcher constructs a new
kernel environment. #315's E2 acceptance needs the sources actually used;
#356's lifecycle correction and #363's upstream follow-up remain separate.

## Current receiving

[PR MolSysMT #721](https://github.com/uibcdf/molsysmt/pull/721) records actual
kernel imports and adds the explicit source/GUI guards. The
[consumer receipt](../jupyter_popup_controls_receiving_20261112.json) receives
both with current copied PyUnitWizard `0.29.4+2.g9bb4f5f`, and 52 affected
receiver controls separately. All 3,169 Git-owned scientific/addon Python
files match `aee7aa65`; actual inner files, data, support and extension are now
in the frozen input set. The copied tree reports `0+unknown`, with no generated
version file; do not infer its identity from that label. The earlier guard pair
retains its separate 0.28.1 overlay scope.

Original raw records are unchanged; the cache receipt carries a dated
qualification correction for nested attempts `513`/`515`. Owner integration,
the bounded review of older nested claims and full E2 memory acceptance remain
pending. The corrected campaign completes all thirty functional cycles in
1,749.912 s with one scientific kernel and all 10,182 selected inputs unchanged.
No blanket requalification is inferred.
