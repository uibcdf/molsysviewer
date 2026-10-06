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

## Next observations

The source corrections for #164/#165 and their regression guards pass,
including all 39 core browser suites. The once-run Python suite has 2,816
passed, 22 sandbox permission failures and 23 skipped; the explicit 22 nodes
pass with normal pytest outside the sandbox. This selected follow-up is not
a second complete run. The unit JS fixture failure is separately tracked as
[#166](pending_bugs/group_panel_unit_dom_missing_query_selector.md).
[The validation receipt](load_usability_fixes_20261006.json) preserves the scope.

**Human confirmation — 2026-10-06:** after publication of the corrections in
`66a924404feadaef7aa7147fea573533c21d40c8`, Diego reports that both errors
are corrected: Welcome no longer flashes and the source-region labels are
correct. This closes the pending human retest for #164/#165. Kernel/browser
restart details and client version were not separately reported. Visibility
and representation of regions are the next stage; their human result is
still pending.

For this stage, use Studio's Hide/Show buttons first, then the notebook's
Python cells for `show_only()` and restoration. The notebook prose suggests
isolating through Studio, but the current Regions cards do not expose a
dedicated isolation button; the Python cell is the available step. The open
scratch notebook is preserved.

Before adding an own representation, hiding caffeine masks its atoms on Whole.
After adding orange ball-and-stick, hiding the own representation can reveal
Whole underneath; that is the fallback contract, not an atom-wide hide.
An additional independent-visibility check is to hide Whole with caffeine's
own representation visible, then show Whole again. Resetting the region's
representation returns it to the base visibility behavior. These are expected
results for the pending human observation, not newly observed passes.

Continue in the same notebook:

1. Hide/show/isolate source regions, restore them and add a dedicated representation.
2. Compare batch loading with progressive loading.
3. Review Studio Interactions calculation, inspection/display filters and trajectory controls.
4. Save/reopen a recognizable session and compare the restored scene.

Record actual observations as they arrive. This review remains open until those
steps have been discussed; the current result does not close installed-package,
hosted-public, standalone Qt or final 1.0 qualification. Scientific background
and previous automated limits remain in
[the scientific follow-up](scientific_usability_review_20261004.md) and
[the fixed source handoff](source_pair_handoff_20261006.json).
