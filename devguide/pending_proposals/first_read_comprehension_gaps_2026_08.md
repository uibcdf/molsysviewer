# What a first read got wrong, and what that says about the documentation

**Status: acted on 2026-08-06. One item left, and it is a decision, not work** —
see *Closure* at the end. Findings 1, 2, 4 and 6 were fixed; 3 and 5 had already
been closed by other work. Recommendation 3 (whether the sixty-bullet feature
inventory should sit above or below the quickstart) is a positioning call and
stays with the maintainer; archive this document once it is made.

Evidence, not design. It proposes documentation changes and owns none of them.

**Origin:** one uninterrupted first read of this repository on 2026-08-03, by an
assistant with no prior exposure to it, asked only to "study the repo so you can
help". Four judgements about the product were formed and all four were wrong.
Each wrong turn is recorded below with the document that produced it and the
artifact that disproved it.

**Why record it at all:** a first read can only happen once per reader, and its
mistakes are the cheapest documentation evidence there is — they name exactly
where the repository misinforms a stranger, with the misinformation still
attached. A maintainer cannot generate this evidence about their own project.

**How to weight it.** This was one reader, and an unusual one: it greps quickly,
reads source willingly, and has no stake. A human scientist evaluating the tool
would hit finding 1 *harder* (they would not open `loaders/` to check) and would
likely never reach findings 3 and 4. Weight the findings by audience, not by
how confidently they are stated here.

---

## Finding 1 — The strongest selling point is invisible (affects users)

**What was concluded:** that MolSysViewer charges an adoption tax — a user
living in MDAnalysis, mdtraj or biotite must convert before seeing anything, and
that this would keep the tool inside its own ecosystem.

**Why:** the README quickstart shows `new_view("1TRS")` and a MolSysMT `MolSys`
passed through an add-on. `development_mantra.md` and the vocabulary rules
emphasise MolSysSuite terms. Nothing on the path a newcomer reads says other
object types are accepted.

**What was actually true:** `load_from_molsysmt` passes the input straight to
`msm.convert(..., to_form="molsysmt.MolSys")`, and `molsysmt/form/` covers
`MDAnalysis_Universe` / `AtomGroup` / `Topology`, `mdtraj_Trajectory` /
`Topology` and its file handlers, biopython objects, and roughly twenty file
formats. ~~`syntax=` accepts other selection dialects.~~ **A user converts
nothing.**

> **Correction, 2026-08-06.** The struck sentence is wrong, and was written the
> way this document criticises: from the declared list, without executing it.
> `MolSysMT` and `MDTraj` work from any form; `MDAnalysis` only from a PDB file
> or an MDAnalysis object; `Amber`, `NGLView`, `ParmEd` and `MolSysMT_NEW` do
> not work at all. See *Closure* below.

**Severity: highest in this document.** This is the easiest advantage in the
product to communicate, it is the first question a prospective user asks, and
the answer is excellent — and absent. A scientist who makes the same inference
does not open `loaders/` to check; they close the tab.

**What would prevent it:** one line in the README quickstart that passes an
`mdtraj.Trajectory` or an MDAnalysis `Universe` directly into `new_view`. Not a
paragraph, a line of code. It belongs to first-contact onboarding (gate #12 in
`path_to_1_0.md`).

## Finding 2 — The differentiator does not appear on the first screen (affects users)

**What was observed:** the README's Features section is a long capability
inventory — seven categories, roughly sixty bullet points — and the quickstart
that follows shows load, regions, a shape overlay, an HTML export and add-on
registration.

**What is missing:** the product's own thesis. `guiding_principles.md` §1 and
`development_mantra.md` both say the centre of the product is that *exploratory
interaction becomes reproducible state*. **No quickstart snippet demonstrates
that loop.** `export_state()` / `import_state()` appear once, as a bullet inside
a feature list, and are never shown working.

The consequence is that the README sells what every viewer sells — formats,
representations, overlays, export — and stays silent about the only thing that
is hard to copy. A reader comparing it against NGLView or py3Dmol on that page
sees a longer feature list, not a different category of tool.

**What would prevent it:** a quickstart whose *last* snippet closes the loop —
interact, capture, restore, and get the same scene — with a sentence naming what
just happened. The capability exists; only the demonstration is missing.

## Finding 3 — A design record contradicted the runtime (affects everyone)

**What was concluded:** that `whole.set_representation` stacks representations
additively and that this is a usability papercut.

**Why:** `areas_of_opportunity_analysis.md` §2, in a section titled *"Estado
Final de Implementación"*, records the behaviour as **"Excluido por decisión de
diseño […] se mantiene de forma aditiva"**.

**What was actually true:** `state-handlers.ts` implements succession
(add-then-remove per Contract S9), and Python's `Whole._representation` is
single-valued and cannot express two coexisting global representations.

This is the finding with the widest blast radius, because it is not a gap — it
is an assertion, in the location a reader trusts most, that the code
contradicts. Already filed separately as
[`archive/whole_representation_succession_semantics.md`](../archive/whole_representation_succession_semantics.md),
now closed by Contract S10.

**What would prevent it:** behavioural claims live in `scene_contracts.md`,
which is normative and has tests behind it; vision documents describe intent and
say so. Today `scene_contracts.md` says nothing about succession of the whole's
global representation, so the only written answer was the wrong one.

## Finding 4 — A decision that was taken read as a decision that was pending (affects contributors)

**What was concluded:** that the Qt standalone track is "practically a second
product inside the first", and that whether it is a port or a product is a
decision that should be taken explicitly.

**Why:** seven files named `standalone_*.md`, five rebuilt PySide6 conda
packages, and a `standalone_qt/` package. The `devguide/README.md` lists the
seven files flat, in alphabetical order, with no annotation saying which one
holds the decision.

**What was actually true:** the decision is taken, and stated more sharply than
the criticism: `standalone_direction.md` says **"one workbench model, multiple
hosts"** and *"standalone mode should not become a separate product with a
separate interaction model or a separate scene/state architecture"*, and
sequences standalone as the last major step before 1.0.

**What would prevent it:** index entries that say what a document *decides*, not
only that it exists. One clause per line — "`standalone_direction.md` — the
decision: one workbench, multiple hosts" — converts a flat list into a map.

## Finding 5 — Two current-state documents disagreed about the current state (affects contributors)

`checkpoints.md` carries a section *"Phase 5 endpoint isolation (in progress,
2026-08-02)"* describing implemented work. The master plan's execution
dashboard, which its own reporting protocol declares the authority on progress,
shows row 5 as `○ 0%`. Resolving which was true required diffing the working
tree.

The dashboard's protocol already anticipates this — it says a slice is opened by
changing its row to `◐` — so the rule exists and was not followed. That is worth
noting precisely because it is the failure mode the protocol was written to
prevent: a reader who trusts the dashboard concludes Phase 5 has not started.

## Finding 6 — Vision material has no reading order (affects contributors)

Concluding that the project "does not compete with desktop tools, and is right
not to" survived until `render_quality_vision.md` and
`future_vision_beyond_1_0.md` §5 were opened — both of which plan exactly that
competition, in detail, including the Blender/MolecularNodes bridge and
editorial-resolution export.

`devguide/README.md` has an explicit "Read first" order for contracts, rules and
architecture, and none for vision and direction documents, which sit among
roughly fifty top-level files. The consequence is that the project's most
ambitious thinking is the least likely to be found.

---

## Recommendations, by audience

**README (a prospective user, first ninety seconds):**

1. Show a non-MolSysMT object going straight into `new_view` (finding 1).
2. End the quickstart with the reproducibility round trip (finding 2).
3. Consider moving the sixty-bullet feature inventory below the quickstart. It
   answers "what else does it do", which is the second question, not the first.

**`devguide/README.md` (a new contributor, first hour):**

4. Annotate index entries with what each document decides (finding 4).
5. Give vision/direction documents a reading order, as contracts already have
   (finding 6).

**Documentation discipline (everyone):**

6. Behavioural claims belong in the normative document with a test behind them;
   vision documents state intent and label it as intent (finding 3).
7. When a document records "Estado Final de Implementación", that section is a
   claim about code and should be verified like one — this is
   `engineering_rules.md` §5's *verify documentation against the code* applied
   to the documents rather than to the code.
8. Follow the dashboard's own opening protocol (finding 5).

## What this document does not claim

- That the documentation is bad. It is unusually thorough; findings 3–6 are all
  consequences of *volume*, not absence, and volume is a better problem.
- That any of these is a defect in the software. Only finding 3 touches code,
  and only to ask which of two accounts is true.
- Any authority over the README. What a project leads with is a positioning
  decision, and this document is evidence for it, not the decision itself.

---

## Closure, 2026-08-06

Acting on this document required executing every claim in it, including its own.
That turned up more than it reported.

**Finding 1 — fixed, and the reported cure was too small.** The README now
passes an `mdtraj.Trajectory` straight into `new_view`, and states the mechanism
(`new_view` hands the object to MolSysMT's `convert`) rather than a list. Three
input types were verified end to end: `mdtraj.Trajectory`, `MDAnalysis.Universe`
and an OpenMM topology.

**But this document's own claim about selection dialects was false.** It states
that "`syntax=` accepts other selection dialects". Measured: of the seven
declared syntaxes, `MolSysMT` and `MDTraj` parse selections from any form;
`MDAnalysis` parses only from a PDB file or an MDAnalysis object, because
`molsysmt.MolSys → MDAnalysis.Universe` is not implemented; `Amber` and
`NGLView` raise; `ParmEd` and `MolSysMT_NEW` are declared but absent from the
dispatch tables, so they pass argument digestion and then fail inside `select`.
The README therefore promises two dialects, not six. Reported upstream as
`molsysmt/devguide/pending_proposals/declared_selection_syntaxes_without_implementation.md`.
This is the same defect the document is about, committed by the document.

**Finding 2 — fixed.** The quickstart's last snippet is the round trip, with a
sentence naming what happened. Verified: regions, visibility, representations
and shape overlays all survive `export_state` → JSON → `import_state`.

**Finding 3 — already closed** by Contract S10 in `scene_contracts.md`;
`whole_representation_succession_semantics.md` is archived. The contradicting
section of `areas_of_opportunity_analysis.md` is now flagged in the index.

**Finding 4 — fixed.** `devguide/README.md`'s Standalone list says what each
document decides, starting with the decision itself. Annotating them surfaced a
document whose premise is dead: `standalone_performance_and_depythonization.md`
argues from Numba JIT cold-start latency, and MolSysMT no longer uses Numba.

**Finding 5 — already closed.** The dashboard row for Phase 5 reads `◐ 60%` and
agrees with `checkpoints.md`.

**Finding 6 — fixed.** The Project direction list is ordered and annotated: what
the product is, what 1.0 scopes, what comes after. `render_quality_vision.md`'s
entry now states outright that the project *does* intend to compete with
desktop-quality rendering, which is the misreading the finding recorded.

### What acting on it revealed that it did not report

**The README had never been executed.** Three of its five quickstart snippets
could not run: `regions["chain-A"]` (`make_regions_by(element="chain")` produces
`"A"` and `"A__2"`), `n_atoms` and `ms` undefined, `origins` omitted although it
is a required argument, and an addon registration pattern superseded by
`addons.register_module`. A reader who copies the second snippet gets a
`KeyError` on their second command. This is worse than either finding above, and
a first read did not catch it because a first read does not run the code.

`tests/test_readme_quickstart_runs.py` now executes every quick-start block with
`UserWarning` escalated to an error, and asserts the reproducibility claim
rather than merely the absence of exceptions. Mutation-verified: removing the
representation before `hide()` — the exact shape of the original defect — and
breaking the `import_state` line each turn it red.

**Documentation prose is not executed anywhere.** 259 python blocks live in 63
`.md` files under `docs/content/`. The notebooks are executed by
`docs/execute_notebooks.py`; the markdown is not executed by anything.
`docs/content/user/overlays/shapes/vectors.md` was broken in its *Minimal
example* — bare arrays where units are required — and had been for as long as
units were enforced. Fixed here, along with a parameter table that described a
required argument as optional. **The other 62 files are unverified.** A test in
the shape of `test_readme_quickstart_runs.py`, applied per page with fixtures
for shared context, would close this; it is not attempted here because most
blocks depend on names defined in prose around them and the work is a project,
not a fix.

**A small state defect.** `export_state()` → `import_state()` → `export_state()`
returns an identical document except `order_high_water_mark`, which grows by 4
on every cycle: `_restore_high_water_marks` runs before the regions are
recreated, and recreating them advances the counter past the restored value.
Region `order` values themselves are preserved, so this is cosmetic — but it
defeats `restored.export_state() == state`, which is the first check a user
writes to convince themselves the round trip worked. Worth a look when Phase 5
frees up; not worth a hurried fix inside ordering semantics.
