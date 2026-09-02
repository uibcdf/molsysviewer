# Saving and restoring a scene

`save_state` writes what you built — regions, overlays, measurements, colours,
representations — to a JSON file, and `load_state` puts it back on a viewer.

**It does not carry the molecular system.** Load the structure first, then the state. That
is what keeps the file small and shareable: the same scene can be applied to any compatible
structure, and the file describes your work rather than duplicating the data.

If you would rather have one file that reopens on its own, system included, that is a
{doc}`session`.

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
| annotations, measurements, shapes | undo/redo history |
| stored selections and the active selection | global visual settings (background, lighting, fog) |
| layers and clipping sections | |
| the whole's representation and colour | |
| **the vantage point**: camera, current structure index, playback settings | |

The vantage point travels under a `view` key. A scene restored to the right atoms but a
different camera and a different frame is not the scene that was saved, so `save_state`
asks the frontend for a **fresh** camera before writing. `export_state()` cannot do that —
it has no round trip to wait for — so it records the last camera the frontend pushed. On a
viewer that has never rendered there is no camera at all, and the key is simply absent.

A region is stored as **the rule that produced it** *and* as the atoms that rule resolved
to. Onto the same structure the atoms are used. Onto a different one the rule is
re-resolved, because replaying the indices would address different atoms — which is what
used to happen. Anything without a rule is re-resolved by atom identity instead, and what
cannot be resolved either way arrives marked broken, with a warning naming the mismatch.

The remaining exclusions are deliberate; the boundary is set out in
`devguide/archive/what_save_state_promises.md`.

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

**It is not a session.** It carries no molecular system, so reopening it means knowing
which structure it was built on and loading that first. When you want the file to reopen
on its own, use {doc}`session` instead.

**It is not a picture.** Global visual settings — background, lighting, fog — are outside
it, and it makes no claim to reproducing a screenshot. If you want the image, {doc}`html_export`
carries the scene and its rendering together.
