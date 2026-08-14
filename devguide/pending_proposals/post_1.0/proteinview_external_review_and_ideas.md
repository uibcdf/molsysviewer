---
summary: Idea inventory from an external terminal viewer.
issue: uibcdf/molsysviewer#50
status: open
opened: 2026-08-02
closed:
verification: inspected
area: [docs]
guard:
normative:
blocked_by: []
supersedes: []
---

# Post-1.0 ideas from an external review of ProteinView

**Status:** idea inventory, post-1.0. Not an approved design. Each surviving item
needs its own proposal before any implementation.

**Source:** ProteinView v0.3.0, read 2026-08-02 at `~/repos@others/ProteinView`.
A Rust terminal molecular viewer, ~13.5k lines, MIT. All line references below
point at that checkout.

---

## 0. Why a terminal viewer is worth reading at all

ProteinView renders with its own software rasteriser into braille characters,
Sixel, or the Kitty graphics protocol. None of its `src/render/` transfers to us
— we have Mol\*, which does that better and is not our problem.

What transfers is orthogonal to rendering: **what it chooses to show without
being asked, and how it lets itself be driven by something that is not a human.**
Those are product decisions, and a viewer built under a completely different
constraint makes them differently.

---

## 1. Already covered — do not open proposals for these

This section exists to prevent duplicated work. Four of the features that look
most attractive in ProteinView's README are already designed here, in most cases
more thoroughly.

**Classified non-covalent interactions.** ProteinView classifies inter-chain
contacts as salt bridge (≤4.0 Å), hydrogen bond (≤3.5 Å), hydrophobic contact
(≤4.5 Å) or other (`src/model/interface.rs:130`). This is
[`interactions_domain.md`](interactions_domain.md), which goes considerably
further: named criterion, cutoffs and engine serialised as provenance,
per-frame re-evaluation, and `persistence` over a trajectory. ProteinView's
classification is also weaker than it looks — it inspects **only the single
closest heavy-atom pair per contact**, a limitation the authors document
themselves at `interface.rs:126`, so a salt bridge at 3.8 Å is lost whenever a
C–C pair sits at 3.5 Å. There is nothing to import here.

**Pocket geometry.** Covered, and far more ambitiously, by
[`visualization_representations_roadmap.md`](visualization_representations_roadmap.md)
§1.1 (cavity wall meshes, mouth caps, volumetric envelopes). ProteinView has no
cavity geometry at all — see §4 below for what it actually computes.

**Headless image export.** Already implemented, with two backends:
`molsysviewer/viewer/core.py:2882` (`_export_image_headless_qt`) and
`core.py:3001` (`_export_image_headless_playwright`). Their `--snapshot` flag is
the same capability behind a CLI flag we do not expose — which is the subject of
[`viewing_in_the_terminal.md`](viewing_in_the_terminal.md), where the
implementation lessons drawn from their terminal output path are collected.

**Colour schemes by chain, element, B-factor, and sequence position.** Present in
`molsysviewer/colors.py` and `molsysviewer/styles.py`, plus the Mol\* theme
registry in `styles.py:150`.

---

## 2. Predicted-structure awareness and confidence colouring

**What.** The viewer should know that a loaded structure is a *prediction*, and
offer a confidence colour scheme (pLDDT) that says what the number means.

**Why.** Verified 2026-08-02: `plddt` and `alphafold` appear **zero times** in
`molsysviewer/` and **zero times** in `devguide/` (excluding `course/`). Today a
predicted structure can be coloured through the Mol\* `uncertainty` theme
(`styles.py:157`) or `occupancy` (`:152`), but nothing in the viewer states that
the B-factor column holds a confidence score rather than a crystallographic
temperature factor. Those are different quantities with different units and
opposite polarity, displayed through the same control.

Predicted structures are now a large share of what users open. This is the
highest value-to-cost item in this document: Mol\* already ships the theme, so
the work is semantics and exposure, not rendering.

**How.** The field semantics must come from MolSysMT, not from a viewer
heuristic. ProteinView autodetects AlphaFold structures and switches the palette;
we should not — a B-factor column in the 0–100 range is also an ordinary
B-factor column, and silently relabelling it is exactly the kind of unrecorded
scientific claim the guiding principles forbid. The viewer **offers** the scheme
when MolSysMT declares the column's meaning, and never imposes it.

**Entry gate:** MolSysMT publishes an attribute that declares the semantics of
the per-atom scalar field.

---

## 3. Interface as an aggregate report, not an edge set

**What.** A different granularity from the Interactions domain: not "which atom
pairs interact" but "**which residues of chain A touch chain B, how many per
chain, and in what order of proximity**", presented as a sorted, navigable list.

**Why.** [`interactions_domain.md`](interactions_domain.md) produces graph edges
over frames. It does not answer the aggregate question, which is the one asked in
epitope/paratope work, complex assembly inspection, and any "what is the binding
footprint" workflow. ProteinView answers it directly: `interface.rs:303`
(`analyze_interface`), `:331` (`analyze_interface_for_chain`), `:456`
(`contacts_between`), `:474` (`summary`), rendered as a dedicated sidebar in
`src/ui/interface_panel.rs`, with its own focus/partner palette that is
deliberately mutually exclusive with the regular colour schemes.

**How.** As a thin aggregation layer over the Interactions domain, reusing its
records rather than recomputing contacts. **Strictly after** that domain exists;
it has no independent life.

**Entry gate:** the Interactions domain is implemented through at least its
state/history slice.

---

## 4. Ligand environment as a zero-configuration gesture

**What ProteinView actually does.** Despite the name `binding_pockets`, it
performs no pocket detection. `interface.rs:366 analyze_binding_pockets` is a
brute-force scan: for every ligand, every polymer residue with any heavy atom
within 4.5 Å joins a `HashSet<(chain_idx, residue_idx)>`. Hydrogens are skipped
by element. There is no solvent-accessible surface, no alpha spheres, no grid, no
volume, and no druggability score. The whole computation is gated on
`if !protein.ligands.is_empty()` (`src/app.rs:213`, `:237`), so **an apo
structure yields nothing at all**. It reports who surrounds an already-bound
ligand; it does not find sites.

**Why it is still worth recording.** The value is not the algorithm — 
`molsysmt.structure.get_neighbors` already computes this, better. The value is
the **gesture**: open a structure that has a ligand, and the viewer immediately
offers "these are the residues lining it", highlighted and listed by distance,
click to focus. Zero parameters, zero criterion negotiation, useful in the first
minute.

This is distinct from both §1 entries: the pocket-envelope roadmap is cavity
*geometry*, and the Interactions domain requires a named criterion before it can
answer anything. A first coordination shell requires neither.

**Caveat inherited from their parser.** Ligand identity is decided per residue in
`src/parser/pdb.rs:35-72`: all-HETATM residues qualify, waters are dropped by
name, and a fixed 20-name allow-list plus a ≤1-heavy-atom rule separates ions
from ligands. Consequences that are probably unintended there and must not be
reproduced here: selenomethionine (MSE) is all-HETATM and multi-atom, so it
becomes a "ligand" that generates a pocket around itself inside its own chain,
and any multi-atom ion outside the 20-name list is classified as a ligand. Our
equivalent must ask MolSysMT what a ligand is.

---

## 5. An agent-facing headless control surface

**What.** ProteinView ships `src/panel_server.rs` (1144 lines, plus 604 lines of
tests): a persistent process that owns the molecular state, reads **one NDJSON
command per line of stdin**, atomically replaces a PNG on disk, and answers with
the request id, a **monotonic revision**, and the complete camera and
presentation state. It offers `get_state` without rendering, caps requests and
responses at 64 KiB, and rejects undeclared commands as `unknown_command`
(`:1034`). On top of that they built two agent integrations
(`integrations/codex/`, `integrations/oh-my-pi/`) that put a live, controllable
molecular panel inside a chat session.

**Why it is interesting for us specifically.** We already own nearly every piece:
`runtime_actions.json` as a declared manifest, `wrapOutbound` rejecting
`unknown-action`, the runtime router with identity/authority/acks, revisions, and
two working headless render backends (§1). What is missing is only the loop that
exposes them to an external process.

**Why it is post-1.0 and not negotiable.** The pre-1.0 master plan §4.B forbids
creating a public extension API before 1.0 without a demonstrated consumer. This
would be exactly that, and a large one. Recorded here so the option is not
rediscovered from scratch.

**What makes it cheap later, at no extra cost now.** Master plan Phase 5 (the
endpoint matrix) and Phase 9 (the manifest as single source of truth) already
produce most of the contract this would need.

**Entry gate:** the 1.0 API freeze has ended **and** a concrete consumer exists.

**Shares its machine with the terminal viewer.** A persistent headless page that
owns the state, receives commands and replaces the frame is exactly what an
interactive terminal viewer needs; an agent driving it over NDJSON and a human
driving it with arrow keys are two drivers of one mechanism. See
[`viewing_in_the_terminal.md`](viewing_in_the_terminal.md) §6, which defers its
interactive tier to this section rather than specifying a second one.

---

## 6. One scene summary

**What.** A single call that answers "what is on screen right now" in one
printable digest: structures, chains, active representations, visible layers,
current selection, measurements, frame.

**Why.** We have per-manager `info()` methods throughout the Python API, and
`export_state` for the full serialised scene (Contract C.2), but nothing between
them. ProteinView has `InterfaceAnalysis::summary()` (`interface.rs:474`) and
`interaction_counts()` (`:419`) producing exactly that kind of compact textual
account. It is useful in a notebook, and it is the single most useful thing to
hand an agent — which is why it should be designed before §5, not after.

**Entry gate:** none beyond ordinary post-1.0 scheduling. Small and
self-contained.

---

## 7. Implementation pattern worth copying: speculative background precompute

`src/app.rs:207-221`: when the structure is large, ProteinView starts the
interface analysis **on a background thread at load time**, before the user has
pressed anything, so the result is already waiting when the key is pressed. The
foreground path stays interactive and the analysis is never paid for
synchronously.

Our natural equivalent is computing in Python while the frontend mounts the
scene. Worth remembering for §3 and §4, and for the Interactions domain's
dynamic mode.

Their fallback in the same block is also sound: a very large structure defaults
to a cheaper representation, **but only when the user did not choose one
explicitly** (`app.rs:242`). We have no size-aware degradation visible in
`molsysviewer/viewer/presets.py`; Mol\* may decide something internally. The
transferable part is not the degradation, it is *saying so* rather than silently
drawing something other than what was asked for.

---

## 8. Not an idea — a fidelity defect found while reading

ProteinView is precise about residue addressing: `A:42` and `A:42[A]` are
different residues, and omitting the insertion code selects **only** the blank
code, never every residue numbered 42.

Checking ours, `molsysviewer/js/src/plugin/structure.ts:397`:

```ts
pdbx_PDB_ins_code: Column.ofConst("", atomCount, Column.Schema.str),
```

The insertion code is set to empty for every atom when the structure is built in
the frontend. Where insertion codes carry meaning — Kabat/Chothia antibody
numbering above all — distinct residues become indistinguishable in the viewer.
`insertion code` and `icode` appear **zero times** in `devguide/`.

**Routing note.** This is a loss of scientific information, not a feature idea,
and it does not belong in a post-1.0 document on merit. It is recorded here only
because this review is where it surfaced. It has **not** been traced to its
origin — the information may already be absent upstream in what MolSysMT hands
over. Someone should decide whether it belongs in the open-items inventory
instead; that decision is not made by this document.

---

## 9. Anti-patterns their own analysis records

ProteinView ships `.planning/codebase/CONCERNS.md`, a self-audit, and it is the
most instructive file in the repository:

- `atoms_bonded_3d` is duplicated verbatim in `src/render/braille.rs:46` and
  `src/render/hd.rs:130`, **each with its own hardcoded 1.9 Å bond cutoff**.
- `color_to_rgb` is duplicated in `src/render/ribbon.rs:105` and
  `src/render/hd.rs:74`.
- The 4.5 Å contact cutoff appears as a bare literal five times in
  `src/app.rs` alone.
- Their rainbow scheme keys hue on `seq_num / total_residues`
  (`src/render/color.rs:171`), which breaks on non-contiguous residue numbering —
  gaps from disordered regions, insertion codes — producing a wrong but
  plausible-looking figure.

All four are the recurring defect pattern named in §0 of the pre-1.0 master
plan: *where two things must agree and nothing mechanically forces them to, they
drift in silence.* The last one is a direct warning for us: if any of §2, §3 or
§4 introduces a per-residue colour mapping, `molsysviewer/colors.py:596`
(`expand_values_to_atoms`) is where that same bug would live, and any distance
cutoff we add belongs in one named place.

---

## Entry gates

| Item | Start only when |
|---|---|
| §2 Predicted-structure confidence | MolSysMT declares per-atom scalar field semantics |
| §3 Interface aggregate report | the Interactions domain has reached its state/history slice |
| §4 Ligand environment gesture | MolSysMT's ligand definition is the one used; no local heuristic |
| §5 Agent control surface | 1.0 API freeze has ended **and** a concrete consumer exists |
| §6 Scene summary | none beyond post-1.0 scheduling |
| §7 Speculative precompute | applies within whichever of §3/§4/Interactions ships first |
| §8 Insertion codes | routing decision taken; origin traced to viewer or upstream first |

---

## Triage note

Per this directory's rules, post-1.0 location is a scope decision and not a
commitment to implement. Sections 1 and 9 are permanently useful regardless of
whether anything else here is ever built: §1 prevents duplicated proposals, §9 is
a concrete warning about code we already have.
