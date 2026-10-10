# Studio interaction contract

Studio presents the native scene domains; optional domain extensions use the
Add-ons surface. MolSysMT is the required scientific backend. Its former addon
is retired: automatic discovery skips its legacy entry point before import,
and explicit registration reports the native route. Legacy `remove_selection`
does not mutate atoms or clear the active selection. Molecular editing remains
with the scientific owner and the existing explicit system-edit/loading contracts.

## Card and navigation

Floating geometry survives background lock, minimize/restore and dock/float.
Resizing the host clamps existing bounds instead of recentering the card.
Disposal disconnects host/panel observers and active global drag listeners.

Below 480 px of card body width, an owned native selector replaces the sidebar.
Wide cards use the sidebar. Both layouts select the same section/workspace;
Studio's selector follows persisted/reordered tab order and includes Settings.
The compact layout must preserve room for the editor. Hidden workspaces retain
their last layout until measurable.

Native switches, checkbox labels, row actions and form names carry keyboard
semantics. Focus is visible. Settings re-rendering preserves focused switch
activation. These requirements do not constitute a complete accessibility
certification of Mol* or arbitrary external addon content.

Shared panel re-rendering restores focus for named selects and checkboxes while
keeping their values from the canonical projection. Text edits retain their
draft/caret behavior. Accessible-name selectors escape quotes and backslashes.

## Interactions

Interactions retains its experimental notice. Saved sets are readable without
opening the creation form. Opening a form does not compute. Calculation scope
and display scope remain independent. Restricted atom calculation exposes its
selection controls; the structure field explains `current`, `all` and explicit
indices. Optional representation identifiers and scientific metadata use
disclosures; inspection retains participant identities, measurements and units.

## Export delivery

PNG dimensions derive from the renderer drawing buffer and the requested scale,
rounded exactly like the image exporter. `figure_background` projects the actual
recipe background; `figure_variants` retains its publication catalogue meaning.

Native Studio HTML export sends a request-specific transient `html_export_ready`
reply using the existing self-contained exporter. Only the requesting controller
downloads it; duplicate/shared replies do not download again. The reply bypasses
the structure stream and is excluded from popup replay storage. Ordinary Python
file export and remote URL delivery retain their contracts. HTML scene editing
requires live Python authority; standalone Qt remains experimental.

## Guards and boundaries

`molsysviewer/js/tests/e2e/studio-usability.e2e.ts` uses real pentalanine,
all-structure native hbonds, Python action replies and Chromium/Mol*. It checks
downloaded PNG bytes/alpha, actual browser HTML delivery, compact navigation,
keyboard controls, floating bounds and disposal. Controls reveal and smooth
whole-group fading retain their separate `controls-visibility.e2e.ts` guard.
`tests/test_addons.py` guards legacy refusal and native calculations.
Source validation does not qualify a frozen installed artifact or authorize
publication. The next version is agreed as 0.25.0 but remains unfrozen.

## Saved-list and creation tools (second review)

`ListSearch` owns local search state. `SavedListTools` owns native row filtering,
independent marks, exact-target deletion confirmation and correlated batch
feedback. Every native saved domain uses the tool. Searching/marking sends no
molecular action. Search changes retain marks, including filtered targets;
projection removes marks for missing targets. The optional management disclosure
keeps bulk controls out of the ordinary reading flow. Stored scientific analyses
and the Add-ons manager use the same local search primitive. Search metadata
belongs to each domain and excludes action-button captions.

`batch_scene_objects` validates the complete current target list and supported
operation before changing anything. `SceneHistory._atomic_operation` groups
existing owner operations into one undo step and restores the scene on failure.
Selections offer deletion; layers offer show/hide/ungroup for user layers only;
other saved domains offer show/hide/delete. Set deletion preserves named analyses;
layer ungroup preserves members. No new scientific computation belongs here.

Shapes creation returns transient `studio_action_result` feedback to the matching
request only. Draft/anchors clear only on Python success. Missing anchors and
invalid geometry fail explicitly, without a scene mutation. Links/arrows use
unique atoms' geometric centers at `view.player.index`, in nm, and explicitly
convert to the Å wire format. These are fixed snapshots. Atom-anchored spheres
retain their existing moving-anchor behavior. Pocket surfaces require staged
atoms; ring geometry is a supplied-geometry guide, not an aromaticity detector.
The nine advanced examples execute through real public digested Python APIs.

`PanelDisclosures` persists deliberate creation/advanced disclosure choices;
initial defaults adapt when canonical saved items first arrive. Contextual
creation deliberately opens its form. `EditorDrafts` retains secondary text
fields keyed by object/control while their canonical value is unchanged;
cancellation, deletion and canonical replacement discard stale drafts. Target
reconciliation runs on canonical projections even for a hidden panel; Undo must
not resurrect a deleted object's old editor. Measurement and layer creation
names are model state, so they survive switching tabs while unfocused.
Saved-selection editors own their open state and value separately from DOM
nodes. BasePanel restores focus/caret and never blurs a live annotation editor
merely because it repaints. Icon actions and fields have accessible names.

Annotation cleanup checks the current Mol* transform before each sequential
removal. A structure rebuild can already have removed a label and its ghost
parent. Missing references are skipped; errors removing existing references
still propagate. History restoration must recover actual annotation cells.

PNG dimension notifications update the readout in place, preserving a download
button held between pointer-down/up. Export reports rendering, actual download
initiation or a renderer error. The browser guard observes rendering completion
separately from file delivery, preserving the requested PNG dimensions,
transparency and rendering quality. The passing exact-source core run and the
historical timeout are recorded in [the Studio review](studio_review_20261009.md)
and its receipt; this source validation does not qualify a future packaged
candidate.

`studio-list-workflows.e2e.ts` is registered in the normal core lane. It uses
pentalanine, real Python replies and Mol*/Chromium for creation failure/recovery,
filter/mark independence, atomic visibility/undo, drafts and deletion semantics.
The bounded selector profile in `tests/test_reporting_protocol.py` verifies
registration/build routing; it does not prove scientific correctness itself.

## Creation completion and scientific deletion (final review)

`CreationFeedback` owns correlated creation state for Measures, Annotations and
Layers. Submitting keeps the draft and staged participants, disables creation
controls while pending, and clears the draft only on the matching successful
`studio_action_result`. Failure keeps the draft and shows an inline error;
unrelated or stale results cannot complete the request. The dispatcher assigns
the owning domain rather than trusting a caller-supplied creation domain.

`create_layer` carries initial members in the same request. Every tag and member
is resolved before mutation. Existing owner operations run inside one scene
history boundary, so failure rolls back and one Undo restores the whole creation.
The consumer must not send independent membership requests after creation.

Regions owns the new-region name as model state, including while unfocused or
hidden during canonical projections. A successful creation reply or Escape clears it.
Annotation coordinate anchors require three finite numeric fields in nm. Empty
fields stay invalid across repaints; explicit zero remains valid. Python validates
the same numeric boundary before mutating the scene; the existing nm-to-Å
conversion is independent of the session standard unit.

Regions, active-selection saving, saved-selection conversion/rename and Add-ons
registration also retain their drafts until a matching reply. Add-on import errors
still enter discovery diagnostics and now return a failed correlated result.
Cross-domain saved-selection editors consume only their own request identities.

Studio replacement sends one creation/rename request with an explicit overwrite
intent. Existing owner operations run within one history boundary; failure restores
the old complete scene and its Redo, and one Undo/Redo recovers both versions.
Public saved-selection mutations own scene history. Same-system state restoration
preserves selection levels, descriptors and recipes instead of defaulting to groups.

Canvas/panel snapshots carry loaded-system and active-selection metadata for
Annotations, Measures and clipping sections, together with measurement settings.
An exported page keeps readable scene projections but has no Python authority:
unavailable form actions report that requirement, retain drafts and leave pending
state immediately. Its Interactions backend is unavailable for calculation or
inspection; local camera reset and PNG downloads remain usable.

Deleting a stored scientific analysis is separate from deleting a visual set.
Studio first asks for explicit confirmation naming the analysis and stating that
the operation cannot be undone and clears all scene Undo/Redo history. Cancel
sends no request. Filtering does not change the captured target; analyses with
visual references cannot be deleted. Completion/errors use a correlated result,
and pending deletion cannot be submitted again. This does not change the public
Python deletion contract or the experimental scientific classification.
