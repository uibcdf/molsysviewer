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
