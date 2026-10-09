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
