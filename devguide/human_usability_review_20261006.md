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
independent. The implementation has passing regression coverage; a human retest remains
pending after publication.
The additional independent Whole hide/show check has not been explicitly
reported.

Diego also asks whether Saved Regions should offer Show Only and how users
should return from it. Discuss a plain action using scene Undo versus a
temporary isolation with an explicit visibility restore. A restore must
preserve earlier hidden regions and Whole visibility; showing everything is
not equivalent. Current `show_only()` changes region hidden flags and does
not itself retain a dedicated visibility restoration snapshot.

The Hide/enablement revision is accepted and tracked in
[#167](archive/region_enablement_and_visibility.md). The temporary
isolation API and return control remain open for discussion after this change.

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
does not replace Diego's pending retest of the changed Hide behavior.

**Human confirmation — 2026-10-06:** after publication of the corrections in
`66a924404feadaef7aa7147fea573533c21d40c8`, Diego reports that both errors
are corrected: Welcome no longer flashes and the source-region labels are
correct. This closes the pending human retest for #164/#165. Kernel/browser
restart details and client version were not separately reported. Region
observations are recorded above; Hide/enablement is now accepted and isolation's
return control remains open.

For this stage, use Studio's Hide/Show buttons first, then the notebook's
Python cells for `show_only()` and restoration. The notebook prose suggests
isolating through Studio, but the current Regions cards do not expose a
dedicated isolation button; the Python cell is the available step. The open
scratch notebook is preserved.

Before adding an own representation, hiding caffeine masks its atoms on Whole.
Under #167, adding orange ball-and-stick keeps Hide's Whole constraint:
caffeine disappears through both its own representation and Whole. Disabling
the hidden region releases its constraint and permits Whole to draw it again;
re-enabling restores the hidden request. This is the new expected retest result,
not a human observation already reported. Other overlapping representations
and Whole's global visibility remain independent.
An additional independent-visibility check is to hide Whole with caffeine's
own representation visible, then show Whole again. Resetting the region's
representation returns it to the base visibility behavior. These are expected
results for the pending human observation, not newly observed passes.

Continue in the same notebook:

1. Retest #167's Hide/enablement revision, then discuss the isolation return control.
2. Compare batch loading with progressive loading.
3. Review Studio Interactions calculation, inspection/display filters and trajectory controls.
4. Save/reopen a recognizable session and compare the restored scene.

Record actual observations as they arrive. This review remains open until those
steps have been discussed; the current result does not close installed-package,
hosted-public, standalone Qt or final 1.0 qualification. Scientific background
and previous automated limits remain in
[the scientific follow-up](scientific_usability_review_20261004.md) and
[the fixed source handoff](source_pair_handoff_20261006.json).
