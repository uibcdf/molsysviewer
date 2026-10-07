# Visualizing interactions

Use Interactions to show chemically interpreted relationships while retaining
their method, measurements and evaluated structures. A named scientific analysis
is stored in your view's molecular system. A tagged visual set selects what to
draw from that analysis. You can create several sets from the same data.

:::{admonition} Experimental availability
This feature currently requires MolSysMT's experimental public Interactions and
H5MSM APIs. The compatible published dependency version remains to be qualified.
Ordinary molecular viewing works without those experimental APIs; the Interactions
form explains when its scientific backend is unavailable.
:::

## Choosing a source

The floating Studio card has an **Interactions** tab with three routes:

- **Calculate:** calculate Buch hydrogen bonds or geometric disulfide candidates,
  save the result under a name, then create a visual set.
- **Stored analysis:** create a visual set from an analysis already in the system.
- **H5MSM file:** load one named analysis, then create its visual set. The path
  addresses the Python session's filesystem.

Calculation uses the visible structure by default. Request all structures or an
explicit list when you need broader coverage. Playback only queries saved results;
it does not calculate new interactions. A structure evaluated without results and
a structure that was never evaluated have different statuses.

Buch uses a hydrogen–acceptor distance criterion, with a default threshold of
2.3 Å. This is a particular criterion, not a general certification of hydrogen
bonds. Disulfide candidates are geometric sulfur–sulfur contacts; calculating them
does not add covalent bonds to the topology. Periodic calculations require valid
box vectors and preserve the images chosen by the detector.

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
graphic representation is unsupported. Initial graphics support hydrogen–acceptor
links and sulfur–sulfur candidate links.

## Understanding limits

Live projection is bounded to 50,000 selected observations and 8 MiB of geometry
per set and frame. Inspection pages contain at most 200 observations (50 in
Studio), with a 512 KiB reply budget and bounds on compound participant details.
Until the provider supports bounded occurrence pages, materialization is also
checked before copying the selected frame. An oversized request reports a limit
with its count; narrow the filter to inspect it. These budgets do not bound the
memory occupied by the loaded trajectory or complete scientific analysis.

Static HTML embeds frame geometry within a 64 MiB interaction budget and fails
explicitly when that budget is exceeded. Overlapping sets currently repeat that
geometry. The scientific inspector requires a live Python session.

See {doc}`../cookbook/interactions_workbench` for the executable Python workflow.
