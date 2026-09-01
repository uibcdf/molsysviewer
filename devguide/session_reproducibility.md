# Session reproducibility — the standing requirement

**Status:** durable requirement (not a phase). Owner: whoever touches viewer
state. Current mechanism: `view.export_state()` / `view.import_state()`, plus
the thin file helpers `view.save_state()` / `view.load_state()`; document
`version: 2` (landed Phase 6 of the scene rework). Since 2026-09-01 there is also
`view.save_session()` / `molsysviewer.load_session()`, which carry the molecular
system as well (§The session file).

---

## The promise

> A user must be able to save their session, close the viewer, and later
> reload that session on another machine (or in another kernel) and continue
> as if they had never left.

This is not a feature of one subpanel. It is a **cross-cutting invariant**: any
piece of scene state a user can create must be recoverable. If a new capability
is not serialised, the promise quietly breaks for that capability, and — because
`export_state` still returns something and `import_state` still runs — it breaks
**silently**. That is the failure mode this document exists to prevent.

## Why this needs a standing note, not just code

The promise was already broken once and nobody noticed for a long time. Before
Phase 6, `export_state` persisted `{tag, atom_indices}` per region and nothing
else — no representation, no colour, no visibility, no provenance, and nothing
of the `whole`. A saved session reloaded as bare grey regions, and no test
caught it because the round-trip *ran without error*. The audit that found it
(2026-07-10) is why Contract C exists.

The lesson: **serialisation coverage decays by default.** Every phase that adds
state adds a way for the promise to rot. So this is a checklist that outlives
any single phase.

## What "the session" is

Today the reproducible unit is the **overlay state on top of a loaded
structure** — the structure itself is not part of the document (`import_state`
requires a compatible structure already loaded). The document carries:

- annotations (structured anchors, style, visibility and broken state),
  measurements (recipes, visibility and broken state), saved selections and
  literal shape payloads;
- user-created layers, including their provenance, visibility, kind and metadata;
- clipping sections, including their tag, point, normal and inverted side;
- **regions**: identity (`uid`, `tag`, `selection`), recipe (`provenance`,
  `mode`), ordering (`order`), visual state (`representation` incl. `inherit`,
  `preset`, `params`, `hidden`), and the region's own colour layer;
- the **whole**: representation, preset, params, visibility, structural colour
  theme, base colour layer;
- the **order high-water mark**, so a region created after a reload still
  outranks the restored ones — without it, the winner in every overlap zone
  silently flips.
- per-domain tag high-water marks, so the next generated tag cannot collide
  with an imported or previously consumed tag.

Regions are restored in **topological order** (a recipe's operands, referenced
by `uid`, exist before the dependent is rebuilt). A corrupt graph (a cycle or a
missing operand) raises rather than loading half a session.

`save_state(path)` writes that same document atomically as UTF-8 JSON, and
`load_state(path)` parses it before delegating to `import_state`. These helpers
do not define a `.msv` bundle and do not broaden the reproducible unit: the
molecular system, camera and undo history remain outside the file.

## The session file

`view.save_session(path)` writes the scene **and the system it was built on**;
`molsysviewer.load_session(path)` reopens it with nothing loaded first. That is
the whole difference, and the reason the format exists: a state document cannot
keep the promise at the top of this file on its own, because reopening one
requires the user to already have the right structure and to know which one it
was.

The file is a zip holding three members:

| member | what it is |
| --- | --- |
| `manifest.json` | format, version, and what structure is inside |
| `state.json` | the `export_state` document, unchanged |
| `structure.h5msm` | the molecular system, in MolSysMT's own form |

**Why `.h5msm` and not `.bcif`.** MolSysMT writes `.pdb` and `.h5msm` from a
`MolSys`, and not `.bcif` — the usual preference for binary CIF over PDB is about
*reading* what a user supplies, and does not apply to what we write here. Of the
two available, `.pdb` collapses chains, misassigns waters, and carries one
structure where a trajectory has thousands. Measured: `.h5msm` round-trips 62
atoms across 5,000 structures, in 0.17 s out and 0.15 s back.

**The property the format depends on.** A structure that survived the round trip
in every respect *except* the fields the topological fingerprint is taken over
would produce a session that warns, on reopening, that its own structure is not
the one its own state was written for. That the fingerprint survives is
measured, and guarded by
`test_the_reopened_session_does_not_warn_about_its_own_structure`.

**The manifest repeats the structure's identity** from the state document on
purpose, so a reader — a person, a tool, a future migration — can tell what is in
the file without parsing the scene.

**Still open: size.** A session is as large as its trajectory (a 5,000-frame
pentalanine is 3.5 MB before compression; a solvated protein trajectory is not).
There is no budget, no warning and no downsampling. `scale_budget.py` already has
the machinery for the equivalent question on load, and reusing it here is the
obvious first move — but the threshold is a policy decision, not an
implementation detail, so it is recorded here rather than guessed.

## The rule for every future change

**When you add state a user can create or change, you extend the document in
the same change, or you have broken reproducibility.** Concretely, ask of any
new capability:

1. Can a user produce this state from the API or the GUI? If yes, it must
   round-trip.
2. Does `export_state` capture it, and `import_state` restore it *exactly* —
   including precedence/ordering, not just presence?
3. Is there a **round-trip test** that fails if the field is dropped? A test
   that asserts "the region exists after import" is not enough; assert the
   *content* — the winning colour in an overlap, the restored order, the
   provenance — and confirm by mutation that removing the serialisation fails
   it. (This is exactly how the silent 2026 breakage would have been caught.)

## Known gaps and open questions (keep this list honest)

- ~~**The structure is not in the document.**~~ **Closed 2026-09-01 (#38).** It
  still is not, and now that is a property of `save_state` rather than a gap:
  the open product question was answered by adding a second unit rather than by
  growing the first. See §The session file. A *state* document remains the
  overlay applied onto a structure the caller has already loaded.
- **No v1 reader.** v2 is the only accepted version by design (no external users
  yet). The moment there *are* saved sessions in the wild, a version-migration
  policy becomes a real obligation, not an optional one.

  *Re-read 2026-08-06: still true, but the premise moved. MolSysMT is now an
  external adopter, so "no external users" is no longer the blanket fact it was.
  What they consume is the HTML export — a history replayed into a page — and not
  a saved session, so no v2 document is in anyone's hands yet. The condition has
  not fired; it is now one adopter away from firing.*
- **History / undo** (Phase 8, Contract H): the command history is
  session-scoped and deliberately **not** serialised. If a user ever expects
  undo to survive a reload, that is a separate, larger decision — flagged here so
  it is a choice, not an accident. In memory, checkpoints are deterministic
  compact JSON bytes rather than duplicated Python object graphs. The store is
  bounded by both 25 entries and 64 MiB across undo and redo; crossing the byte
  budget discards the oldest checkpoints with a `RuntimeWarning`, never the
  current scene or the newest available checkpoint.
- **Terminology.** "State" (a snapshot you can reload) and "history" (the
  sequence of commands, for undo and for reproducible replay/export to HTML) are
  different mechanisms that both bear on reproducibility. They must not be
  conflated: a snapshot restores *where you are*; a history replays *how you got
  there*. Both exist; keep their contracts distinct.

## Future proposal: a command history that compacts itself

Phase 8's undo/redo is **snapshot-based**: each mutating operation stores a full
`export_state` snapshot in compact JSON form, and undo restores the previous
one. This is guaranteed-correct and bounded, but it discards *how* the user got
there — the sequence of commands — and large changing snapshots consume the
byte budget faster than ordinary scene edits.

A **command-based** history (each operation records its forward command and its
inverse) would instead preserve the narrative: the exact steps taken, replayable
and exportable as a reproducible script. The reason it was not chosen is the cost
of maintaining a correct inverse for every operation, and of a log that
accumulates do/undo churn (create then delete, colour then recolour) that a naive
implementation never cleans up.

That objection weakens if a language model is in the loop. A command log could be
**periodically compacted by an LLM**: collapsing an operation and its later
inverse, merging a sequence of small edits into one intent, and rewriting the log
into the *minimal* command sequence that reaches the same state — turning a noisy
interaction trace into a clean, human-readable, reproducible protocol. That is a
genuinely new capability (a session that documents itself as a tidy script), and
it belongs to the same family as this document: mechanisms that make a session
reproducible. Proposed for the future; not built. If pursued, it would sit
alongside — not replace — the snapshot state, since a self-documenting *history*
and a reloadable *snapshot* answer different questions (§Terminology).

*Note (2026-07-31):* the runtime envelope makes this proposal materially
cheaper without having been designed for it. Every message now carries
`messageId`, `correlationId`, `action` and a `direction`, and
`WidgetRuntimeRouter` already establishes the invariant a command log needs:
**one `command` message → one public-API mutation → one history checkpoint**,
with duplicates rejected rather than replayed. The raw material for a command
log is therefore already on the wire and already deduplicated; what is still
missing is only the *inverse* of each operation, which was always the expensive
half of the objection above. This does not reopen the decision — Phase 8 stays
snapshot-based — but a future attempt starts from a much better position than
this section assumed. The router's command record is a bounded LRU for
deduplication and is explicitly **not** a history: do not grow it into one
without deciding the questions in this section first.

## Where the mechanism lives

- `molsysviewer/viewer/state.py` — `export_state` / `import_state`, `STATE_VERSION`.
- `molsysviewer/session.py` — `save_session` / `load_session`, `SESSION_VERSION`.
- `tests/test_session_bundle.py` — the session round-trip, the trajectory, the
  refusals and the fingerprint guard.
- `tests/test_state_structure_identity.py` — re-resolution onto a different
  system; `tests/test_state_view_state.py` — the vantage point;
  `tests/test_state_focus_overlays.py` — focus overlays as state.
- `tests/test_state_v2.py` — the round-trip, overlap-winner, high-water-mark,
  topological-order, transient-filter and whole-restore tests.
- `scene_contracts.md` §C — the normative contract this implements.
