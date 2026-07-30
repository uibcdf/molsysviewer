# Post-1.0 proposals

Everything in this directory is deliberately outside the 1.0 release gate.
Documents may be approved designs, benchmark-gated architecture work, or
upstream-dependent ideas.

## Suggested order after 1.0

1. `interactions_domain.md` and
   `studio_interactions_subpanel_ui_design.md`: the next major scientific scene
   domain, already designed. Implement it in vertical slices:
   - canonical Python manager and immutable records;
   - calculation adapters and explicit imported pairs;
   - state, history, rebuild, broken references, and frame semantics;
   - frontend rendering;
   - Studio subpanel last.
2. `canvas_picking_level.md`: self-contained interaction UX.
3. `structure_windowing_and_lazy_materialization.md`: decide the public meaning
   of resident versus available structures before implementing a cache.
4. `multiview_split_screen.md`: depends on the pre-1.0 runtime router and popup
   ownership contract.
5. Advanced annotations, representations, chemical metadata, typing generation,
   and test-output studies as their use cases or upstream contracts mature.

The array-native transport for fully materialized structures and the runtime
router moved to active pre-1.0 proposals. Lazy structure sources, partial
residency, and cache eviction remain deferred because they change the meaning of
`view.molsys`. `zero_copy_visual_rendering.md` is feasibility analysis, not a
second transport specification.

## Entry gates

| Work | Start only when |
|---|---|
| Interactions | 1.0 API freeze has ended and MolSysMT calculation vocabulary is confirmed |
| Canvas picking | desired levels and Mol* granularity behavior are verified against local `src_molstar` |
| Structure windowing | MolSysMT vocabulary, `view.molsys` semantics, add-on behavior, edits, and materialization are specified |
| Multiview | view/session identity and command routing are stable |
| Chemical metadata | MolSysMT publishes the canonical SDF/MOL2 metadata contract |
| Advanced MVS annotations | a real use case requires MVS machinery beyond current labels |
| Advanced representations | a scientific workflow selects a concrete representation and acceptance fixture |
| Generated mixin typing | public API churn is low enough for generated declarations to remain useful |
| Test-output study | measured token cost shows a meaningful iteration penalty |

## Completion discipline

Every implementation starts from one document, names the public contract it
changes, and includes serialization in the same slice for user-created state.
Render claims require Mol* real; performance claims require recorded fixtures
and commands. Once the work is implemented and documented durably, remove its
proposal rather than leaving a completed plan in this directory.
