# Competitive positioning

**Status:** position record. It states what MolSysViewer competes on, what it
concedes, and why. It is not a roadmap and it commits nothing to a date.

**Why it exists:** `development_mantra.md` and `guiding_principles.md` say what
the product *is*. Nothing said what it is *against*. Before 2026-08-03 the only
mentions of PyMOL, ChimeraX or VMD in this repository were as sources of UI
ideas (`strips.md`, `interaction_modifiers_and_future.md`). A project can drift
for a long time on a clear identity and an unexamined comparison.

---

## 1. The field, and where the real contest is

Two groups are usually named as competition, and only one of them is:

- **Notebook viewers** — NGLView, py3Dmol, recent Mol\* bindings. This is the
  category MolSysViewer is in. NGLView is widely used and largely unmaintained;
  py3Dmol is a thin wrapper over strings. The bar here is lower than its
  install counts suggest.
- **Desktop applications** — PyMOL, ChimeraX, VMD. Decades of work, teams,
  and specialist domains.

The instinct is to say the second group is out of reach. That instinct is a
category argument, and category is the wrong variable. The right one is **where
the working loop closes**.

## 2. The structural advantage: direction of dependency

PyMOL and ChimeraX both expose Python. The difference is not the presence of an
API, it is which side owns the model:

- In a desktop application, Python is a **scripting language inside the app**.
  The authoritative state lives in the application; the API is a remote
  control. Bringing that into a numpy/pandas/Jupyter workflow is possible and
  permanently awkward.
- In MolSysViewer, the viewer is a **library inside the user's Python**. The
  authoritative state is a Python object graph the caller already owns.

Closing that gap would require those tools to stop being what they are. This is
why NGLView and py3Dmol have real traction despite being far weaker
technically: the inversion matters more than the feature list.

A second consequence is usually missed. The analysis toolkit that surrounds a
library-shaped viewer is **larger than anything that fits inside a desktop
application**. MolSysViewer does not have to reproduce twenty years of
specialist tools, because it is not its own catalogue that competes — it is the
scientific Python ecosystem plus MolSysMT.

## 3. The entry ramp, currently invisible

`load_from_molsysmt` passes the user's input straight to
`msm.convert(..., to_form="molsysmt.MolSys")`. MolSysMT's `form/` directory
covers `MDAnalysis_Universe` / `AtomGroup` / `Topology`, `mdtraj_Trajectory` /
`Topology` and its file handlers, biopython objects, and roughly twenty file
formats; `syntax=` accepts other selection dialects (Amber, MDTraj, …).

So a user who lives in MDAnalysis or mdtraj **converts nothing**. That is the
single easiest advantage to communicate in this whole document, and it is the
one a newcomer cannot see: the README quickstart shows `new_view("1TRS")` and a
MolSysMT `MolSys`, and never shows an `mdtraj.Trajectory` or an MDAnalysis
`Universe` going in directly.

**Action:** this belongs in the first-contact onboarding gate (#12 in
`path_to_1_0.md`), not in a vision document.

## 4. What is conceded, and which concession is structural

Three gaps against the desktop tools are real. They are not equivalent.

| Gap | Nature | Route |
|---|---|---|
| Offline photorealistic rendering | Feature gap, cheap to close | Do not build a ray tracer. Bridge to Blender. See [`render_quality_vision.md`](render_quality_vision.md) and [`future_vision_beyond_1_0.md`](future_vision_beyond_1_0.md) §5 |
| Multi-million-atom systems, cryo-EM volume work | **Platform gap — the only structural one** | WebGL2 in a tab against native GPU. The native path is the standalone host; the numbers come first, from Phase 8 of the master plan |
| Twenty years of specialist tools (map fitting, interactive refinement, morphing) | Domain breadth | Not an obligation. Domains arrive as add-ons when someone needs them — which is what the add-on system is for |

Only the middle row cannot be closed by choosing what to work on. Today its
real ceiling is unmeasured, which is itself the argument for keeping the Phase 8
scale matrix a gate rather than a nicety.

Note what is **not** on this list: rendering quality in the interactive case.
Mol\* is state of the art and RCSB PDB ships it.

## 5. The agent-facing advantage

The desktop tools were shaped around a human at a GUI, with a command language
added later. The consequence is the same one as §2, seen from a different side:
**an agent driving them can act but cannot know.** It emits a command and, to
learn what happened, must inspect pixels or interrogate the application piece by
piece.

MolSysViewer's advantage here was not designed for it. **The reproducibility
thesis and the agent thesis are the same thesis**: *interaction becomes
explicit, queryable, replayable state* is what a scientist needs to reproduce
work and what an agent needs to operate at all. Four mechanisms already built
for other reasons serve it directly:

- **Queryable authoritative state.** `view.regions`, `view.scene_objects`,
  `export_state()`. An agent holding a model can reason; an agent holding a
  remote control cannot.
- **Command deduplication (R1).** One accepted command yields one public-API
  mutation and one history checkpoint. That is precisely the property an agent
  retry loop needs so a retry does not double-apply. Built for wire
  correctness.
- **Argument digestion.** For an agent, error quality *is* the interface: it
  recovers from an error that names what was wrong and flails on an opaque one.
- **Observable failure**, quality target #6 of the master plan: rejection,
  timeout, corruption and fallback all leave a diagnostic.

And one that is nearly free: **`build_popup_scene_snapshot` is already the
canonical current-state projector over the live registries.** An agent-facing
`describe`-style scene summary is that same projector with a different
serializer — a new output of existing work, not new work.

### The distinction against the copilot idea

[`future_vision_beyond_1_0.md`](future_vision_beyond_1_0.md) §3 proposes an LLM
**inside** the viewer translating natural language into API calls. This section
is the inverse and the larger of the two: the viewer as a first-class instrument
for agents that live **outside** it. It requires no LLM integration at all — only
that the API surface, the legibility of state, and the visual feedback loop
(headless render to image) be good. Cheaper, and more defensible.

### The discipline that keeps this honest

Do not bet the product identity on a trend. The filter:

> **Pursue an agent affordance only where it is the same work as
> reproducibility.** If something serves agents only, it is speculation.

Almost everything above passes that filter, which is exactly what makes the bet
cheap. What would *not* pass — an MCP server, a machine-readable API schema, a
context-window-shaped scene description — stays out of the 1.0 scope and is
judged separately, on its own evidence, if and when it is proposed.

---

## 6. Two different targets, one shared core

"Good with AI" is two design problems, not one, and they pull in different
directions. Conflating them produces a tool that is mediocre at both.

- **Target A — the agent operates the viewer.** No human watches each step.
- **Target B — the human operates the viewer, assisted.** The human is present,
  has eyes, and is the judge.

### Target A: what an agent is actually short of

An agent's loop is intent → act → observe → decide, and the scarce resource is
**observation**, not action. Emitting a call is easy; knowing what happened is
the whole problem.

1. **State legibility beats images.** A rendered PNG is a weak and expensive way
   for a model to perceive a 3D scene. The structured description is the primary
   channel and the image is confirmation, not evidence.
2. **The context window is the real budget.** A description whose size grows
   with the scene will not survive a real system. This argues for a
   **hierarchical, queryable** description — a summary with handles that expand
   on demand — rather than one exhaustive blob. Note that the existing canonical
   projector already scales with *current scene* rather than session length,
   which solves half of it; scene content itself is the remaining half.
3. **Nothing may be confirmable only by looking.** Any capability whose sole
   feedback is visual is invisible to an agent. This is the same requirement as
   `engineering_rules.md` §4's rule against tests that assert only the message
   they sent, arriving from the other direction.
4. **"Not told" must never look like "nothing there."** Contract S7 already says
   this for damaged anchors. For an agent it generalizes: a plausible wrong
   answer costs more than a loud refusal, because the agent will act on it.
5. **Retry safety**, already provided by R1 deduplication.
6. **Runtime discoverability.** A niche library is not in a model's weights, so
   the public surface must be introspectable at runtime or the agent guesses
   method names. The argument-digestion metadata is the raw material.

### Target B: what an assisted human is short of

Completely different. The human sees the scene, so the visual channel is free.
What is scarce is **shared reference** and **trust**.

1. **Deixis.** "this loop", "that residue", "the thing I just clicked". The
   assistant is useful in proportion to how well it knows what the human is
   attending to. `active_selection`, `hover_target`, the current camera and the
   last interaction stop being telemetry and become **the context of the
   conversation**.
2. **Reversibility outranks correctness.** A wrong agent action wastes tokens; a
   wrong assistant action destroys a human's work in progress and their trust.
   Undo must cover everything the assistant can reach — no exceptions, because
   the exception is what the user will hit.
3. **Attribution.** The human must be able to tell what the assistant did from
   what they did. This is exactly
   [`pending_proposals/post_1.0/scene_object_owner_field.md`](pending_proposals/post_1.0/scene_object_owner_field.md),
   filed for add-ons: *an add-on's shape is indistinguishable from one the user
   drew*. An assistant makes that gap sharper and more urgent than an add-on
   does.
4. **Explanation in the product's vocabulary.** The assistant reports in
   `regions` / `layers` / `selections` / `annotations`, never in Mol\* internals.
   Otherwise it teaches the user a model the API does not have.
5. **Interruptibility.** An assistant that blocks the canvas while it thinks is
   worse than no assistant.

### The rule that governs both

> **An assistant is a GUI.**

`engineering_rules.md` §1 already states that the GUI never reaches past the
public Python API. That rule must bind an in-viewer assistant with no softening,
and it is the single most important decision in this whole section. An assistant
with a privileged path — direct Mol\* calls, a side channel, its own state —
would produce scene state that is not reproducible, not undoable, and not
exportable, and it would do so **silently**, which is how the System subpanel's
colour dropdown was lost for months. The failure mode is identical and the
lesson is already paid for.

The corollary is pleasant: if the assistant only uses the public API, then
everything it does is already reproducible, replayable and exportable, for free.

### What is shared, and what actually diverges

| Concern | Target A | Target B | Shared? |
|---|---|---|---|
| Complete, honest public API | required | required | **yes** |
| Error quality (names the fix) | interface-critical | helpful | **yes** |
| Queryable authoritative state | required | required | **yes** |
| Undo coverage and attribution | useful | critical | **yes** |
| Determinism / replay | required | required | **yes** |
| Description under a context budget | **critical** | irrelevant | no |
| Shared referents / deixis | irrelevant | **critical** | no |
| Headless render to image | confirmation | the human's eyes | no |

The shared column is not new work. It is the pre-1.0 programme already in
flight, read through a different lens. Only the two divergent rows are new, they
are both post-1.0, and they are cheap **only** because the shared column is done
first. Building either divergent half on an incomplete API would produce a
demo, not a capability.

### A decision this already informs

[`archive/opt_in_hover_telemetry.md`](archive/opt_in_hover_telemetry.md)
resolved one product question: what `view.hover_target` means when telemetry is
off. Target B informed the selected answer. If hover is how an assistant knows what
the human is looking at, then a `hover_target` that silently reports "nothing
hovered" when the truth is "not being told" does not merely mislead a user — it
makes the assistant confidently wrong about the one thing it most needs to be
right about. The proposal's first option (an explicit *telemetry disabled* state
that `info()` reports honestly) is the only one compatible with this section.
That is why the explicit `telemetry_disabled` option was selected and
implemented, rather than silently reporting an empty target.

---

## What this document does not claim

- That the desktop tools are behind. They are ahead on the axes in §4.
- That agent usage is a demonstrated market. It is a positioning bet whose cost
  is near zero because the work is already required for reproducibility.
- That any of this changes the 1.0 gates. It changes emphasis inside gate #12
  and nothing else.
