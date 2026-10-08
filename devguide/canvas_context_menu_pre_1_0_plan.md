# Canvas context menu: accepted pre-1.0 redesign

**Decision — 2026-10-08:** the principal maintainer accepts this redesign as
required before 1.0 (`uibcdf/molsysviewer#179`). **Implementation delivered; human acceptance pending:** the
menu shell, shared scene/Studio navigation, molecular-target and object/occurrence
workflows are delivered; human acceptance remains pending.
The [owning report](pending_proposals/canvas_context_menu_target_actions.md)
records the inspected findings. Current executable contracts are maintained in
[`interaction_gestures_and_menus.md`](interaction_gestures_and_menus.md) and
[`scene_contracts.md`](scene_contracts.md) alongside this implementation.

## Release boundary

Publication is paused for both Viewer and MolSysMT: neither 1.0 is requested or
authorized. Viewer 0.24.1 build 1 / `ae1fb995` remains an immutable staging
checkpoint and will be superseded as the next candidate by the menu changes.
Choose the next pre-1.0 version/build/source after implementation and review.
Preserve old tags, branches, files, hashes and gate verdicts; do not transfer
their qualification to new code. Public baseline remains Viewer 0.24.0 build 1
and MolSysMT 0.23.0 ABI3 build 0.

## Product contract

Opening or dismissing the menu leaves scene and active selection unchanged.
Identify the target separately from the active selection; direct creation uses
the target without implicitly replacing the selection. Right drag continues
to pan. Geometry, scene objects, interaction data and selection semantics stay
in their existing owners. Studio remains the configuration and collection editor.

Use compact root entries and normally one submenu level. Do not enumerate all
saved selections or build full collection editors in the menu. Related regions
are restricted to actual target overlaps. Ellipses indicate an editor/form;
stateful choices show their state; action names explicitly identify their scope.
Offer executable operations, with meaningful disabled explanations where needed.

The layouts below are discussion labels in Spanish. Implementation follows the
existing application's language consistently; this work does not introduce a
localization framework.

## Accepted layouts

### Molecular target

```text
ALA 42 · cadena A · Proteína
Átomo señalado: N

Enfocar
Inspeccionar…
Seleccionar                 ▸
Crear                       ▸
Medir                       ▸
Interacciones               ▸
Regiones relacionadas       ▸

Selección actual · 18 átomos ▸
─────────────────────────────
Vista                       ▸
Deshacer
Rehacer
Abrir Studio…
```

Include residue identifier, chain and source when available, plus the identified
atom. Selection supports explicit replace/add/remove and one-shot atom, residue
or chain actions according to target information. Global picking preferences
remain deferred under #45.

Create region or annotation directly from the target. Shape creation opens an
appropriate prefilled Studio workflow where supported. Configuration makes the
chosen atom scope visible. Region creation is the existing route to a separate
representation and visibility; preserve hide versus disable and Whole ownership.
Arbitrary atom-hide masks and new isolation/show-only UX are outside this work.

Measure exposes distance, angle and dihedral with visible pick progress and
explicit endpoint policies. Do not silently substitute a centroid or
representative atom for an atom-based operation. Existing managed measurements
remain replayable objects; no redundant save-last-measurement workflow is needed.

Interactions opens existing-data inspection, display configuration or calculation
in Studio with a declared target scope. Calculation confirms name, method and
structure scope; opening a menu never computes or assumes all frames. Retain the
experimental classification and existing calculation guards.

The active-selection section names its actual content, including mixed scene
objects. Offer applicable focus/inspect/save/create/expand/clear operations and
route advanced selection configuration to Studio. Molecular actions require
atom indices; a shape-only selection must not advertise an executable atom query.

### Interaction occurrence

```text
Puente de hidrógeno · hbonds-proteína
N–H···O · estructura 2

Inspeccionar esta interacción…
Seleccionar participantes
Enfocar participantes
─────────────────────────────
Conjunto «hbonds-proteína»    ▸
─────────────────────────────
Selección actual             ▸  [cuando exista]
Vista                       ▸
Deshacer
Rehacer
Abrir en Studio…
```

Inspect the clicked occurrence with roles, participants, measures/units and
available periodic metadata. Set operations explicitly focus/hide/configure or
remove the graphical representation. Stored-analysis deletion stays in its
existing dedicated management flow; do not imply an occurrence editor exists.

Resolve the pick against frame, analysis version and query/filter revision with
bounded occurrence lookup/inspection. Current observation APIs require a matching
inspected page; adapt that seam without removing checks or materializing the
trajectory. Close or invalidate a menu whose context becomes stale.

### Empty canvas

```text
Canvas

Restablecer encuadre
Enfocar todo
Selección actual             ▸  [cuando exista]
─────────────────────────────
Vista                       ▸
Deshacer
Rehacer
Abrir Studio…
Ayuda
```

Shared view/history/Studio access is also available on object targets. View
contains light/dark background, automatic rotation, swing and viewer modes with
explicit state. Reuse the single scene history and truthful can-undo/can-redo;
do not promise undo of every calculation or molecular-system mutation. Remove
Hide Canvas from the ordinary contextual menu; retain layout controls in their
existing owning surface.

### Other objects

| Target | Applicable operations |
| --- | --- |
| Annotation | Edit text, focus anchor, explicitly select associated atoms, hide, delete annotation. |
| Shape | Edit appearance, focus meaningful geometry bounds/anchors, explicitly select associated atoms when available, hide, delete shape. |
| Measurement | Inspect value/units, focus endpoints, select endpoint atoms, edit appearance, hide, delete measurement. |
| Related region | Open its Studio context, focus, and explicitly scoped visibility/activation actions. |

Unsupported focus must not silently do nothing. Core and addon contributions
share applicability rules; addon entries remain context-specific and grouped.

## Implementation sequence

Stage 1 now provides in-card submenus, target/active-selection headings,
keyboard/ARIA/focus ownership and menu-first Escape. View controls, authoritative
history availability and section-aware Studio opening have also landed ahead
of their stages. Browser-owned navigation is consumed locally; backend-owned
mutations have one dispatch. View toggles carry an explicit requested state so
the Python echo does not toggle them again. The owning report records validation
and outstanding work; this foundation does not close #179.

Stage 2 resolves explicit replace/add/remove target selections in the canonical
MolSys atom space, with atom/residue/chain scopes. Target region and annotation
composers leave the active selection intact. Read-only target inspection and
staged Shapes/Interactions navigation reuse Studio owners; Interactions staging
neither calculates nor silently applies a display filter. The form starts with
target A and current-structure calculation scope, and asks for a name. Measure
has three actions and an explicit endpoint selector; progress names the policy,
and individual-atom mode refuses ambiguous multi-atom picks. Load/clear/frame
changes dismiss the menu and its read-only target snapshot.

Stages 3–4 now connect clicked occurrences through one bounded, identity-checked
inspector page, and reuse participant selection/focus and graphical-set owners.
Object menus open the existing annotation/shape/measurement editors; free
geometry can focus its real Mol* bounds without claiming associated atoms.
Contextual Hide requests an explicit hidden state. Related regions open their
Studio inspector; empty canvas offers orientation-preserving Focus All and the
existing Help overlay where its owner is available. The final extended browser guard passes; the
maintainer's notebook/popout acceptance remains a separate gate.

1. **Menu shell and context contract.** Extract reusable target/action
   applicability, add bounded submenus and meaningful headings, implement
   keyboard/ARIA/focus and menu-first Escape. Preserve click-versus-drag behavior.
2. **Molecular workflows and Studio navigation.** Explicit target selection,
   target-based region/annotation creation, simple measurement entry points,
   active-selection operations and section-aware Studio opening. Use common
   dispatch/owners and correct panel labels/routing.
3. **Object and occurrence workflows.** Annotation/shape/measurement actions,
   bounded clicked-occurrence inspection and participant selection/focus,
   graphical-set scope, frame/revision refusal, and meaningful focus availability.
4. **Common scene actions and consistency.** View controls and scene history on
   all targets, truthful states, applicable addon entries, unit handling and
   consistent behavior in the main canvas and supported popouts/export hosts.
5. **Verification and human review.** Focused owner tests, real Mol*/Chromium
   regressions, then the principal maintainer's remote-Jupyter review. Update
   current contracts/user guidance, archive #179 with adopted addressable guards,
   review accumulated changes and choose the next candidate. Qualify its exact
   source/bytes/dependency closure before any separately authorized publication.

## Acceptance scenarios

The first human review (2026-10-08) finds two failures: missing boundary peptide
half-links after contextual region creation and an unpickable translucent sphere.
The corrections pass the expanded real-pointer/geometry guard; repeat these two
scenarios in the maintainer's notebook before accepting #179. Details and
validation scope remain in its owning report.

- Right-click residue B while a working selection contains residue A: opening,
  dismissing, inspecting and creating from B preserve A until an explicit
  selection operation. Replace/add/remove have distinct observable results.
- Pick atom, residue and chain deliberately; molecular headings and generated
  regions/annotations reflect the chosen scope and source identity.
- Measure with an explicit endpoint policy and visible remaining picks; confirm
  that the resulting managed object has the correct value and units.
- Pick one interaction among parallel observations, on a nonconsecutive selected
  frame: inspect the correct occurrence and select/focus its participants.
  Frame/filter/analysis changes invalidate the old reference. Query stays bounded.
- Hide a graphical interaction set without deleting its stored analysis. Verify
  region hide/disable ownership, shared representations and persistence unchanged.
- Handle free-position shapes, annotations, measurements and mixed selections
  without misleading atom actions or ineffective focus entries.
- Access view/history/Studio from populated and empty canvas. Escape closes the
  menu first; keyboard navigation, focus return and canvas-edge positioning work.
- Verify main canvas and supported popup paths, plus truthful availability in
  static/exported hosts. Qt remains experimental and remote remains post-1.0.

Completed slices do not imply human acceptance of the full redesign or
replacement-package qualification. Preserve separate evidence scopes.
