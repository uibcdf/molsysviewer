# Movie timeline model — first M1 implementation and design

This refines the accepted pre-1.0
[Movie requirement and M0 findings](pending_proposals/pre_1_0_movie_authoring_export_and_agent_timeline.md)
under [#320](https://github.com/uibcdf/molsysviewer/issues/320).

The experimental Python implementation supports three independent channels:
camera pose, structure index and visibility. The
[implemented API and recipe example](../docs/content/user/movie/timeline.md#independent-tracks-experimental)
cover a detached baseline, edits, validation, arbitrary-time evaluation and
JSON/session persistence. The JavaScript runtime exports
`compileMovieTimeline(recipe)` for the same three channels. Python's live
`seek_async()` validates binding and applies a sample through existing scene
owners, with a version-2 visual capture barrier on the primary canvas. Existing
version-1 playback uses its original recipe.
The sections below describe the broader M1–M6 design and its remaining work.

## One model, several consumers

A Movie is a detached scene baseline, molecular/scene correspondence, a finite
duration and independent typed property tracks. An evaluator produces a complete
desired visual state at an arbitrary time. Preview, seeking, image sampling,
video encoding, portable web playback and later agent authoring consume that
same validated model. An agent produces an inspectable plan; it does not acquire
a private playback engine or run molecular preparation during playback.

Keep `view.movie` as the Python owner. Timeline editing, validation, inspection,
serialization and pure evaluation work without a frontend. Applying a pose,
capturing the current camera and rendering require their explicit live-host
contracts. `to_dict()`/inspection and accepted imports have no nested aliases;
an invalid edit/import leaves both the previous timeline and scene unchanged.
ArgDigest, SMonitor, existing scene identities and PyUnitWizard remain the
owning boundaries. A new schema does not promote scientific interactions.

An empty Movie remains a legitimate unconfigured manager: `clear()` returns to
that state and does not invent a baseline or alter the scene. A configured
positive-duration plan with no changing tracks is a valid static hold. Do not
carry forward the old requirement for two global keyframes. GUI form drafts
remain separate from the accepted plan; an unfinished form cannot replace the
last valid movie. Empty serialization must be an explicit supported variant,
not a malformed executable plan accidentally admitted by the reader.

## Baseline, targets and changes to the molecular system

The baseline reuses a detached scene-state record and explicitly supplied camera;
it does not recursively contain its own Movie. Scientific coordinates and
analyses are referenced once through session/web assets, not copied into each
key. A recipe references those assets and cannot alone promise a playable web
presentation. A session contains the necessary molecular system and analyses.

Targets use existing domain/tag identity, with region UID correspondence where
that existing contract applies. A tag alone is not a cross-domain identity.
Tracks refer to existing regions, shapes, annotations, measurements, interaction
representations, layers and overlays; they do not invent a competing object
registry. New objects can be authored before the baseline with initial
visibility false. Showing an interaction uses supplied analysis and preserves
evaluated-empty versus unevaluated structure coverage.

Validation checks target existence, compatible property/representation,
structure bounds and declared molecular correspondence. Missing or ambiguous
targets are errors, not silent omissions. Renaming, extraction or atom/structure
remapping uses the existing correspondence tools and an explicit target map;
if a required target cannot survive, the derived timeline is reported unusable
until repaired. Do not infer correspondence from `source_id` or authenticate
arbitrary raw molecular edits. Managed edits invalidate the affected compiled
plan. Arbitrary external edits still require explicit application/invalidation.
Asset digests establish byte correspondence with a preserved plan, not the
authenticity of a molecular source or the scientific validity of an analysis.

Changing the scene after baseline capture cannot silently redefine the movie.
Compilation records its expected scene/system revision. Incompatible edits
interrupt application and request explicit revalidation/rebasing. Rebase is a
reviewable operation with a target/conflict report, not an automatic replacement
of recorded choices. Importing a recipe alone does not apply it to the scene.

## Channels and interpolation

Each track owns one `(domain, target, property)`; simultaneous keys in different
tracks are independent. There is one writer per property. Duplicate keys at the
same time in a track, overlapping writers and unsupported properties are
rejected transactionally. Explicit key replacement is an edit operation.

| Property | Values and evaluation |
| --- | --- |
| Camera pose | Target, positive target distance and orthonormal orientation; interpolate target/distance and shortest-arc unit quaternion orientation. Reject degenerate input. Keep projection mode separate and discrete. |
| Camera lens/clipping | Supported field of view, fog and clipping settings with finite ranges; interpolate only fields whose renderer contract admits continuous change. |
| Structure | Explicit structure indices; held discrete keys. A sweep helper expands a declared ordered list into keys and never interpolates coordinates implicitly. |
| Object/layer visibility | Boolean step keys through the existing domain and region enable/visibility semantics. A hidden representation does not erase an analysis. |
| Representation | A validated representation recipe; step change. Preflight rejects a representation incompatible with its target. |
| Colour/opacity | Explicit supported uniform colour or colour-map recipe; discrete maps, continuous uniform RGB/opacity only. Interpolate uniform colour in linear-light sRGB and record that definition, with cross-language transfer/rounding tests. No implicit recalculation of colour properties. |
| Labels, measurements and overlays | Text/content/anchor recipes step; visibility and supported opacity have their own tracks. Reuse existing atom/coordinate anchor and quantity contracts. |
| Lighting/background | Explicit supported renderer fields, with validated finite ranges. Discrete presets are expanded to recorded settings; unsupported controls fail validation. |

The supported property catalogue starts with the three channels above;
this table does not promise arbitrary Mol* settings. For continuous keys,
interpolation uses the outgoing key's named easing. A baseline value is the
implicit key at zero when no explicit zero key exists. Before the first explicit
step key the baseline holds; after the last key the last value holds. Evaluation
is a pure function of baseline, tracks and time: reverse seek, loops and repeated
seeks produce the same values. Inserting a visibility key cannot split a camera
segment. A full orbit uses intermediate keys to express its intended path,
rather than asking shortest-arc interpolation to infer a complete turn.

Camera orientation uses shortest-arc quaternion interpolation. JavaScript uses
the installed Mol* quaternion and vector primitives, with the same near-parallel
threshold as Python. At a half-turn tie (`abs(dot) <= 1e-12`), both evaluators
make the first quaternion component above that tolerance positive, in XYZW
order, and interpolate as if the dot product were zero. This selects one of the
equally short arcs consistently when roundoff changes the sign of the dot.

## Time and physical quantities

All times are finite and nonnegative, duration is positive and every key is
within duration. Keep existing numeric `*_ms` arguments explicitly in
milliseconds; general quantity arguments use the public PyUnitWizard boundary.
Persist time and camera length quantities with their explicit field/unit
contracts. Camera orientation/up and opacity are dimensionless. A v1 camera's
position/target are explicitly Å; its up vector is dimensionless despite the
old docstring's wording. Never apply the length unit to up.

Export specifies a rational positive frame rate `p/q` and constant-rate samples
`t_k = k*q/p`, with `N = max(1, ceil(duration_seconds*p/q))` samples over the
half-open movie interval. Evaluate the first sample at zero and do not append
an extra encoded frame merely to display the exact endpoint. The final encoded
sample precedes the duration by at most one frame interval; inspection/preview
can evaluate the exact endpoint, and an explicit final hold supplies a desired
ending. The manifest records duration, exact sampling rule, rate, sample count
and actual encoded duration. Variable-rate exports need a separate contract.

Python and TypeScript share a numerical oracle authored on a three-structure
pentalanine trajectory, with boundary and reversed seeks, same-tag targets in
distinct domains, and a generic half turn. Frame sampling for encoded output
will receive its own numerical tests alongside playback and export.
Finite JSON and safe integer bounds apply at the transport boundary. No field
silently changes under a different application unit policy.

## Python authoring and planned application

The implemented methods author and evaluate generic typed tracks:

```python
view.movie.set_baseline(duration_ms, camera=camera, state=scene)
view.movie.set_duration(duration_ms)
view.movie.add_track(track)                 # one tagged target/property and its keys
view.movie.update_track(tag, keys=keys)
view.movie.remove_track(tag)
view.movie.validate()                      # raises if binding or targets are invalid
view.movie.evaluate(time_ms)               # detached desired state
await view.movie.seek_async(time_ms, timeout=5.0)
view.movie.to_dict()
view.movie.from_dict(recipe)
```

The planned application surface adds coherent live capture, coordinated
playback, explicit target mapping and rendering acknowledgments. Proposed calls:

```python
await view.movie.capture_baseline_async(...)
view.movie.play(...)
await view.movie.stop_async(...)            # drain pending writes, freeze pose
await view.movie.reset_async(...)           # restore baseline and time zero
view.movie.from_dict(recipe, target_map=...)
```

Review the application signatures before implementation. Add a correlated
export job with progress/cancel/result
rather than exposing an uncorrelated View-wide frame list. Synchronous existing
calls need a declared compatibility route; a notebook cannot block its own
comm event loop while waiting for frames. Preserve user-facing semantics or
provide an explicit reviewed migration rather than silent signature drift.

## Application, playback and export ownership

The first live route is a single Python seek. It validates the recipe and
reserves the reply before applying commands, pauses trajectory and camera
motion, and sets the evaluated camera and structure. It applies visibility
only on tracked targets, using each domain's existing semantics. One scene
history operation groups those visibility changes. The primary canvas samples
the camera and structure after frame projections and draw are current. The
reply must match the pose and stopped structure. Cancellation or timeout
retires the request and can leave already accepted changes on screen. A changed
recipe, scene or navigation intent invalidates the acknowledgment.

One execution owner arbitrates Movie, trajectory playback and camera spin/rock.
Starting Movie explicitly pauses competing motion. Each application has a
generation/request identity and awaits structure data, representation/anchor
refresh, overlays and actual final draw. Stale work cannot report completion
for a replacement job. Stop drains pending writes and leaves the observed pose;
Reset explicitly returns to baseline. Neither implicitly restarts prior clocks.
Reuse the existing frontend request, coherent-capture and owned streaming
boundaries instead of introducing another uncorrelated event list. A stopped
or sought Movie records its applied time and visual overrides with the scene;
coherent saving must preserve that actual pose and its executable timeline,
rather than refusing every scene that has ever used Movie visibility.

Evaluate independent channels first, then apply only differences through
existing scene owners; do not rebuild the entire scene at each frame. Bound
in-flight frames and encoded storage. Video export streams frames to a qualified
encoder with backpressure and uses an atomic destination. Cancellation, host
loss, unavailable codecs and invalid images produce explicit terminal outcomes,
clean up owned resources and preserve an existing destination. A placeholder
image is never a successful movie. The export manifest retains plan/assets,
runtime/encoder identity, units, sampling, resolution and actual outcome.

Media composition explicitly includes the molecular canvas and selected visual
overlays, without Studio, toolbars or authoring controls. Native geometry and
DOM plots/legends cannot silently receive different export treatment. The same
composition descriptor declares included layers and their placement at export
resolution. An unsupported visible overlay needs a clear refusal or an explicit
user choice to exclude it; a successful file cannot quietly omit part of the
authored story. Historical figure context remains available in the preserved
plan/assets even when its expandable details are not painted into each frame.

Portable web export contains the same plan, molecular/analysis assets and
identified runtime, plus a player with play/pause/seek and an explicit asset
loading policy. It must work from its documented deployment route without a
Python kernel, and must not quietly depend on an owner's local paths. Offline
packaging and network dependencies must be stated and tested separately.

## Migration and receiving

The version-2 recipe is fully validated before replacement. Migrate detached
v1 camera/structure keys into independent tracks with explicit units and a
supplied baseline. Resolve old untyped visibility tags only when unambiguous;
otherwise require a domain map. Preserve the original recipe and return a
migration report. Unknown future schema versions are rejected.

M1 acceptance needs genuine bundled molecular demos, immutable inspection,
invalid-import preservation, target collisions/remapping, nondefault units,
cross-language arbitrary-time oracles and save/reopen integration. M2–M6 then
receive the actual pocket/ligand/interactions/labels story, calm Studio
authoring, both popup routes, real final draws, useful readable video and
portable web playback. Source tests do not substitute for these outputs or
their installed/native/human scopes.
