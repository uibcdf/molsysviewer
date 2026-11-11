# Movie timeline model — first M1 implementation and design

This refines the accepted pre-1.0
[Movie requirement and M0 findings](pending_proposals/pre_1_0_movie_authoring_export_and_agent_timeline.md)
under [#320](https://github.com/uibcdf/molsysviewer/issues/320).

The experimental Python implementation supports independent camera, structure,
visibility and a bounded appearance catalogue. The
[implemented API and recipe example](../docs/content/user/movie/timeline.md#independent-tracks-experimental)
cover a detached baseline, edits, validation, arbitrary-time evaluation and
JSON/session persistence. The JavaScript runtime exports
`compileMovieTimeline(recipe)` for the same channels. Python's live
`seek_async()` validates binding and applies a sample through existing scene
owners, with a version-2 visual capture barrier on the primary canvas. Existing
version-1 playback uses its original recipe.
The first version-2 export route, `await view.movie.export_async(...)`, streams
correlated images to MP4/H.264, WebM/VP9 or a PNG/manifest ZIP. The
[receiving record](movie_export_receiving_20261110.json) separates source
encoder, browser and API scopes. Uniform colours/alpha, simple molecular
representations, annotation text, RGB background and ambient/diffuse lighting
have their first implementation. Complete baseline/rebase/reset, richer style
recipes, Studio authoring and a portable interactive web player remain open.
The [appearance receipt](movie_appearance_receiving_20261110.json) retains its
separate numerical, native-node, popup, session and media evidence.
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

The table describes the complete direction, not arbitrary Mol* settings. The
currently admitted appearance catalogue is specified below. For continuous keys,
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

### Received appearance catalogue

| Target | Property | Initial contract |
| --- | --- | --- |
| Whole/region | `representation` | Canonical public simple type; discrete keys. A simple explicit baseline representation is required. Presets and inherit need a later recipe contract. |
| Whole/region | `color`, `alpha` | Uniform structural RGB and opacity in `[0, 1]`. Reuse the existing representation setter with one combined material update per target; retain baseline parameters and region order. Own per-atom colour layers are refused for a uniform colour track. |
| Sphere | `color`, `alpha` | Existing sphere mutators; other shape families await their own qualified adapters. |
| Interaction visual | `color`, `alpha` | Existing style owner; no calculation or modification of named scientific results. |
| Annotation | `text` | Discrete text through the existing anchored annotation owner. |
| Scene | `background`, `lighting` | Explicit RGB; a complete `{ambient, diffuse}` record with intensities in `[0, 1]`. These baseline values must be configured explicitly. Specular is not an independent channel because the current renderer maps it to diffuse. |

Colours are canonical 24-bit integers. Recipes using colour tracks record
`color_interpolation: "linear-light-srgb-half-up@1"`: decode sRGB, interpolate
linear-light components, encode sRGB and quantize to 8-bit with nearest/half-up
rounding. The transfer follows the [W3C conversion definitions](https://www.w3.org/TR/css-color-4/#color-conversion-code);
the rounding/versioned recipe rule belongs to MolSysViewer. A Decimal control
and the real Python/TypeScript oracle guard it. Alpha and intensities interpolate
independently; representation and text hold discrete values. If a uniform
colour cannot be derived from the baseline theme, an explicit key at zero is
required. No native defaults or scientific colour calculations are guessed.

Samples add an `appearance` list only when such tracks exist. Older three-channel
samples retain their shape. Live application requires `movie_appearance: [1]`;
an older renderer is refused. The compact preview recipe carries only the
required appearance fields, not molecular coordinates or analysis occurrences.
Untracked material-parameter changes on an animated structural target require
a reviewed new baseline; complete static-scene conflict/rebase handling remains
pending. Simple region updates reuse the existing component/representation
nodes, including type changes, rather than deleting them for each material key.
They retain region priority throughout the update and preserve the existing
parent-bond context for ball-and-stick/line representations. The native guard
checks the actual boundary half-link mesh groups after reverse seeks.

The optional state `environment` stores declared background intent and configured
ambient/diffuse values. Parsing uses a closed field catalogue before mutation.
Partial lighting calls accumulate; specular fallback is recorded as diffuse.
Work files and Movie baselines preserve these settings. As with camera/navigation,
ordinary object Undo does not restore viewport environment. This is not a full
resolved renderer snapshot or qualification of arbitrary external Mol* edits.

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
and nominal constant-rate encoded duration `N*q/p`. Container timestamp
quantization is checked on decoded output for received cases; the rational
does not claim exact container timing on every codec/rate combination.
Variable-rate exports need a separate contract.

Python and TypeScript share a numerical oracle authored on a three-structure
pentalanine trajectory, with boundary and reversed seeks, same-tag targets in
distinct domains, and a generic half turn. `tests/test_movie_export.py` checks
half-open sampling, rational rates, boundaries and constant-space scheduling,
then sends the declared rate through actual H.264/VP9 encoders.
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
await view.movie.play_async(loop=False, start_time_ms=0.0, timeout=5.0)
await view.movie.pause_async()
await view.movie.export_async(path, fps="30000/1001", width_px=1280, height_px=720)
view.movie.to_dict()
view.movie.from_dict(recipe)
```

Live application and coordinated preview have draw acknowledgments. The
remaining application surface includes captured baselines, explicit target
mapping and reviewed reset/rebase behavior. Proposed calls:

```python
await view.movie.capture_baseline_async(...)
await view.movie.reset_async(...)           # restore baseline and time zero
view.movie.from_dict(recipe, target_map=...)
```

The export job has a correlated identity, synchronous progress callbacks,
task cancellation and a detached result manifest. Synchronous existing
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

Version-2 preview uses a single primary-renderer clock. The first draw request
passes a compact evaluator recipe containing the tracks and the baseline values
needed by them. Every response acknowledges the actual draw and proposes the
next sample at the renderer's monotonic time. The Python owner checks the
proposal against its recipe and issues the next sample through ordinary scene
commands. There is one outstanding draw. Popups receive scene projections
from that clock. Samples with unchanged visibility avoid overlay snapshots,
and the recipe never carries trajectory coordinates. Preview may skip times
under load and always applies the terminal sample on normal non-looping
completion. Pause drains the pending draw and returns its sample. Seeking
drains preview before starting a distinct request. A session saved after pause
restores the visible scene and the recipe.

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

The initial export route requires version-2 capture plus the explicit
`movie_frame_capture: [1]` capability on the primary canvas. It never falls
back to a placeholder. Each frame carries its job, index, dimensions,
composition and multisampling level. Python checks the echoed metadata and
PNG dimensions before decoding; a stale or malformed reply cannot complete a
new job. Revision changes during export refuse publication. This tranche
receives a scene whose static setup is unchanged after authoring: complete
static-baseline enforcement and reviewable rebasing remain M1 work, rather
than being implied by identity/target checks.

Export uses Mol*'s public image pass in an independently owned task. Abort is
cooperative at its task checkpoints and never calls a global task abort. An
in-flight GPU operation retains screenshot ownership until it actually settles.
The Movie default multisampling level is 2; the helper's previous photographic
settings are restored and interactive-canvas quality is not changed. The
renderer's remaining deadline includes the draw barrier and image capture.

Python sends one decoded RGB frame at a time to a single-thread FFmpeg pipe,
with backpressure and finite waits. MP4 uses libx264/CRF 18/medium/faststart;
WebM uses libvpx-vp9/CRF 30 without a target bitrate. The manifest records the
explicit colour conversion, provider version and executable digest. PNG ZIP
stores each lossless image immediately and appends the manifest; videos embed
it as comment metadata. Both paths use a temporary sibling destination, then
atomic no-clobber publication by default or explicit atomic replacement.
Task cancellation retires the owned encoder and removes temporary output,
preserving any existing destination. The view remains at its last applied pose.

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
