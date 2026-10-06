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
[#164](pending_bugs/welcome_card_flashes_during_system_rebuild.md).

Regions contains the two sources but displays `Cafe_na` and `Prote_na`,
instead of the supplied accented labels. The existing ASCII slug rule is
reproduced directly; this is tracked as
[#165](pending_bugs/automatic_source_regions_corrupt_unicode_labels.md).

The cell emits the provider's box mismatch warning (incoming caffeine has no
box; the protein's box is retained) and structural-attribute warning
(`b_factor`, `occupancy` discarded during concatenation). Diego explicitly
reports that both warnings are understandable. This observation does not
change the scientific box/attribute policy or declare the combined system
chemically prepared.

## Next observations

Continue in the same notebook and existing protein view:

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
