---
summary: Large multi-chain assemblies render without their protein copies
issue: uibcdf/molsysviewer#64
status: resolved
opened: 2026-08-19
closed: 2026-09-02
severity: high
verification: reproduced
area: [transport, frontend, representations]
guard: molsysviewer/js/tests/e2e/bioassembly-chain-identity.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# The data arrived; the hierarchy did not

**Reported:** 2026-08-19, first as `uibcdf/molsysmt#163` against `make_bioassembly` and
moved here by measurement. Triaged and fixed 2026-09-02, in the first session with a
browser available to look.

## What

```python
molsys    = msm.convert('2BUK')
assembled = msm.build.make_bioassembly(molsys, bioassembly='1')
msm.view(assembled)
```

A 60-copy icosahedral capsid displays the waters of every copy and the protein of none
beyond the asymmetric unit.

|  | atoms | chains | proteins | ions | waters |
| --- | --- | --- | --- | --- | --- |
| asymmetric unit | 1 588 | 5 | 1 | 3 | 158 |
| assembly | 95 280 | 300 | 60 | 180 | 9 480 |

## How

`molsysviewer/js/src/plugin/structure.ts` fed the payload's `chain_id` into **both**
`label_asym_id` and `auth_asym_id`, and `residue_id` into both `label_seq_id` and
`auth_seq_id`.

Those are *author* labels, and a bioassembly reuses them by construction: the 60 copies
all call their chains A–E. Measured on the payload the viewer actually sends:

| field | distinct values | should be |
| --- | --- | --- |
| `chain_id` | 5 | 300 |
| `residue_id` | 345 | 20 700 |
| `atom_id` | 1 588 | 95 280 |
| `molecule_id` | 9 720 ✓ | — |
| `component_id` | 9 720 ✓ | — |

The last two rows are the tell: they were already built from `*_index`, while the three
that feed Mol\*'s hierarchy were built from labels.

## Why

Cartoon traces a polymer per residue. With 60 copies' atoms collapsed into one copy's
worth of residues, only one copy can be traced. Waters are per-atom points and need no
hierarchy at all, so all 9 480 kept rendering — which is what made the defect look like a
capacity limit rather than an identity one.

Nothing errored, nothing warned, and the scene looked like a capsid. A user would have
read 59 missing copies as the assembly itself.

## What was refuted

**The report's own first place to look — "whether cartoon generation has a per-chain or
per-atom ceiling that 300 chains and 95 280 atoms cross".** There is no ceiling. The
defect reproduces with **two copies of a four-residue helix**, 32 atoms in total.

**That contiguity would save it.** This was the diagnosis this document nearly shipped.
The copies are contiguous, so the label sequence changes at every copy boundary
(A B … A B …), and Mol\* could plausibly have segmented on the change rather than on the
value — in which case the labels would have been harmless and the cause lay elsewhere.
It does not. Measured in a real browser:

| two copies, one shared label | chains | residues | atoms |
| --- | --- | --- | --- |
| labels repeated | **1** | **4** | 32 |
| labels made unique | 2 | 8 | 32 |
| expected | 2 | 8 | 32 |

Mol\* groups by the value it finds. Every atom arrived in both cases: what was lost was
never the data.

**That the visual claim needed a screen.** The original report marked the rendering
`asserted` because its environment was headless. It did not need pixels — it needed
Mol\*'s own hierarchy counts, which a headless Chromium reports perfectly well. The gap
was that nothing had asked.

## Resolution

Fixed in `ccbe32e8`. `chain_index` and `residue_index` now travel in the payload and feed
`label_*`; `chain_id` and `residue_id` stay in `auth_*`, where the user reads and selects
by them. This is what mmCIF separates the two identities for. A payload without the
indices behaves exactly as before.

Cost: the two arrays are 10.6% of the atom block (1.06 MB of 9.99 MB on this assembly).
Dense per-atom integers; they would compress well if that ever matters.

Guard: `bioassembly-chain-identity.e2e.ts`, registered in the runner (suite 31). It asks
Mol\* for its own hierarchy rather than reading our bookkeeping, and was mutation-verified
by pointing `label_asym_id` back at the author label.

## A consequence worth knowing, which is not a defect

A state document re-resolves onto a different system by atom identity —
`(chain_id, group_id, group_name, atom_name)` — and on this assembly that tuple has 1 588
distinct values for 95 280 atoms: every one is 60-fold ambiguous. `_reindex_by_identity`
refuses an ambiguous match rather than guessing, so a state saved elsewhere will not
re-resolve onto a bioassembly.

That is correct and not fixable by switching to `chain_index`: an index is positional, and
an identity that moves when the system is reordered is not an identity. The 60 copies are
genuinely indistinguishable by any label-based scheme, because they *are* identical except
in position. Onto the same assembly the fingerprint matches and the stored indices are
used directly, so the ordinary case is unaffected.


---

## Correction appended 2026-09-02 — the limitation below is gone

The section above records that a state document cannot re-resolve onto a bioassembly,
because the atom identity `(chain_id, group_id, group_name, atom_name)` had 1 588 distinct
values for 95 280 atoms, and argues the limitation is not fixable by switching to
`chain_index`, since an index is positional.

That argument still holds and the limitation no longer applies: **MolSysMT removed the
ambiguity at its source.** `uibcdf/molsysmt#198`, reported from here, is fixed in their
`2f6c46f3c` — bioassembly copies now receive unique chain IDs while keeping the repeated
author chain names.

Re-measured on 2BUK bioassembly 1 with their fix in place: `chain_id` now carries 300
distinct values, and the identity tuple is 95 280 distinct for 95 280 atoms, **zero
ambiguous**. Verified end to end: an annotation on an atom of copy 7 (index 3016) restores
onto a trimmed copy of the same assembly at index 3009, unbroken.

Worth keeping as a shape rather than a fact about one bug. The limitation was real, it was
correctly diagnosed as unfixable *from here*, and it was removed by fixing the thing that
caused it in the package that owned it. Reporting it was what made that possible.
