# Saving a whole session

`save_session` writes the scene **and the system it was built on** to a single file, and
`load_session` reopens it — with nothing loaded first.

```python
import molsysviewer as msv

view = msv.demo["1TCD"]
view.regions.add(selection='molecule_type=="protein"', tag="prot", representation="cartoon")

view.save_session("work.msv")
```

Later, elsewhere, in a fresh kernel:

```python
import molsysviewer as msv

view = msv.load_session("work.msv")
view.regions.tags()
```

That is the whole difference from {doc}`state`. A state document is applied *onto* a
structure you must already have loaded and must know to load; a session brings its own.

## When to use which

|  | {doc}`state` (`.json`) | session (`.msv`) |
| --- | --- | --- |
| carries the molecular system | no | **yes** |
| reopens on its own | no | **yes** |
| applies to a *different* structure | yes, that is the point | no, it brings its own |
| size | small — your work, not the data | as large as the trajectory inside it |

Reach for a state document to move a scene *between* structures, or to keep something
small enough to commit next to a notebook. Reach for a session to put the work down and
pick it up later, or to hand the whole thing to somebody else.

## What is in the file

A `.msv` is a zip with three members:

```
manifest.json      what this file is, and what is inside it
state.json         the same document `export_state()` produces, unchanged
structure.h5msm    the molecular system, in MolSysMT's own format
```

It is an ordinary zip, so you can look inside one with any tool you already have.

The structure is written as `.h5msm` rather than `.pdb` on purpose: PDB collapses chains
and misassigns waters, and holds one structure where a trajectory has thousands. `.h5msm`
is MolSysMT's own format, and it preserves the structure's topological fingerprint — which
is what lets a reloaded session recognise its own system as the one its own state was
written for.

## No size budget

A session is as large as what it contains. A long trajectory makes a large file, and
nothing truncates it for you. If that matters, save a state document instead and keep the
trajectory where it already lives.

## Experimental

The format carries `version: 1` and is declared **experimental**: it may change before it
is declared stable, and a future MolSysViewer may refuse an old session rather than migrate
it. `save_state` is the stable one. Do not use a session as an archival format yet.
