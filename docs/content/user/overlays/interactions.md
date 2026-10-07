(User_Overlays_Interactions)=
# Visualizing interactions

Use Interactions to show chemically interpreted relationships while retaining
their method, measurements and evaluated structures. A named scientific analysis
is stored in your view's molecular system. A tagged visual set selects what to
draw from that analysis. You can create several sets from the same data.

Use MolSysMT **0.23.0 or later** with MolSysViewer **0.24.0 or later** for
these workflows. The published 0.24.0 / 0.23.0 pair has passed installed-package,
scientific and browser qualification. MolSysMT provides the calculations and
H5MSM storage directly; you do not register a MolSysMT addon.

## Choosing a source

The floating Studio card has an **Interactions** tab with three routes:

- **Calculate:** choose a supported interaction family and its scientific
  parameters, save the result under a name, then create a visual set.
- **Stored analysis:** create a visual set from an analysis already in the system.
- **H5MSM file:** load one named analysis, then create its visual set. The path
  addresses the Python session's filesystem.

Python calculation uses the visible structure by default. In Studio, choose
**Calculate structures** independently of **Display structures**. Request all
structures or an explicit list when you need broader calculation coverage.
Playback only queries saved results;
it does not calculate new interactions. A structure evaluated without results and
a structure that was never evaluated have different statuses.

Buch uses a hydrogen–acceptor distance criterion, with a default threshold of
2.3 Å. This is a particular criterion, not a general certification of hydrogen
bonds. Disulfide candidates are geometric sulfur–sulfur contacts; calculating them
does not add covalent bonds to the topology. Periodic calculations require valid
box vectors and preserve the images chosen by the detector.

## Calculating from Python

Calculate first, then add a visual set. The returned result is retained in
`view.molsys.interactions`; adding or hiding a visual set does not recalculate it.
This example evaluates every structure in a three-structure view:

```python
import molsysviewer as msv

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
result = view.interactions.hbonds.get_buch_hbonds(
    name="hydrogen_bonds", structure_indices="all", pbc=False,
)
hbonds = view.interactions.add("hydrogen_bonds", tag="hbonds")
```

You can inspect any evaluated structure and control the set independently:

```python
observations = view.interactions.inspect("hbonds", structure_index=2)
hbonds.hide()
hbonds.show()
```

Use a distinct analysis name for another calculation. Existing names are not
overwritten. Calculating does not add covalent bonds or alter molecular topology.
Each method has an explicit signature; scientific defaults and profiles follow
the corresponding MolSysMT detector. For example, the generic hydrogen-bond
getter defaults to Baker–Hubbard, whereas `get_buch_hbonds` explicitly selects Buch.

## Supported families and their graphics

The methods below belong to `view.interactions`. Pass `name=...` and the
scientific parameters required by the selected getter. Studio calls the same
family getters. There is no generic public `compute()` operation.

| Family | Python getter | Graphic representation |
| --- | --- | --- |
| Hydrogen bonds | `hbonds.get_hbonds`, `hbonds.get_buch_hbonds`, `hbonds.get_luzard_chandler_hbonds` | Hydrogen–acceptor link; donor, hydrogen and acceptor remain inspectable. |
| Disulfide candidates | `disulfides.get_disulfide_candidates` | Sulfur–sulfur candidate link; no covalent bond is added. |
| Ionic contacts | `ionic.get_ionic_interactions` | Positive–negative participant guide, using centroids for compound participants. |
| Pi–pi | `pi_pi.get_pi_pi_interactions` | Ring-centroid guide. |
| Cation–pi | `cation_pi.get_cation_pi_interactions` | Cation-to-ring-centroid guide. |
| Halogen bonds | `halogen_bonds.get_halogen_bonds` | Halogen–acceptor link; all four scientific participant roles are retained. |
| Hydrophobic contacts | `hydrophobic.get_hydrophobic_interactions` | Contact link between the observed participants. |
| Metal coordination candidates | `metal_coordination.get_metal_coordination` | Metal–ligand candidate link. |
| Water bridges | `water_bridges.get_water_bridges` | Two or three hydrogen–acceptor segments per occurrence for one or two water mediators. |

A centroid guide is a visual aid. Its length does not replace a detector's
recorded measurement, such as the minimum distance between charged groups.
An observation can produce several segments; the displayed occurrence count
and segment count therefore need not match. Compound participants split across
a periodic boundary are reported as unsupported rather than silently unwrapped.

## Declaring file correspondence

An independent analysis must use the same atom and structure order as your loaded
system. You must explicitly declare that correspondence. If the order differs,
provide ordered source atom and structure maps. Dimension and index validation do
not prove that a file belongs to your system; source labels preserve provenance
without authenticating the origin.

H5MSM can contain a full molecular system and named analyses, or only named
analyses. Loading an analysis through Interactions does not replace coordinates.
Saving a MolSysViewer session preserves the system, complete analyses and visual
references together. A visual state file alone needs the corresponding scientific
analyses already loaded.

## Saving named analyses

Use `view.interactions.save` to keep scientific results in an interactions-only
H5MSM file. Choose one analysis name or a nonempty list; omit `analysis_names`
to save every named analysis in the view. The file retains complete analyses
and their atom/structure index domains, rather than the visual set's filter.
It contains neither molecular coordinates nor scene styles.

```python
view.interactions.save("hydrogen_bonds.h5msm", analysis_names="hydrogen_bonds")
reloaded = view.interactions.load(
    "hydrogen_bonds.h5msm", analysis_name="hydrogen_bonds",
    name="hydrogen_bonds_reloaded", assume_aligned=True,
)
```

Here the file was saved from the same unchanged system, so its indices are
aligned. For an independent file, verify correspondence before declaring
`assume_aligned=True`. Loading adds scientific data; call `add` when you also
want a visual set. Existing analysis names are not overwritten.

Saving refuses an existing destination unless you supply `overwrite=True`.
Names are validated before writing, and a completed file replaces the destination
only after serialization succeeds. Saving analyses is distinct from saving a
session, which retains the molecular system and scene together.

## Filtering and inspecting a set

The display filter is independent of the calculation scope. Filtering cannot
create observations for atoms or structures that were not evaluated.

| Mode | Retained interactions |
| --- | --- |
| `involving_selection` | At least one participant atom is in your selection. |
| `within_selection` | All participant atoms are in your selection. |
| `across_selection_boundary` | Participant atoms are both inside and outside your selection. |
| `between_selections` | Participants touch both disjoint selections A and B. Exclusive confines all atoms to their union. |

Atom and structure indices are local to the loaded system. You can supply
nonconsecutive integer lists. The selection dock fills the same selections used
by the Python API.

Each saved card offers Focus, Show/Hide, Edit, Inspect and Delete. Edit changes
the filter, color, opacity or radius in one undoable Apply operation. Layers
control visibility through the existing scene controls. Deleting a set retains
its scientific analysis. Delete an unreferenced analysis explicitly from the
stored-analysis section when you want to remove the data.

Inspect shows the current frame's participants, roles, measurements and units,
evidence, periodic images and occurrence identities. It also states the
calculation scope. Compound participants remain inspectable even when their
graphic representation is unsupported. Inspect the recorded measurement and unit
when interpreting a guide or candidate link.

### Reading another inspection page

`inspect` returns a bounded page of observations for one structure. Its `total`
counts filtered occurrences; `next_offset` identifies the next page. Stop when
it is `None`, and check `limit_reason` before treating inspection as complete.
Use the returned offset instead of assuming that every page has the requested
length. In this demo, switch to local structure 1 to inspect its hydrogen bonds:

```python
view.player.go_to_structure(1)
page = view.interactions.inspect("hbonds", offset=0, limit=1)
if page["next_offset"] is not None:
    page = view.interactions.inspect("hbonds", offset=page["next_offset"], limit=1)
```

Inspection remains available when the selected set is too large to draw. It
does not require copying every occurrence into a Python dictionary. Check the
page's `status` and `limit_reason`: excluded or unevaluated structures and
participant/byte limits are explicit, rather than silently incomplete results.

### Selecting or focusing an observation

Studio's inspector offers **Select participants** and **Focus participants**
for each observation. Python provides the same operations. Inspect the visible
structure first, then use the occurrence identifier and revisions from that
latest page:

```python
page = view.interactions.inspect("hbonds", limit=50)
if page["observations"]:
    occurrence = page["observations"][0]["occurrence_index"]
    identity = dict(
        structure_index=page["frame"],
        analysis_revision=page["analysis_revision"],
        query_revision=page["query_revision"],
    )
    atoms = view.interactions.select_observation("hbonds", occurrence, **identity)
    view.interactions.focus_observation("hbonds", occurrence, **identity)
```

Selection includes every atom in each participant, including compound rings or
groups. Focus uses their canonical molecular coordinates; it does not unwrap
periodic images. After changing the visible structure, filter or analysis,
inspect again. A stale identity or an occurrence absent from the latest page
is rejected before selection or camera changes. Editing the returned dictionary
does not change the internally retained participants.

## Understanding limits

Live projection is bounded to 50,000 selected observations and 8 MiB of geometry
per set and frame. Inspection pages contain at most 200 observations (50 in
Studio), with a 512 KiB reply budget and bounds on compound participant details.
The published provider supports bounded occurrence pages, which the inspector
uses without serializing the whole analysis. A fallback for results without that
page interface checks materialization before copying the selected frame.
An oversized request reports a limit
with its count; narrow the filter to inspect it. These budgets do not bound the
memory occupied by the loaded trajectory or complete scientific analysis.

Static HTML embeds frame geometry within a 64 MiB interaction budget and fails
explicitly when that budget is exceeded. Overlapping sets currently repeat that
geometry. The scientific inspector requires a live Python session.

See {doc}`../cookbook/interactions_workbench` for the executable Python workflow.
