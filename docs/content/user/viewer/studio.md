(User_Viewer_Studio)=
# Studio and add-ons

Use Studio to organize your molecular scene and inspect the objects you have
created. Open it with the canvas panel button or **Open Studio…** in the
{doc}`context_menu`.

## Choosing a section

The sidebar contains the native tools. In a narrow card, a **Studio section**
selector replaces the sidebar so the editor retains room for its controls.
Switching sections keeps the current scene and selection.

| Section | Use it to |
| --- | --- |
| System | Inspect molecular organization and select atoms, groups or chains. |
| Whole | Change the base representation of the complete system. |
| Selection | Inspect, save and reuse atom selections. |
| Regions | Create atom subsets and manage their representations and visibility. |
| Measures | Create and inspect distances, angles and dihedrals. |
| Annotations | Add text anchored to atoms or coordinates. |
| Interactions | Calculate, load, display and inspect experimental interaction analyses. |
| Shapes | Create and manage geometric objects. |
| Layers | Group scene objects and control their visibility together. |
| Viewport | Adjust camera, background, lighting and clipping sections. |
| Export | Download PNG images and HTML views. |
| Settings | Configure automatic hiding and the reveal area of canvas controls. |

Regions distinguish **Hide/Show** from **Enable/Disable**. A hidden enabled region
retains ownership of its atoms in Whole. Disabling it releases that ownership,
so those atoms can appear in Whole again. Independent representations keep their
own visibility; see {doc}`../scene_management/regions`.

## Organizing saved objects

Search each saved list by name and its displayed metadata. Searching only
filters the list; it does not hide atoms or change the molecular selection.
Open **Manage marked items** to mark individual rows or all matches. Marks
are independent of atom selections and remain when you change the search.
**Show marked**, **Hide marked** and **Delete marked** act on all marked rows,
including those hidden by the search. Deletion lists the target names and asks
for confirmation. Use **Undo** to restore the whole batch with one action.
Deleting interaction sets keeps their stored scientific analyses; ungrouping
layers keeps their members.

To remove stored scientific data, use **Delete analysis** under Interactions.
Studio asks you to confirm the named analysis: this deletion cannot be undone
and clears all scene Undo/Redo history. Remove its visual sets first if it is
still referenced. **Cancel** keeps the analysis and history.

When creating a measurement, annotation or layer, Studio keeps the form until
Python confirms success. If creation fails, the error appears beside the form
and you can correct the retained draft. A new layer and its initial members
are created together and can be undone in one step. Coordinate annotations
require a number for each coordinate in nm; enter `0` explicitly when needed.

Creation sections are collapsed when saved objects already exist. Open the
**New …** heading to create another object. Studio keeps the disclosure state,
creation values and secondary text drafts while you change sections or navigate
structures. Cancelling an editor or deleting its target discards that draft.
Optional annotation offsets and leader lines are in **Advanced options**.

## Creating shapes

Stage the required selections before creating a shape. An anchored sphere
follows its atoms through the trajectory. Links and displacement arrows use
the geometric centers of the staged selections in the visible structure;
the resulting geometry is fixed and does not follow later structures.
Coordinates and radii in the form use nm; arrow radius scale is dimensionless.
Studio preserves the shape name and anchors if Python rejects creation and
shows the reason in the form.

Advanced shape entries provide Python examples for supplied geometry with
explicit units. Ring geometry draws centers, normals and radii you supply;
it does not detect aromaticity. Use Interactions for computed contacts.

## Calculating and displaying interactions

Saved sets remain visible while **New interaction set** is collapsed. Open it
to calculate an analysis, use a stored analysis or load one from an H5MSM file.
The file path is resolved in the Python session.

Choose **Calculate atoms** and **Calculate structures** before submitting.
`current` evaluates the visible structure, `all` evaluates all loaded structures,
and a list such as `0,2,5` evaluates only those indices. Choosing staged A or A/B
opens the selection controls. Display filters limit what is drawn; they do not
extend the calculation. Inspect reports the visible structure's observations
and distances with their units. Scientific metadata is available in a separate
disclosure. See {doc}`../overlays/interactions` for the experimental contract.

MolSysMT supplies these native scientific operations. You do not register it
as an addon. Optional domain extensions retain their own **Add-ons** workspaces;
the Add-ons manager enables them and registers modules supplied by their toolkit.

## Moving the card and using the keyboard

Drag the header to move a floating card and resize its lower corner. Background
lock, minimize/restore and dock/float retain its floating bounds, with clamping
when the canvas becomes smaller. In a narrow Add-ons card, an **Addon workspace**
selector replaces its sidebar too.

Use Tab to move through native controls. Buttons support Enter and Space;
checkboxes support Space, and disclosure headings support Enter or Space.
Focused controls have a visible outline.

## Downloading a view

Export shows PNG dimensions from the actual canvas drawing buffer and selected
scale. Choose the light or dark preset and whether the background is transparent.
**Download PNG Image** saves the image in your browser.

**Download HTML View** downloads a self-contained browser view from the live
Python session. It does not create a file on the Python host. Camera navigation
works in the exported view; scene editing requires a live Python session. This
HTML view is distinct from the experimental standalone Qt host. Use the Python
export API when you want to save to a path in the Python environment.
