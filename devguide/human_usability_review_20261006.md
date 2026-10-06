# Human usability review — 2026-10-06

**In progress.** Diego is reviewing `sandbox/revision_pre_1_0.ipynb` through
Jupyter running on the remote development machine, accessed through an SSH
tunnel from his own browser. Observations below are his direct reports in this
session, distinct from automated source/browser qualification.

The product source baseline is Viewer
`c046fca173f501c6e259761ef8f3d6b1825f17e8`; the documentation successor
`e71eaf63a289bd9d3a8809c6cfd43e5e147f535a` does not change the product.
The notebook requests `molsyssuite@uibcdf_3.14`. Its separate preparation
check executed all 16 Python cells, confirmed identical batch/progressive
coordinates and restored the named 65-occurrence analysis from a session.
That check does not supply the human observations below. Client operating
system/browser details and screenshots have not been supplied.

## 1. Initial protein and canvas controls — observed passing

Diego reports the following after loading the bundled 1VII protein:

| Operation | Human observation |
| --- | --- |
| Initial protein | Displays correctly. |
| Rotation | Protein rotates correctly. |
| Mouse wheel | Zoom in/out works. |
| Right-button drag | Translates the protein correctly. |
| Right-button click | Opens the context menu. |
| Reset View | Resets the view correctly. |
| `h` and `H` | Open the Help card. |
| Question-mark button | Opens the Help card. |
| Full screen | Entering and returning both work. |
| Studio/Addons toggle | Opens the panel correctly. |
| Floating Studio/Addons | The panel floats. |
| Panel minimize/maximize | Both work. |
| Panel opacity toggle | Works. |
| Lock background | Works. |
| Dock panel split | Works. |
| Studio/Addons popup | Opens correctly. |
| Close Studio/Addons popup | The corresponding close button works. |
| Canvas popup | Opens and its protein stays synchronized with the original canvas for rotation, zoom and translation. |

No defect is reported in this step. The synchronization direction was not
specified; this report does not independently establish every bidirectional
popup route. Correct initial display is observed, while detailed text
legibility and source-region semantics remain for subsequent steps.

## 2. Progressive caffeine load — observed with two defects

Diego reports that caffeine appears alongside the protein, the final framing
is appropriate and Whole shows the combined system. Before the new system is
drawn, Welcome briefly reappears; this is tracked as
[#164](archive/welcome_card_flashes_during_system_rebuild.md).

Regions contains the two sources but displays `Cafe_na` and `Prote_na`,
instead of the supplied accented labels. The existing ASCII slug rule is
reproduced directly; this is tracked as
[#165](archive/automatic_source_regions_corrupt_unicode_labels.md).

The cell emits the provider's box mismatch warning (incoming caffeine has no
box; the protein's box is retained) and structural-attribute warning
(`b_factor`, `occupancy` discarded during concatenation). Diego explicitly
reports that both warnings are understandable. This observation does not
change the scientific box/attribute policy or declare the combined system
chemically prepared.

## 3. Region visibility and representation — observations and accepted revision

Diego reports that Studio Regions/Saved Regions Hide removes unrepresented
caffeine while the protein remains, and Show restores caffeine. He reports
that the section 2 Python API works throughout: hide/show, isolation,
restoration and the orange own representation.

After creating the orange own representation, Studio Hide removes that style
but caffeine remains drawn through Whole. This matched the §A.3 fallback
contract at the time of observation. Diego subsequently approved the #167
revision: enabled Hide hides own representations and masks its atoms on Whole
in every representation state. Separate `enable()` / `disable()` suspends and
reapplies visual configuration, preserving identity, style and hidden request.
Studio offers Enabled independently. Other region representations remain
independent. The implementation has passing regression coverage.
After publication in `845d34b6ae6a9ce07d84145b1ca44278174afa4e`, Diego reports
that the implemented behavior works correctly. This confirms the requested
Hide/Enabled retest; he does not enumerate additional lifecycle routes.
The additional independent Whole hide/show check has not been explicitly
reported.

Diego also asks whether Saved Regions should offer Show Only and how users
should return from it. The discussion considered a plain action using scene Undo versus a
temporary isolation with an explicit visibility restore. A restore must
preserve earlier hidden regions and Whole visibility; showing everything is
not equivalent. Current `show_only()` changes region hidden flags and does
not itself retain a dedicated visibility restoration snapshot.

The Hide/enablement revision is accepted and tracked in
[#167](archive/region_enablement_and_visibility.md).
**Decision — 2026-10-06:** keep the existing Python `show_only()` and Saved
Regions controls unchanged. Do not add a Show Only button or introduce temporary
isolation and a return control in this review. Continue to the notebook's
section 3, batch loading of the same protein and caffeine.

## 4. Same sources loaded together — observed passing

The notebook step creates a separate `batch` view with
`load([protein, caffeine], multiple=True, structure_indices=[0],
labels=["Proteína", "Cafeína"])`. Diego reports that both protein and caffeine
appear with appropriate framing, the regions are properly defined, and Whole
contains both. Hide of caffeine removes it while preserving the protein; Show
restores it. He confirms the following cell executes correctly: its exact
coordinate-array equality assertion passes against the progressive view, and
it reports the batch source records. The reference source counts are 596 and
24 atoms; the user does not separately transcribe the output table.
The manually added orange representation in the progressive view is not
expected in the fresh batch scene.

## 5. Interactions and trajectory — calculation/display observed; remaining controls under review

Notebook section 4 loads real pentalanine structures in source order [0, 8, 3],
mapped to local frames 0, 1 and 2. Diego reports correct molecular representation
and successful navigation across all three frames with the canvas controls.
The calculation appears to complete, but he believes no H bonds are displayed
on the first structure. Saved sets shows Evaluated there and Not evaluated on
the other two. He expected the calculation to cover all three; the submitted
calculation scope and stored scientific parameters have not yet been confirmed.

Read-only local reproduction of the semantic Studio action on the same source
structures, with Buch, 4 Å, all atoms, no PBC and unrestricted display, gives
20 occurrences and coverage [0] for `current`; `all` gives coverage [0, 1, 2]
and per-frame occurrences [20, 25, 20]. The current-frame request produces the
same evaluated/unevaluated status pattern Diego reports. This is a diagnostic
comparison, not a reproduction of his browser input or a confirmed root cause.
The frontend defaults Calculate structures to `current` and Display structures
to `all`; they are independent fields. Diego subsequently confirms that he
left the initial value, believing it was `all`. The current-frame default
explains the reported coverage; there is no evidence here that an explicit
`all` request was lost. This confusion is a human usability observation about
the separate calculation/display scopes, not a diagnosed transport defect.
Diego supplies `analyses()` for `revision-studio`: Buch, 62 atoms, three
structures, one evaluated structure, zero occurrences/relations and no PBC.
The stored hydrogen–acceptor cutoff is 0.23 nm (2.3 Å), rather than the planned
0.4 nm (4 Å). The empty canvas lines therefore correspond to an empty analysis,
not evidence that existing occurrences failed to render. The optional Studio
distance field is initially blank with Method default and nm units, so the
effective cutoff comes from the provider when left blank. The next comparison
was to create a separately named analysis with Calculate structures explicitly
set to `all`, Buch, 0.4 nm and no PBC. The subsequent human result is below.

Diego then reports that the former name field is now a dropdown showing
`revision-studio 0 observations` and cannot find how to enter a new calculation
name. After successful creation, InteractionsPanel switches its source to
Stored analysis; this dropdown selects a saved analysis. The Calculate tab at
the top of New interaction set restores the Store analysis as text field.
Guide him through that switch before the explicit all-frame comparison. The
automatic mode transition is not evident to him; this is a second direct
usability observation in the calculation workflow.

**Subsequent human confirmation:** Diego reports that H bonds are now represented
and are specific to each structure. This establishes visible, structure-dependent
interaction geometry in his review. He does not separately report exact counts,
all-frame evaluated metadata or the new analysis name.

Diego subsequently confirms saved-set Hide/Show works. Inspect presents the
current frame's interactions with participants and distances in nm; Select
participants and Focus participants both work. Inspect also works after changing
the frame. Diego also confirms the proposed structure-filter checks all work
as expected: restrict display to local structure 0, see Excluded by display
filter on 1/2, restore all and preserve evaluated-structure/total-observation
counts in Stored analyses. No new defect is reported in those checks. Next
is the notebook's Python reference calculation and atom-incident filter, then
session recovery. Hide the Studio-generated set before drawing the Python
reference so the two representations can be compared separately.

**Accepted naming decision:** during the Python atom-filter step, Diego finds
incident unfamiliar and approves `involving_selection`, `within_selection`,
`across_selection_boundary` and `between_selections`. This public
query/display vocabulary change is tracked in
[#168](archive/explicit_interaction_selection_mode_names.md), requiring
MolSysMT coordination and a saved-filter compatibility decision. Both are now
implemented against provider `a0ceca86ec99c89377e78fac15cbdf32145a362e`:
new calls use the canonical names; version-1 saved visual filters migrate to
extension 2, leaving scientific metadata/H5MSM untouched. Automated qualification
is in [the receipt](interactions_query_modes_20261006.json). Direct human retest
of the renamed controls is pending. The open scratch notebook is preserved;
after kernel restart, change its explicit `mode="incident"` to
`mode="involving_selection"` before repeating the atom-filter check.

## Next observations

The source corrections for #164/#165 and their regression guards pass,
including all 39 core browser suites. The once-run Python suite has 2,816
passed, 22 sandbox permission failures and 23 skipped; the explicit 22 nodes
pass with normal pytest outside the sandbox. This selected follow-up is not
a second complete run. The unit JS fixture failure was separately tracked as
[#166](archive/group_panel_unit_dom_missing_query_selector.md) and is now fixed.
[The validation receipt](load_usability_fixes_20261006.json) preserves the scope.

The later enablement revision passes 322 JS unit tests, 12 focused Python tests
and a 264-test selected follow-up. All 39 core browser suites pass across the
initial 26 suites and a 13-suite follow-up after updating a stale tooltip
assertion. Its once-run full Python suite had eight diagnosed failures, with
passing selected follow-ups; it was not repeated. See
[the enablement receipt](region_enablement_20261006.json). This automated result
is separate from Diego's subsequent confirmation of the changed Hide behavior.

**Human confirmation — 2026-10-06:** after publication of the corrections in
`66a924404feadaef7aa7147fea573533c21d40c8`, Diego reports that both errors
are corrected: Welcome no longer flashes and the source-region labels are
correct. This closes the pending human retest for #164/#165. Kernel/browser
restart details and client version were not separately reported. Region
observations and the later Hide/Enabled confirmation are recorded above. The
Show Only controls remain unchanged by the subsequent maintainer decision.

For this stage, use Studio's Hide/Show buttons first, then the notebook's
Python cells for `show_only()` and restoration. The notebook prose suggests
isolating through Studio, but the current Regions cards do not expose a
dedicated isolation button; the Python cell is the available step. The open
scratch notebook is preserved.

Before adding an own representation, hiding caffeine masks its atoms on Whole.
Under #167, adding orange ball-and-stick keeps Hide's Whole constraint:
caffeine disappears through both its own representation and Whole. Disabling
the hidden region releases its constraint and permits Whole to draw it again;
re-enabling restores the hidden request. Diego reports the implemented behavior
works correctly, without separately itemizing these steps. Other overlapping representations
and Whole's global visibility remain independent.
An additional independent-visibility check is to hide Whole with caffeine's
own representation visible, then show Whole again. Resetting the region's
representation returns it to the base visibility behavior. These are expected
results for an additional human observation, not newly observed passes.

Continue in the same notebook:

1. Review Studio Interactions calculation, inspection/display filters and trajectory controls (notebook section 4).
2. Save/reopen a recognizable session and compare the restored scene.

Record actual observations as they arrive. This review remains open until those
steps have been discussed; the current result does not close installed-package,
hosted-public, standalone Qt or final 1.0 qualification. Scientific background
and previous automated limits remain in
[the scientific follow-up](scientific_usability_review_20261004.md) and
[the fixed source handoff](source_pair_handoff_20261006.json).
