# Whole representation succession semantics

**Status:** open, audit only. No behavior change is proposed until the audit
answers the question below.

**Origin:** filed 2026-08-03 after a reading of
[`../areas_of_opportunity_analysis.md`](../areas_of_opportunity_analysis.md) §2
contradicted the runtime. The document is the design record for the decision;
the runtime appears to implement the opposite. One of the two is wrong, and
nothing in the suite currently says which.

## The contradiction

`areas_of_opportunity_analysis.md` §2 states the problem as *"si un usuario
aplica un estilo (ej. `Cartoon`) y luego otro (ej. `Sticks`), Mol\* añade ambos
estilos simultáneamente"*, proposes `mode="replace" | "additive" | "exclusive"`,
recommends `replace` as the pre-1.0 default, and then records in its closing
section:

> **Estado**: **Excluido por decisión de diseño**. […] El comportamiento por
> defecto se mantiene de forma aditiva (`additive`).

The runtime reads as `replace`. `StateHandlers.handleSetGlobalRepresentation`
(`js/src/managers/handlers/state-handlers.ts`, around the
`collectBaselineGlobalRepresentationRefs()` call) does:

1. collect the refs of the current baseline global representations;
2. clear `globalReprs`;
3. build the new representation and register its refs;
4. remove the collected refs that the build did not reuse.

That is add-then-remove — Contract S9's no-gap ordering — and its net effect is
succession, not accumulation. The comment at that site describes the case
explicitly: *"the loader's preset leaves four global representations behind and
they collapse into one"*. Python agrees: `Whole._representation` and
`Whole._preset` are single-valued, so the Python model cannot even express two
coexisting global representations.

## Why this is worth an audit rather than an edit

Three readings are possible and they have different consequences:

- **The document is stale.** `replace` was implemented later (plausibly as part
  of the S9 camera/representation work) and the "excluded by design" note was
  never revisited. Then the fix is documentation, and the missing piece is a
  test that pins the semantics so the next reader does not have to re-derive
  them from the renderer.
- **The document is right about a case the reading missed.** Presets, user
  presets with rules, region-owned representations and the `layer`/`order`
  colour stack all pass through the same handler. Succession may hold for the
  simple `representation` argument and not for some preset or add-on path.
- **They are both right about different things.** "Additive" may have been
  about Mol\* nodes rather than about the user-visible whole, in which case the
  vocabulary is what needs fixing.

Deciding this from either artifact alone is the failure mode
`engineering_rules.md` §5 warns about: *verify documentation against the code,
not against the plan*. This proposal exists because the reverse was nearly done
here — a papercut was almost reported to the maintainer on the strength of the
document, and the code disproved it.

## What the audit must establish

1. Which semantics are actually in force for `whole.set_representation`, at the
   real seam, for each entry path: bare `representation`, `preset`, `user_preset`
   with rules, and a load whose loader preset installs several global
   representations.
2. Whether the answer is the same after `apply_system_edit`, after a second
   `load`, and in the canonical popup and static-export projections. A
   succession rule that holds live and not on replay is worse than either rule
   applied consistently.
3. Whether any public state document (state v2) records more than one global
   representation, which would make the Python single-valued model lossy.

## Acceptance

- A named test asserts the surviving global representation count and type after
  two successive `set_representation` calls, read from the **actual Mol\* cells**
  (`transform.params.type`) as `scene-contracts.e2e.ts` already does for other
  claims — not from the emitted message.
- The same assertion runs for the preset and user-preset paths, or the audit
  records explicitly that those paths are excluded and why.
- Mutation: removing the `stillToClear` removal step must turn that test red. If
  it stays green the test is reading the wrong channel — per
  `engineering_rules.md` §9, prove the mutated path executed before concluding
  anything about the test.
- Whichever answer the audit produces, `areas_of_opportunity_analysis.md` §2 is
  corrected in the same commit as the evidence, and — if `replace` is confirmed
  — the sentence describing the behaviour moves to
  [`../scene_contracts.md`](../scene_contracts.md), which is the normative home
  for it. Today that file says nothing about succession of the whole's global
  representation.

## Not in scope

The three-mode API (`mode="replace" | "additive" | "exclusive"`) is **not**
proposed here. If the audit confirms that succession is already the behaviour,
adding a mode argument to re-enable accumulation is new product surface and
belongs to a separate proposal, judged on whether anyone actually needs to stack
two whole-level representations — a question the layered-colour and region model
may already answer better.
