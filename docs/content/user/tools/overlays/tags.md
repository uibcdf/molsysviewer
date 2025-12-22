# Tags & scene management

Tags help you group shapes and clear them selectively.

Add shapes with tags

```python
v.shapes.add_pocket_blob(..., tag="pocket-1")
v.shapes.add_channel_tube(..., tag="channel-A")
v.shapes.add_pharmacophore_features(..., tag="ph4-A")
```

Clear by tag

```python
# Remove only shapes tagged "pocket-1"
v.shapes.clear(tag="pocket-1")

# Remove all shapes
v.shapes.clear()
```

Tips
- Reuse tags for related overlays (e.g., all pocket surfaces/blobs for a system).
- Combine with recipe notebooks: export a static view after adding shapes, then clear to prepare the next view.
