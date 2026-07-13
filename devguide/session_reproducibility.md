# Session reproducibility — the standing requirement

**Status:** durable requirement (not a phase). Owner: whoever touches viewer
state. Current mechanism: `view.export_state()` / `view.import_state()`,
document `version: 2` (landed Phase 6 of the scene rework).

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

- **The structure is not in the document.** Reload requires the same structure
  loaded first. Whether a session should bundle (a reference to, or a copy of)
  its structure is an open product question. Until decided, document this
  limitation wherever save/load is surfaced to users.
- **Sections are not in the document.** Clipping planes therefore do not yet
  survive a session round-trip. This debt belongs to the Viewport work.
- **No v1 reader.** v2 is the only accepted version by design (no external users
  yet). The moment there *are* saved sessions in the wild, a version-migration
  policy becomes a real obligation, not an optional one.
- **History / undo** (Phase 8, Contract H): the command history is
  session-scoped and deliberately **not** serialised. If a user ever expects
  undo to survive a reload, that is a separate, larger decision — flagged here so
  it is a choice, not an accident.
- **Terminology.** "State" (a snapshot you can reload) and "history" (the
  sequence of commands, for undo and for reproducible replay/export to HTML) are
  different mechanisms that both bear on reproducibility. They must not be
  conflated: a snapshot restores *where you are*; a history replays *how you got
  there*. Both exist; keep their contracts distinct.

## Future proposal: a command history that compacts itself

Phase 8's undo/redo is **snapshot-based**: each mutating operation stores a full
`export_state` snapshot, and undo restores the previous one. This is
guaranteed-correct and cheap to build, but it discards *how* the user got there —
the sequence of commands — and it grows linearly with the number of operations.

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

## Where the mechanism lives

- `molsysviewer/viewer/state.py` — `export_state` / `import_state`, `STATE_VERSION`.
- `tests/test_state_v2.py` — the round-trip, overlap-winner, high-water-mark,
  topological-order, transient-filter and whole-restore tests.
- `scene_contracts.md` §C — the normative contract this implements.
