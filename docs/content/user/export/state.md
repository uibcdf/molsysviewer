# Saving and restoring a scene

`save_state` writes what you built — regions, overlays, measurements, colours,
representations — to a JSON file, and `load_state` puts it back on a viewer.

**It does not carry the molecular system.** Load the structure first, then the state. That
is what keeps the file small and shareable: the same scene can be applied to any compatible
structure, and the file describes your work rather than duplicating the data.

## Saving

```python
import molsysviewer as msv

view = msv.demo["1TCD"]
view.regions.add(selection='molecule_type=="protein"', tag="prot", representation="cartoon")
view.measurements.add_distance(
    selection_a="atom_index==[0]",
    selection_b="atom_index==[10]",
    tag="d1",
)

view.save_state("scene.json")
```

The write is atomic: the file appears complete or not at all, so an interrupted save
cannot leave you with half a scene.

## Restoring

```python
other = msv.demo["1TCD"]     # the structure comes first
other.load_state("scene.json")

other.regions.tags()
other.measurements.tags()
```

## What is in the file

| In | Not in |
| --- | --- |
| regions, with the selection that produced each one | the molecular system |
| annotations, measurements, shapes | the camera |
| stored selections and the active selection | undo/redo history |
| layers and clipping sections | global visual settings (background, lighting, fog) |
| the whole's representation and colour | the current structure index |

A region is stored as **the rule that produced it**, not as a list of atom indices. That
is why a state file applies to a compatible structure rather than only to the exact one it
was written from.

Those exclusions are deliberate, and the boundary is being made explicit before 1.0 —
see `devguide/pending_proposals/what_save_state_promises.md`. The camera is the one that
is not simply unimplemented: it is the frontend's state, mirrored back to Python, and is
absent on a viewer that has never rendered.

## Restoring onto a scene that is not empty

By default a load replaces what is there. To add instead:

```python
third = msv.demo["1TCD"]
third.regions.add(selection='molecule_type=="water"', tag="solvent", representation="line")

third.load_state("scene.json", clear_first=False)
third.regions.tags()
```

Both regions are now in the scene: the one that was there and the one that arrived.

Tags can collide, and `on_conflict` decides what happens then.

Loading the same file again collides on `prot`. With `"skip"` the scene keeps what it
already has:

```python
third.load_state("scene.json", clear_first=False, on_conflict="skip")
third.regions.tags()
```

The default would have refused instead — and refused *before* applying anything, so a
conflict never leaves the scene half-loaded.

`"rename"` is the third option: it keeps both, giving the incoming region a new tag. Reach
for it when the two really are different things that happen to share a name — two copies
of the same region will overlap, and MolSysViewer warns about that for good reason.

## Dictionaries instead of files

`export_state()` and `import_state()` are the same thing without the file, for when you
want to keep the scene in a variable, send it somewhere, or diff two of them:

```python
snapshot = view.export_state()
other.import_state(snapshot)
```

`export_state → import_state → export_state` is stable: the second export equals the
first.

## Versions

The document carries `version: 2`. A build reads its own version and **refuses** an older
one rather than guessing at a migration. If you have archived state files, keep the
MolSysViewer version that wrote them until a migration path is decided.

## What this is not

This is not a session bundle. It does not reproduce a screenshot, and it makes no claim
to: the camera, the current frame and the global visual settings are all outside it. If
you want the picture, {doc}`html_export` carries the scene and its rendering together.
