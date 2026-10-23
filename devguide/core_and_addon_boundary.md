# Core visualization and add-on tools — product boundary

**Status: approved and normative for development — 2026-10-22.** The principal
maintainer accepted this boundary after reviewing native Studio integration,
explicit reconciliation and the MolSysMT add-on alternative. This is a local
product architecture decision. It does not change runtime registration, declare
an add-on available, retire an API or authorize a release.

## Product identity

MolSysViewer provides molecular visualization and exploration without add-ons.
Its core includes calculations whose direct purpose is to create or configure
visual content. Add-ons provide additional scientific analysis, molecular
preparation and editing tools, and domain-specific models and workflows.

MolSysMT remains the required scientific backend for the core. Optional access
to a MolSysMT tools interface is a different responsibility from that backend
dependency. Scientific algorithms, validation and molecular semantics remain
with their scientific owner; Viewer owns scene integration and presentation.

## Classify the user's intended action

| Intended outcome | Product owner |
| --- | --- |
| Load molecular data, inspect/select it, navigate structures and manage reproducible views | Core visualization and exploration. |
| Create, inspect or style regions, representations, annotations, shapes, measurements or interaction visuals | Core scene domains. |
| Calculate a supported result to add or configure visual content, such as displaying hbonds or coloring groups by SASA | The relevant core scene domain may offer a visual convenience operation over the scientific provider. Each integration still needs its own contract and qualification. |
| Remove atoms, repair/protonate/solvate a system, transform its coordinates or run a general scientific analysis | MolSysMT tools or another owning add-on/scientific library, using shared Viewer integration when applying an edit/result. |
| Work with a specialized domain model, such as a pharmacophore, cavity model or elastic network | The owning domain add-on. Core shapes, colors and plots remain reusable rendering tools. |

Examples refine the boundary; they do not promise unimplemented controls.
Showing principal axes adds geometry; aligning molecular coordinates to those
axes edits the system. Drawing the periodic cell is visual; assigning its
matrix edits molecular data. Hiding water changes visibility; removing its
atoms changes the molecular system. Secondary structure, chemical features,
scalar properties and structure series can supply visual content where a
specific integration is justified.

Being drawable or plottable does not by itself make every scientific workflow
core. Review the primary user intent, required domain model and reusable scene
owner. A domain add-on can calculate a result and use the same generic core
renderer without moving its entire scientific workflow into Studio. Preserve
established loading, extraction, persistence and editing APIs until an explicit,
qualified migration changes their contracts.

## Calculations offered through a visual operation

The action must make its selection, structures, reference/state where relevant,
method, units and consequential scientific options explicit. Reuse the actual
provider tools; do not duplicate a detector or property algorithm inside a panel.
Preserve provider stability/experimental labels, prerequisites, diagnostics and
actual producer provenance. Do not silently add hydrogens, change protonation,
align coordinates or perform another preparation step to make a visual request
succeed. Explain missing prerequisites or offer a separate explicit operation.

Keep the scientific result distinct from its visual representations. Reuse a
compatible existing result where appropriate; making it visible again must not
require recalculation. Multiple visual sets can refer to one result. Hiding or
deleting a representation does not delete its underlying scientific analysis.
Deletion of scientific data is a separate explicit operation. Preserve frame
coverage, correspondence, units and applicability; stale or unevaluated data
must not look like a current calculation or a genuine zero result.

Storage and persistence remain domain-specific. Named Interactions belong to
the molecular analysis owner; this decision does not introduce a universal
result store or promise that H5MSM serializes every result. Follow the existing
[scene](scene_contracts.md), [Interactions](interactions_compatibility_contract.md) and
[reproducibility](session_reproducibility.md) contracts.

## Python, Studio and add-on integration

The Python API remains the primary, headless and composable foundation. Studio
organizes visual intent and scene objects. Add-on panels organize the additional
scientific tools. Both reuse public scientific tools and qualified Viewer
integration; private coordination must not become an alternative scientific
implementation or a GUI-only capability. Panel placement does not prescribe
new Python namespaces or one method per button.

The accepted direction reopens a MolSysMT tools add-on. Its expert API mirrors
the scientific module/function hierarchy, binds the primary system to the
current `view.molsys` and aims at broad public-tool coverage. Its graphical
interface uses understandable tasks independently of that expert hierarchy.
See [the approved add-on direction](molsysmt_tools_addon_plan.md): preserve native
mutation/return semantics, synchronize bound-system edits by default and adopt
independent results only explicitly. Deferred synchronization requires qualified
maps, safe pending state and recovery without repeating completed science.
Exact receiving APIs, installation/discovery and panel layout still need
implementation contracts and qualification.
The runtime still refuses the retired legacy MolSysMT root entry point under
uibcdf/molsysviewer#186. The redesigned provider-owned source integration uses
`molsysviewer_molsysmt.tools` for discovery. Its source facade exposes bound
`basic` queries, extraction, copies, conversion/preflight, removal and retained-axis
coordinate/box setting under `view.addons.molsysmt`, with lazy per-view state and
closed-view guards. Broader tools, edit families and panels remain pending in
uibcdf/molsysmt#421/uibcdf/molsysviewer#264. Source receiving does not establish
compatibility for a published package pair.

General automatic observation of external MolSysMT/native writes is not a
requirement of this direction. Direct Python edits need explicit qualified
reconciliation. An integrated add-on operation can coordinate its own edit and
update through the same Viewer boundary. Deferred updates/batching require a
contract for pending synchronization, old-to-new maps, safe scene actions,
errors and final reconciliation; a boolean alone does not establish that
contract. Independent returned systems require explicit incorporation. Managed
molecular Undo needs pre-edit retention and its own resource/recovery policy.

The current advanced boundary is `view.apply_system_edit(...)`, with its
documented invalidation/history limits. The design discussion is
uibcdf/molsysmt#413. After the provider proposed explicit reconciliation, the
consumer withdrew the general observer request and said the issue may close
without a new provider deliverable. Concrete operation-specific gaps found
during receiving will be reported separately.
Do not infer new provider notification APIs or remove Viewer setters from this
decision.

## Add-on documentation and catalogue ownership

MolSysViewer owns documentation of what addons are, discovery, registration,
activation/deactivation, configuration, compatibility and lifecycle. It also
owns the guide for creating an addon against its public extension contracts and
a maintained catalogue linking to the owning components.

Each component documents what its addon offers and how to use it: the expert
API, graphical tools, scientific methods, prerequisites, examples and limits.
Link to that reference from Viewer instead of duplicating it. Viewer tutorials
may use addons within a visualization workflow, linking scientific details to
the owner. This division applies to suite components and independent providers.

Third-party authors request catalogue inclusion through a MolSysViewer issue,
with the addon name, purpose, maintainer, package/source, documentation,
installation route and declared compatible versions. Catalogue maintenance is
an editorial task, separate from runtime discovery/registration and installed
qualification. Adding a listing does not require adding a hardcoded discovery
module. The public catalogue explains this request route and links the creation
guide; providers keep their usage documentation in their own projects.

## Supersession and documentation

This decision supersedes the earlier proposal to put general molecular editing,
Build, Topology, Structure and Properties tool panels in native Studio and the
requirement for automatic linked-system observation. Earlier operation
inventories, recovery scenarios and UI prototypes remain design inputs; their
old panel placements and synchronization choices need reassessment under this
boundary. They are not implementation instructions.

For every new capability, document its scene/add-on owner, scientific effects
and current availability. Explain the boundary in the user introduction and
add-on guide. Keep planned examples visibly distinct from implemented features.
The withdrawn native-Studio expansion plan was removed at the maintainer's
request; Git retains its history. The [operation inventory](studio_molsysmt_operation_inventory.md)
and [reconciliation review](linked_molecular_edits_design.md) remain design
inputs. The separate [MolSysMT tools add-on plan](molsysmt_tools_addon_plan.md)
records the accepted API/GUI, edit/update and lifecycle policies with the planned
implementation sequence. Its remaining receiving details need review; the retired expansion
plan is not reused as its implementation plan.
