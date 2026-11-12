(User_Movie_Timeline)=
# Timeline and keyframes

The playback timeline (version 1) is an ordered list of keyframes. Each keyframe says
*what the scene should look like* at a given time.

## Keyframe fields

Every keyframe has a `time_ms` timestamp (milliseconds).
All other fields are optional — missing fields mean "keep the current value".

| Field | Type | Effect |
|---|---|---|
| `time_ms` | `float` | Timestamp in milliseconds (**required**). |
| `camera` | `dict` | `position` and `target` in Å; `up` is dimensionless. |
| `structure_index` | `int` | Trajectory frame to show. |
| `layer_visibility` | `dict[str, bool]` | Step-change visibility of tagged shapes. |
| `easing` | `str` | Transition curve to the *next* keyframe. |

Easing values: `"linear"` (default), `"ease-in"`, `"ease-out"`, `"ease-in-out"`.

## Adding keyframes manually

```python
import molsysviewer as mv

view = mv.demo["dialanine"]

# Capture the current camera
snap = view.camera.get_snapshot()

# Start at t=0 and end at t=5 000 ms
view.movie.add_keyframe(0, camera=snap)
view.movie.add_keyframe(5000, camera={"position": [15, 0, 0],
                                       "target":   [0, 0, 0],
                                       "up":       [0, 1, 0]})

view.movie.info()
# {'n_keyframes': 2, 'duration_ms': 5000.0, 'has_camera': True, ...}
```

Rules:

- `time_ms` values must be **strictly increasing**.
- At least **two keyframes** are required before `play()` or `export()`.

## Camera orbit builder

`add_camera_orbit` generates a full 360° orbit in one call.

```python
view.movie.clear()
view.movie.add_camera_orbit(duration_ms=6000, n_turns=1, n_keyframes=36)
# 37 keyframes (36 steps + closing frame), t=0→6 000 ms
```

Key parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `duration_ms` | 5000 | Total orbit duration. |
| `n_turns` | 1.0 | Number of full rotations. |
| `n_keyframes` | 36 | Keyframes per turn (higher = smoother). |
| `center` | camera target | Orbit center in Å. |
| `easing` | `"linear"` | Easing for each inter-keyframe segment. |

The geometry is computed from the **current camera snapshot** at call time.
Position, target, and up are taken from `view.camera.get_snapshot()`.

## Trajectory sweep builder

`add_structure_sweep` steps through trajectory frames.

```python
view.movie.clear()
view.movie.add_structure_sweep(
    from_index=0,
    to_index=99,
    duration_ms=10_000,
)
# 100 keyframes, each with structure_index 0..99
```

Key parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `from_index` | 0 | First structure index. |
| `to_index` | `n_structures - 1` | Last structure index (inclusive). |
| `duration_ms` | — | Sweep duration (provide this **or** `end_time_ms`). |
| `end_time_ms` | — | Absolute end time (alternative to `duration_ms`). |
| `start_time_ms` | `duration_ms` of last keyframe | When to start. |

## Visibility transitions

`add_visibility_transition` inserts a step-change in the visibility of a tagged shape.

```python
view.movie.add_keyframe(0)
view.movie.add_keyframe(6000)

view.movie.add_visibility_transition("active-site", visible=True,  at_time_ms=1000)
view.movie.add_visibility_transition("active-site", visible=False, at_time_ms=5000)
```

If a keyframe already exists at `at_time_ms`, the entry is merged into it.
Otherwise a new keyframe is inserted at the correct sorted position.

## Chaining builders

Builders always append *after* the last existing keyframe by default.
You can chain them to produce a compound animation:

```python
view.movie.clear()

# First 6 s: camera orbit
view.movie.add_camera_orbit(duration_ms=6000)

# Next 4 s: trajectory sweep (starts at t=6 000 ms automatically)
view.movie.add_structure_sweep(duration_ms=4000)

view.movie.duration_ms  # 10 000.0
```

## Timeline inspection

```python
info = view.movie.info()
# {
#   'n_keyframes': 137,
#   'duration_ms': 10000.0,
#   'has_camera': True,
#   'has_structure_sweep': True,
#   'has_visibility_transitions': False,
# }

view.movie.duration_ms  # 10000.0
view.movie.keyframes    # list of detached dictionaries
```

## Serialization

The version-1 timeline can be saved to JSON and replayed on a view with the
referenced structures and scene objects.

```python
# Save
view.movie.save("recipes/orbit_360.json")

# Load on a different view
view2.movie.load("recipes/orbit_360.json")
view2.movie.play()
```

You can edit a recipe independently. `keyframes` and `to_dict()` return detached
values, and `from_dict()` copies the values you supply.

`to_dict()` / `from_dict()` work with plain Python dicts:

```python
data = view.movie.to_dict()
# {'molsysmovie_version': 1, 'keyframes': [...]}

view2.movie.from_dict(data)
```

## Clearing the timeline

```python
view.movie.clear()
view.movie.duration_ms  # 0.0
```

## Independent tracks (experimental)

Use `set_baseline()` to start a version-2 recipe with the current scene and an
explicit camera pose. Each track controls a single property on its own schedule.
Evaluate at any time from Python, including before displaying the view.

```python
view.movie.set_baseline(
    2000, camera={"position": [0, 0, 15], "target": [0, 0, 0], "up": [0, 1, 0]}
)
view.movie.add_track({
    "tag": "orbit-segment",
    "target": {"domain": "camera"},
    "property": "pose",
    "keys": [{"time_ms": 1500, "value": {
        "position": [15, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]
    }}],
})
pose = view.movie.evaluate(750)["camera"]
view.movie.save("recipe.json")
view.save_session("work.msv")
```

Time is in milliseconds and camera coordinates are in ångströms. Camera poses
interpolate between keys. A `structure` track with property `index` and a
visibility track with property `visible` take effect at their key times and hold
until the next key. Visibility targets are `whole` or a tagged `region`, `layer`,
`shape`, `annotation`, `measurement` or `interaction`. `update_track()` replaces
a track's keys. `remove_track()` removes its scheduled channel. The baseline
remains in the recipe; `reset_async()` restores its recorded scene. Use
`review_rebase()` and `rebase(review)` to adopt intentional changes after
reviewing their effects on the recipe.

`evaluate()` returns detached values without changing the live scene.
`validate()` checks the recipe against the current system and its referenced
scene objects. A JSON recipe can be loaded onto a matching system and scene.
A session keeps the recipe with its molecular data and scene.

### Reviewing a recipe for a prepared scene

Use `review_import()` when the destination scene has different object names
or identities. Prepare its objects first. A map explicitly relates the source
and destination domain/tag; it does not create scene objects or modify the
molecular system. For example, rename the region controlled by a recipe:

```python
import molsysviewer as msv

with msv.demo["pentalanine"] as view:
    view.regions.add(tag="site", atom_indices=[0, 1, 2])
    view.movie.set_baseline(1000, camera={
        "position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]
    })
    view.movie.add_track({
        "tag": "hide-site", "target": {"domain": "region", "tag": "site"},
        "property": "visible", "keys": [{"time_ms": 500, "value": False}]
    })
    recipe = view.movie.to_dict()
    view.regions["site"].delete()
    view.regions.add(tag="pocket", atom_indices=[0, 1, 2])
    review = view.movie.review_import(recipe, target_map=[{
        "source": {"domain": "region", "tag": "site"},
        "target": {"domain": "region", "tag": "pocket"}
    }])
    assert review["can_apply"], review["conflicts"]
    view.movie.apply_import(review)
    assert view.movie.evaluate(500)["visibility"][-1]["visible"] is False
```

Inspect `changes`, `affected_tracks`, `targets`, `warnings` and `conflicts`
before accepting a review. An implicit start value can change with the new
baseline. A same-name replacement of a region or named analysis requires an
explicit map too. Scientific-target associations are reported; their data are
not calculated, aligned or rewritten.
Region identifiers are local to a View. Changing their molecular definition
or dependency definitions also requires explicit correspondence.

If the destination molecular binding differs, declare all tagged targets and
provide `structure_index_map`: one source local structure index (or `None` for
a new structure) per destination structure. Every frame used by the recipe,
including its initial frame, must have exactly one destination. Missing or
ambiguous frames are conflicts. Camera coordinates stay in their original
ångström world space; a correspondence is not a spatial alignment.

Only the latest successful review belongs to that View. Scene or recipe edits
can make it stale. Acceptance rechecks the private source/options and preserves
the old Movie on error. It changes the recipe only; use `reset_async()` when
ready to apply its baseline. The compact import record survives JSON/session
save and media export. Reviewed import currently accepts version 2; legacy
version-1 recipes continue to use their existing reader and playback.

### Animating appearance

You can also change the scene's appearance without changing molecular data:

| Target domain | Properties |
| --- | --- |
| `whole`, `region` | `representation` (step), `color`, `alpha` |
| `shape` (spheres) | `color`, `alpha` |
| `interaction` | `color`, `alpha` |
| `annotation` | `text` (step) |
| `scene` | `background`, `lighting` |

Use canonical representation names and RGB integers such as `0x34D399`.
`alpha` ranges from 0 to 1. Colour transitions use linear-light sRGB; alpha
and lighting intensities interpolate independently. The recipe records the
colour interpolation rule. Text and representation changes happen at their
key times.

Configure a simple explicit representation before capturing a baseline for
structural appearance tracks. Give it a uniform colour with
`set_representation(..., color=...)` when you want a colour transition. A
per-atom colour layer on the target must be cleared first. A colour track
without a uniform baseline requires its first key at zero.

For a background track, configure an explicit colour, such as `"#101010"`,
rather than a light/dark preset. For a lighting track, set both `ambient` and
`diffuse` before capturing the baseline. Each lighting key supplies both
intensities, in the range 0 to 1. Example track values are:

```python
view.whole.set_representation("ball-and-stick", alpha=1.0)
view.movie.set_baseline(
    2000, camera={"position": [0, 0, 15], "target": [0, 0, 0], "up": [0, 1, 0]}
)
view.movie.add_track({
    "tag": "fade-whole",
    "target": {"domain": "whole"},
    "property": "alpha",
    "keys": [{"time_ms": 2000, "value": 0.2}],
})
```

`evaluate()` includes these values in its detached `appearance` list.
Seeking, preview and export apply them through the existing scene owners.
They preserve region order and supplied interaction analyses. Editing an
untracked material parameter on an animated structural target requires a
reviewed new baseline. Applying a Movie now also checks its untracked
serialized scene definition.

### Capturing and restoring the baseline

When you have composed a scene interactively, capture its actual camera and
structure rather than relying on a cached Python camera:

```python
recipe = await view.movie.capture_baseline_async(2000, timeout=5)
```

This starts a new version-2 recipe with no tracks. The duration is in
milliseconds and the timeout in seconds. The same completed draw supplies
the renderer's RGB background, ambient intensity and primary directional-light
intensity. These are dimensionless lighting values in [0, 1], matching the
supported scene controls. Unsupported values are refused rather than clamped.
Light layout, light colours and other native renderer settings are outside
this bounded capture, as are page/CSS backgrounds and transparent page compositing.
An updated frontend must advertise
`movie_environment_capture: [1]`; an older canvas is refused explicitly.

Capture leaves the visible scene and
trajectory motion alone. Finish or pause an active Movie operation first.
Timeout, cancellation and intervening edits preserve the previous recipe.
You can still use `set_baseline()` with an explicit camera when working
without a renderer.

The recipe preserves both the observed environment and its original Python
intent, including unset defaults. Seeking, preview and export reapply the
observed values; property tracks override them directly. This also works
after session recovery. Later explicit changes still require review.

To restore the recorded scene after previewing or editing it, use:

```python
state = await view.movie.reset_async(timeout=5)
```

Reset pauses motion and restores the recorded objects, camera and structure,
then waits for an acknowledged primary-canvas draw. It leaves the recipe and
scientific data unchanged. Later scene objects are removed; object changes
form one Undo step. Missing or changed named scientific analyses are rejected
before replacing objects. As with importing a state file, only recorded
environment settings are restored; unrecorded viewport/export preferences
remain unchanged. A box display absent from the baseline is hidden.

Reset returns the acknowledged state before any time-zero keys. In contrast,
`seek_async(0)` applies those keys. Cancelling or timing out a reset can leave
already accepted scene changes visible. Reset may recreate scene objects;
retrieve them again through their managers if you kept Python handles.

### Reviewing changes to the baseline

When you intentionally change the scene after authoring a Movie, review those
changes before using them as its new baseline:

```python
review = view.movie.review_rebase()
review["changes"]
review["conflicts"]
review["affected_tracks"]
```

Review does not change the scene or Movie. It keeps every track and key, and
proposes the current Python scene and structure as the new baseline. By
default it retains the original baseline camera. Supply `camera=...` explicitly
to change it; position and target use Å and up is dimensionless. Pause live
motion before reviewing: this is a headless operation, not a renderer capture.

To review the actual live camera, structure and supported environment instead,
use the asynchronous route:

```python
review = await view.movie.review_rebase_async(timeout=5)
review["changes"]
review["affected_tracks"]
```

It observes a coherent primary-canvas draw without changing the scene or
recipe. Acceptance is still `view.movie.rebase(review)`. The observation
describes that captured moment; subsequent camera/frame navigation does not
silently replace it. Static-scene and scientific edits invalidate the review.
Finish or pause an active Movie operation before capturing.

A live review carries a private per-view observation ticket. Only the latest
successful live review is retained. Recipe edits, molecular reload/reset and
closing the view retire it; a failed or cancelled capture does not replace a
previous valid ticket. A ticket cannot be transferred to another view or
recovered from a session. The accepted baseline and its environment metadata
are ordinary recipe/session data. Headless reviews remain usable without
a renderer or observation ticket.

`affected_tracks` names tracks whose implicit starting value would change.
An explicit key at zero keeps its own starting value. `changes` uses compact
summaries for large values; inspect `candidate` for the complete proposed
recipe. Missing/replaced targets, incompatible properties or a changed
molecular binding are conflicts. No track is silently dropped or rebound.

After inspecting a review with `can_apply=True`, accept it explicitly:

```python
view.movie.rebase(review)
```

Acceptance checks the original recipe and reviewed scene again. Stale or edited
reviews are rejected while preserving your latest work. Passive camera
telemetry alone does not stale a review. Rebase replaces the recipe's baseline;
it does not apply it to the canvas or recompute scientific analyses.

`validate()`, seeking, preview and export reject untracked changes to the
serialized molecular scene. Reset the recorded scene or review a rebase.
Navigation, active/saved selections, export presets and DOM plots are excluded
from this scene-definition check; plots retain their separate export-composition
policy. Frame-projected box indices and aggregate layer flags are derived
state. Unrecorded native renderer settings remain outside this check.

### Layer visibility in a Movie

A layer visibility track acts as a gate over its members. When a baseline layer
is visible, opening the gate preserves each member's initial hidden state.
A closed gate hides every member, including those with an explicit visible
member key. Member tracks keep their own schedule behind that gate. Evaluation
reports the logical layer/member intent; application composes final member
visibility before issuing commands.

An initially hidden layer has no stored latent visibility because ordinary
layer hiding has already hidden its members. Untracked members therefore open
as visible when its Movie gate opens. Give a member an explicit visibility
track to keep it hidden. Ordinary Python and Studio layer show/hide operations
continue to affect every member.

### Choosing a straight camera path

Independent tracks normally interpolate the target, distance and orientation
with a shortest-arc rotation. To move the camera position and target along
straight lines, set the experimental recipe field
`camera_interpolation="cartesian-constant-up@1"` explicitly. Camera coordinates
are in Å and key times are in milliseconds. Each segment requires the same
up vector and a safe viewing direction throughout its path; a segment that
passes through the target or becomes parallel to up is rejected before the
plan changes. The check is conservative; very ill-conditioned paths can also
be refused.

This example replaces the current Movie with a one-second camera plan on an
already loaded `view`:

<!-- cartesian-camera-example -->
```python
view.movie.set_baseline(1000, camera={
    "position": [0, 0, 10], "target": [0, 0, 0], "up": [0, 1, 0]
})
view.movie.add_track({
    "tag": "camera", "target": {"domain": "camera"}, "property": "pose",
    "keys": [{"time_ms": 1000, "value": {
        "position": [10, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]
    }}]
})
recipe = view.movie.to_dict()
recipe["camera_interpolation"] = "cartesian-constant-up@1"
view.movie.from_dict(recipe)
sample = view.movie.evaluate(500)  # position [5, 0, 5] Å
```

The field travels with the recipe, session, preview and export. Omitting it
keeps the default rotation. This option does not convert legacy keyframes;
reviewed version-1 migration remains pending.

### Preview an instant

Display the view and run this from a later notebook cell:

```python
sample = await view.movie.seek_async(750, timeout=5)
```

The seek pauses running motion, applies the camera and structure, and changes
visibility and appearance on tracked targets. It returns the sample after the
primary canvas confirms a completed draw with the requested camera and structure.
The timeout is in seconds. If the wait is interrupted, scene commands already
accepted can remain visible.

### Play and pause

For a single run, use `await view.movie.play_async()`. It returns the final
drawn sample. For a loop you can pause from another notebook cell:

```python
import asyncio

preview = asyncio.create_task(view.movie.play_async(loop=True))
```

```python
paused = await view.movie.pause_async()
await preview
await view.save_session_async("paused.msv")
```

The primary canvas chooses the next preview time after each completed draw.
Complex frames may skip intermediate samples during playback. Pause waits for
the in-flight sample. You can resume with `start_time_ms=paused["time_ms"]` or
jump to another time with `seek_async()`. The session stores the visible camera,
structure and scene with the recipe. Use `await view.movie.export_async(...)`
to [export these tracks](export.md#exporting-independent-tracks-experimental).
