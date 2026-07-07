(User_Troubleshooting_Performance)=
# Performance

## Slow rendering

**Choose a lighter representation.** The default `ball-and-stick` representation
is expensive for large systems. For exploratory work, use:

```python
view.set_global_representation("backbone")   # protein backbone only
view.set_global_representation("cartoon")    # ribbon/helix/sheet
```

**Load a lighter system.** Waters and ions are usually the largest atom count.
For one-off rendering performance, trim the molecular system with MolSysMT and
reload the viewer:

```python
import molsysmt as msm

trimmed = msm.remove(view.molsys, selection="resname HOH", to_form="molsysmt.MolSys")
trimmed = msm.remove(trimmed, selection="ion", to_form="molsysmt.MolSys")
view.load(trimmed, mode="replace")
```

**Lower surface resolution.** When using pocket or channel overlays:

```python
view.shapes.add_pocket_surface(
    ...,
    resolution=2.0,   # coarser mesh (default is ~1.0)
)
```

## Large trajectories

**Use a shorter frame range.** Pass a frame slice to the player:

```python
view.player.set_frame_range(0, 100)   # show only first 100 frames
```

**Reduce export fps.** For movie export, lower fps reduces render time:

```python
view.movie.export("out.mp4", fps=12)
```

## Overlay complexity

Each shape call adds geometry to the scene. If you have many overlays:

```python
view.shapes.clear()   # remove all shapes before adding new ones
```

Use `layer_tag` to group shapes and hide/show groups instead of
recreating them:

```python
view.shapes.add_links(..., layer_tag="hbonds")
view.hide_layer("hbonds")   # fast — no geometry rebuild
view.show_layer("hbonds")
```

## HTML export file size

`mode="standalone"` embeds the full runtime (~3 MB). Use `mode="lite"` for
smaller files that load the runtime from a CDN:

```python
view.export.html("figure.html", mode="lite")
```
