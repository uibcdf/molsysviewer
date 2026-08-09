# Post-1.0 proposals

Everything in this directory is deliberately outside the 1.0 release gate.
Documents may be approved designs, benchmark-gated architecture work, or
upstream-dependent ideas.

## Suggested order after 1.0

1. `representative_scale_followups.md`: the canonical performance strategy
   derived from the pre-1.0 representative-scale gate. Start with its topology
   v2 prototype and observability work; structure residency remains gated by the
   separate windowing contract.
2. `interactions_domain.md` and
   `studio_interactions_subpanel_ui_design.md`: the next major scientific scene
   domain, already designed. Implement it in vertical slices:
   - canonical Python manager and immutable records;
   - calculation adapters and explicit imported pairs;
   - state, history, rebuild, broken references, and frame semantics;
   - frontend rendering;
   - Studio subpanel last.
3. `canvas_picking_level.md`: self-contained interaction UX.
4. `structure_windowing_and_lazy_materialization.md`: decide the public meaning
   of resident versus available structures before implementing a cache.
5. `multiview_split_screen.md`: depends on the pre-1.0 runtime router and popup
   ownership contract.
6. Advanced annotations, representations, chemical metadata, typing generation,
   and test-output studies as their use cases or upstream contracts mature.

`proteinview_external_review_and_ideas.md` is an idea inventory rather than a
design, so it has no place in that order. Read it before opening any proposal in
the interaction, pocket, or agent-integration space: its §1 records which of
those features are already designed here, and its §9 records concrete defects
found in the reviewed codebase that our own code could reproduce.

`viewing_in_the_terminal.md` is a real proposal and is self-contained: the pixel
source and the CLI argument parsing already exist, so it adds one component and
two triggers. Schedule it independently — it blocks nothing and nothing blocks
it. Its interactive tier is deliberately not specified there; it is the same
machine as the agent control surface and is deferred into the review document
above.

The array-native transport for fully materialized structures and the runtime
router moved to active pre-1.0 proposals. Lazy structure sources, partial
residency, and cache eviction remain deferred because they change the meaning of
`view.molsys`. `representative_scale_followups.md` is the current performance
strategy. The older `zero_copy_visual_rendering.md` feasibility analysis was
archived after D4; it is not a second transport specification.

## Entry gates

| Work | Start only when |
|---|---|
| Performance architecture | the Phase 8 representative baseline is accepted; each optimization sets its A/B gate before implementation |
| Interactions | 1.0 API freeze has ended and MolSysMT calculation vocabulary is confirmed |
| Canvas picking | desired levels and Mol* granularity behavior are verified against local `src_molstar` |
| Structure windowing | MolSysMT vocabulary, `view.molsys` semantics, add-on behavior, edits, and materialization are specified |
| Multiview | view/session identity and command routing are stable |
| Chemical metadata | MolSysMT publishes the canonical SDF/MOL2 metadata contract |
| Advanced MVS annotations | a real use case requires MVS machinery beyond current labels |
| Advanced representations | a scientific workflow selects a concrete representation and acceptance fixture |
| Generated mixin typing | public API churn is low enough for generated declarations to remain useful |
| Test-output study | measured token cost shows a meaningful iteration penalty |
| ProteinView-inspired ideas | per-item gates in that document; none are approved designs |
| Viewing in the terminal | 1.0 API freeze has ended; no upstream or benchmark dependency |
| Export rough edges | 1.0 has shipped and the export mechanism has real external users, so "is anybody using this?" has an answer |

## Completion discipline

Every implementation starts from one document, names the public contract it
changes, and includes serialization in the same slice for user-created state.
Render claims require Mol* real; performance claims require recorded fixtures
and commands. Once the work is implemented and documented durably, remove its
proposal rather than leaving a completed plan in this directory.

[`export_rework_rough_edges.md`](export_rework_rough_edges.md) is neither design
nor defect: four accepted trade-offs from the 2026-08 export rework, written down
while the reasons were fresh so a colder reader can look for better answers. Its
item 2 wants reading together with `qt_render_check_on_a_gpu_runner.md` — both
are checks that need a machine the CI does not have, for the same reason.

`qt_render_check_on_a_gpu_runner.md` is infrastructure rather than design: the
Qt render gate is already closed on a real GPU, and what remains is a
non-blocking CI job that needs a machine with a GPU and a graphical session.
