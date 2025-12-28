# Channels (tubes)

Channel tubes are useful to render pathways as centerlines with radii.

See also the cookbook:
- {doc}`../../../cookbook/channel_tube`

```python
centers = [(0,0,0), (2,0.5,0.2), (4,1,0.5), (6,1.5,1.0)]
radii   = [1.2, 1.0, 0.9, 1.1]
view.shapes.add_channel_tube(
    centers=centers,
    radii=radii,
    color_mode="segment",  # or "distance"
    smoothing=0.5,
    tag="channel-demo",
)
```
