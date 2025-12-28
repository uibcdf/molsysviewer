# Viewer UI

The viewer shows a small on-canvas UI so you can control the scene without writing code for every action.

You use it to:

- reset the camera,
- toggle fullscreen and background mode,
- start/stop simple animations (spin/swing),
- navigate trajectories (when available),
- open a synced popout view (when enabled).

## Control buttons

The on-canvas buttons are:

- `Reset`: reset the camera view.
- `Full`: toggle fullscreen.
- `Bg`: toggle light/dark background.
- `Spin`: toggle continuous spin animation.
- `Swing`: toggle rocking animation.
- `Pop`: open a synced popout window (only when enabled).

## Trajectory bar (structures)

If your molecular system has multiple structures, the viewer exposes a small trajectory bar.
It stays disabled when there is only one structure.

You can:

- Step backward/forward by `step` using the `−` and `+` buttons.
- Play/pause using the play button (`▶` / `⏸`).
- Scrub to a structure index using the slider.
- Read the current position as `current / total` (1-based).
- Set the step size and playback FPS with the numeric fields.

Tip
- In MolSysViewer, “multiple structures” can be a trajectory (time-ordered) or an ensemble/model set.

## Show/hide and placement

You can hide the on-canvas UI entirely:

```python
view.set_controls_visible(False)
```

You can also enable autohide and configure placement:

```python
view.set_controls_visible(
    True,
    autohide=True,
    position=["top", "right"],
    position_fullscreen=["bottom", "right"],
)
```

Defaults come from `molsysviewer.config`:

- `molsysviewer.config.show_controls`
- `molsysviewer.config.autohide_controls`
- `molsysviewer.config.controls_position`
- `molsysviewer.config.controls_position_fullscreen`

## Popout

When the popout button is enabled, the popout viewer stays synced with the host:

- camera changes,
- spin/swing toggles,
- and scene operations (load, shapes, regions, layers).

Notes
- In docs-light exports (`write_html(..., mode="lite")`), popout requires a runtime URL and is controlled by `include_popout`.
