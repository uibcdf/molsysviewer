# Proposal: viewing a scene in the terminal

**Status:** post-1.0 proposal, not approved. Drafted 2026-08-02.

**Shape:** three new usage modes on a board where six already ship (§3.0). One is
documentation over an audited entry point, two share a single new component. One
policy decision and one tier are deferred.

**If you read only one section, read §5.4.** It is the cheapest item here, the only
one that yields a live interactive viewer rather than a still image, and it has no
dependency on the rest of this document.

**Companion:** [`proteinview_external_review_and_ideas.md`](proteinview_external_review_and_ideas.md),
whose §5 owns the interactive tier. Read §8 of this document together with §9 of
that one.

---

## 1. What is proposed

Show the current scene as pixels in a terminal emulator, from three callers:

```bash
molsysviewer traj.bcif.gz --terminal --frame 250
```
```python
view.show_in_terminal()                 # current scene, current frame
view.show_in_terminal(structure_index=250)
```

(The CLI spelling above assumes the decision recorded in §5 is taken in favour of
a separate display flag. It is not settled.)

No browser, no window, no port forwarding. A still image, redrawn when asked.

Frame selection is part of the deliverable, not an extension — see §5. The
motivating user has just produced a trajectory (§10), and a path that can only
render frame 0 does not serve them.

---

## 2. Why this is smaller than it looks

**The hard part already exists.** `molsysviewer/viewer/core.py:3001`
(`_export_image_headless_playwright`) builds the lite HTML through
`_build_lite_html(include_controls=False, include_popout=False,
inline_messages=True)`, serves it on an ephemeral local port, loads it in
headless Chromium, waits for the `[data-molsysviewer-rendered]` selector and
screenshots the page. `core.py:2882` does the same through Qt WebEngine, in
process, setting `QT_QPA_PLATFORM=offscreen` and forcing SwiftShader
(`core.py:2898-2903`) so that **neither a display nor a GPU is required**. Both
are already the fallback used by `exports.image` when no live frontend is
attached.

So the scene → PNG step is solved, with two independent backends. What is missing
is only PNG → terminal.

**And the CLI already parses everything.** `molsysviewer/standalone.py:349-371`
accepts `source`, `--demo`, `--selection`, `--structure-indices`, `--syntax`,
`--load-mode`, and add-on registration. `main()` builds a view and then calls
`launch_standalone0(...)` to write HTML and open a browser. Everything before
that last step is reusable unchanged.

### 2.1 The prerequisite the pixel source does not carry

**Neither rendering backend is a declared dependency**, and this materially
conditions §10.

`pyproject.toml` declares `anywidget`, `argdigest`, `depdigest`, `molsysmt`,
`numpy`, `packaging`, `pyunitwizard`, `smonitor` and `traitlets`. Playwright
appears nowhere and needs a separate `playwright install chromium`. Qt appears
only as an **empty** extra:

```toml
# The standalone Qt prototype requires PySide6_uibcdf with QtWebEngineWidgets.
# This is NOT installable via pip — use the UIBCDF conda channel
standalone = []
```

So on a default installation, `exports.image()` without a live frontend already
fails today. This proposal does not introduce that; it inherits it, and it
inherits it into the one environment where it hurts most — an HPC login node is
precisely the machine least likely to carry a browser engine.

**It is not a blocker, but it must be stated rather than discovered.** The
UIBCDF conda channel publishes the five Qt packages and they install without
compiling, so the honest description of the primary workflow is *"install
PySide6 from the uibcdf channel on the cluster, then view your trajectory"* —
not *"ssh in and it works"*. §11 makes this an entry gate, and the first-run
error message must name the fix rather than reporting a bare `ImportError`.

---

## 3. The decomposition: these are not three fronts

### 3.0 First, the axis that actually matters

It is tempting to enumerate environments — notebook, CLI, script, REPL — and treat
them as peers. They are not. The axis that decides everything is **who issues the
commands** crossed with **where the pixels appear**, and most of that board is
already covered.

| Driver ↓ · Surface → | Browser widget | Standalone HTML | Qt window | Terminal pixels | PNG file |
|---|---|---|---|---|---|
| **Notebook** | ✅ *the primary mode* | — | possible, pointless | — | ✅ |
| **Shell / CLI** | — | ✅ `molsysviewer` | ✅ `molsysviewer-qt` | 🆕 **A** (§5.2) | ✅ |
| **Python script** | — | — | ✅ `launch_standalone_qt0()` | 🆕 **B** (§5.1) | ✅ |
| **Terminal IPython** | ❌ impossible | — | 🆕 **C** (§5.4) | 🆕 **B** (§5.1) | ✅ |

**Six cells already ship.** `molsysviewer` and `molsysviewer-qt` are both declared
console scripts (`pyproject.toml:69-70`), the Qt one documented in
`docs/content/developer/public_api.md:431` and
`devguide/standalone_supported_environment.md:112`, and exercised by
`devguide/audits/standalone_qt_audit_2026_07.md`. Anyone proposing "let the CLI
open a Qt window" is proposing something that shipped some time ago; if it feels
missing, that is a discoverability problem, not a feature gap.

**Three cells are genuinely new**, and one of them is documentation:

- **A** — CLI to terminal pixels: a branch in `main()`;
- **B** — Python to terminal pixels: one method, covering *two* driver rows,
  because an IPython REPL is Python;
- **C** — terminal IPython to a live Qt window: the mechanism exists, the recipe
  does not (§5.4).

**One cell is impossible, and permanently so.** A notebook runs an IPython kernel,
so "notebook" and "IPython" are the same language layer — but what makes the widget
live is the *browser frontend and its comm channel*, not IPython.
`_export_image_impl` already encodes the distinction, falling back to the headless
backends **"when the Jupyter frontend is not ready"** (`core.py:2837`). Terminal
IPython has the kernel and no frontend: `_repr_mimebundle_` offers widget MIME
types that a terminal cannot draw. **The widget cannot be operated from terminal
IPython**, and nothing in this document changes that — it is not a missing feature,
it is the absence of a rendering surface.

What *is* reachable from a terminal REPL is the notebook **experience** rather than
the widget: `%gui qt` gives a live interactive canvas alongside a prompt that
manipulates it, which is functionally a notebook without cells. That is cell C, and
§5.4 argues it should be built first.

### 3.1 Within that cell, the callers are not fronts

CLI, Python and IPython are three **callers of one mechanism**, not three pieces
of work. Organising the work by caller is how the pixel encoder ends up written
three times — the recurring defect pattern named in §0 of the pre-1.0 master
plan, and visible in the reviewed codebase itself (§8.8 below).

The axis that actually separates work is the layer:

| Layer | State | Work |
|---|---|---|
| Pixel source | exists — `core.py:2882`, `core.py:3001` | none, but see §2.1 |
| **Terminal sink** | does not exist | **all of it** |
| Triggers | partially exists — `standalone.py:349` | minimal |

**The honest count:**

- **1** new component — the terminal sink;
- **2** triggers — one method and one CLI flag. IPython is not a third: an
  IPython REPL is Python, and calls the same method;
- **1** separate policy decision — auto-display at the IPython prompt (§5.3);
- **1** documentation-and-testing task with no new mechanism — the Qt window
  driven from a terminal REPL (§5.4), which is the cheapest item here and
  delivers the most;
- **1** deferred tier — interactivity in the terminal, which belongs to the
  companion document.

The triggers together are less work than the sink.

---

## 4. The one new component: the terminal sink

A module that converts a PNG into terminal output, owning:

1. **Capability detection** — which graphics protocol, if any, and the terminal's
   cell size in pixels;
2. **Encoders** — Kitty graphics protocol, Sixel, and a half-block fallback
   (`▀` with foreground/background colour) for terminals with 24-bit colour;
3. **Sizing** — translating available columns and rows into the `width_px` and
   `height_px` requested from the pixel source;
4. **A caption line** — see §4.1.

**Nothing else in the package may import it.** `exports.image` must not know it
exists. §8.1 gives the mechanical test that keeps this true.

### 4.1 The caption is not decoration

A one-line textual summary printed beneath the image — structure name, structure
count, atom count, displayed frame — is a requirement, not a nicety.

The reason is the tiering. At the graphics tier the picture carries the
information and the caption confirms it. **At the half-block tier the caption
carries more information than the picture**: 80×48 pixels tells you the shape of a
fold and nothing about which system produced it, how many frames it has, or which
one you are looking at. A degraded image with no caption is an unlabelled figure,
and the guiding principles do not allow one of those.

It is also the natural first consumer of the scene summary proposed in
[`proteinview_external_review_and_ideas.md`](proteinview_external_review_and_ideas.md)
§6. The caption is that summary in its most compact form. If both are built, they
share one implementation and the caption is a formatting of it; if only the
caption is built, it should be shaped so the summary can later absorb it rather
than duplicate it.

---

## 5. The triggers

**The two triggers do not select frames the same way, and the difference is not
cosmetic.** The package already has two distinct concepts and both are load
bearing:

- `structure_indices` (plural) — *which frames are loaded into the view*. This is
  what `new_view()` takes (`new_view.py:42`) and what the CLI already parses
  (`standalone.py:349-371`).
- `current_structure_index` (singular) — *which loaded frame is displayed*. A real
  public property (`core.py:1774`), read and written by the player
  (`player.py:71`, `:120`).

So `view.show_in_terminal(structure_index=500)` selects what to *draw*, and
defaults to `current_structure_index`. The CLI's existing `--structure-indices`
selects what to *load*, and would then draw the first of them. Passing
`--structure-indices 250` therefore appears to work while meaning something else:
it loads exactly one frame and draws it because it is the only one, not because it
was selected for display. There is no way to express "load a thousand frames and
show me the five-hundredth".

**Decision required before implementation:** either the CLI gains a separate
display flag (`--frame`) distinct from `--structure-indices`, or the documentation
states plainly that the CLI only loads and always draws the first loaded frame.
The first is the better answer; the second is acceptable if it is written down.
What is not acceptable is leaving the two triggers looking equivalent when they
are not.

### 5.1 Python

One explicit method. This is the base surface and the only one that must exist.
It renders the current scene state on each call.

**It must return `None`.** In an interactive REPL, a returned value is echoed by
the interpreter immediately after the image is written, so any return value
appends a stray `repr` under every picture. This is invisible in a script and
unavoidable in IPython, which is exactly the environment the method is most used
in.

### 5.2 CLI

A `--terminal` flag on the existing entry point, branching before
`launch_standalone0`. Everything it needs is already parsed.

### 5.3 IPython auto-display — a decision to take, not a gap to fill

The only thing that makes IPython genuinely different from Python is auto-display
at the prompt: typing `view`, pressing enter, and seeing the molecule. This is
policy, not mechanism, and it is very likely what a reader pictures when they ask
for "IPython support", so the decision is written out here rather than left open.

The risk is concrete: `__repr__` is invoked in tracebacks, in logs, in pytest
output, and whenever a container holding the object is printed. A `__repr__` that
emits graphics escape sequences writes them into all of those places.

**The options:**

- **(a) Do nothing.** `view.show_in_terminal()` works in the IPython REPL because
  IPython is Python. No auto-display. Zero risk, zero work.
- **(b) Opt-in per session.** Something like
  `msv.config.terminal_display = True` installs an IPython display hook for the
  viewer type. Off by default, so no caller is surprised; discoverable through
  config. Interacts with the existing `_repr_mimebundle_` used by Jupyter, which
  must keep taking precedence whenever a real frontend is attached.
- **(c) On by default when the REPL is interactive and a graphics protocol was
  detected.** Best ergonomics, highest risk: detection would have to run at
  display time, and any misdetection writes escape bytes into a traceback.

**Recommendation: (a) for the first slice, (b) as the follow-up if asked for.**
(c) should not be built — it trades an unbounded correctness risk for keystrokes.

Whichever is chosen, it is a separate slice with its own tests and does not gate
§5.1 or §5.2.

### 5.4 A real Qt window driven from a terminal REPL

There is a fourth workflow, it is not a still image, and the machinery for it
already exists.

When a display *is* available but the user prefers a terminal REPL to a notebook,
IPython's `%gui qt` integrates the Qt event loop with the prompt's input loop. The
viewer can then open a **real Qt window with a live, interactive Mol\* canvas**
while the user keeps typing in the terminal. Full interactivity, panels, mouse
picking — everything the notebook gives, driven from a REPL.

**What already exists — more than the mechanism:**

- **A shipped, documented, audited entry point.** `molsysviewer-qt` is a declared
  console script (`pyproject.toml:70`), listed in
  `docs/content/developer/public_api.md:431` and
  `devguide/standalone_supported_environment.md:112`, and exercised by
  `devguide/audits/standalone_qt_audit_2026_07.md:97`, which runs it with
  `--no-exec`. The Qt shell is not a prototype waiting to be finished; it is
  released surface.
- `launch_standalone_qt0(..., exec_app: bool = True)`
  (`molsysviewer/standalone_qt/application.py:195`), whose `:218` reads
  `runtime["exit_code"] = runtime["app"].exec() if exec_app else None`. Passing
  `exec_app=False` builds the window **without entering the event loop**, which is
  exactly what `%gui qt` requires — IPython owns the loop and the application must
  not call `exec()`.
- The CLI already exposes it as `--no-exec`
  (`molsysviewer/standalone_qt/main.py:42`).
- `application.py:119` already stashes `view._qt_process_events`, so pumping the
  loop from Python is an anticipated pattern.

**What is missing is not code.** It is a documented, tested recipe: the `%gui qt`
incantation, the `exec_app=False` call, what happens on a second window, what
happens when the REPL exits, and possibly one convenience wrapper so users are not
calling `launch_standalone_qt0` by hand.

**It does not replace the terminal path, it complements it.** Qt needs a display;
the primary consumer of §10 is a headless cluster node and cannot use it. The two
cover different rows of the §3.0 table:

- display available, REPL preferred over notebook → Qt window, full interactivity;
- no display at all → terminal pixels, still image.

**Scheduling: do this first.** It is the cheapest item in this document and it
delivers the most, because it reuses a finished, audited Qt shell instead of
building a renderer, and it produces a *live interactive viewer* rather than a
still image. It also has no entry gate of its own beyond the Qt install
prerequisite — unlike the terminal sink, it does not wait on master-plan Phase 4a,
because it does not touch `_build_export_messages()` or `_build_lite_html()`.

If only one thing from this document is ever built, it should be this one. It is
kept here rather than split into its own proposal because it answers the same
question — "how do I look at my system without a notebook" — and because whoever
implements one should know the other exists.

**Caveat:** it inherits the Qt install prerequisite of §2.1 in full, and
`qt_popout_parity.md` in this directory records that the Qt shell is built with
`include_popout=False`, so popup-dependent workflows behave differently there.
That gap is owned by that document, not this one.

---

## 6. Deferred: interactivity

Rotating with the keyboard requires a persistent headless page — today
`_export_image_headless_playwright` launches and closes a browser per call
(`core.py:3073`, `:3092`) — plus a re-render loop, raw-mode input, and a
per-frame latency budget.

**This is the same machine as
[`proteinview_external_review_and_ideas.md`](proteinview_external_review_and_ideas.md)
§5** (the agent-facing control surface): a persistent headless page that owns the
state, receives commands, and replaces the frame. An agent driving it over NDJSON
and a human driving it with arrow keys are two drivers of one mechanism. Design
them separately and we build the machine twice.

**It also changes the classification of this work.** The still-image tiers are a
*consumer* of the existing headless export and add no control-plane surface — they
do not widen the endpoint matrix that master-plan Phase 5 must close. The
interactive tier is a genuine new endpoint and does. That is the line between the
two, and it is why they are in different documents.

---

## 7. Honest limits

**Resolution has a hard ceiling without a graphics protocol.** Half-blocks give
two vertical pixels per cell, so an 80×24 terminal is 80×48 pixels. That is enough
to recognise a fold and confirm you loaded what you meant to load. **It is not
enough to do science and it is not a figure.** The documentation must say so, and
the still-image path must not be presented as an alternative to `exports.image`.

**Terminal support is partial.** Kitty, Ghostty, WezTerm, iTerm2 and foot expose a
graphics protocol. GNOME Terminal, xterm and the VS Code integrated terminal do
not, and fall back to half-blocks. Windows Terminal added Sixel in 1.22; older
builds and the legacy console fall back to half-blocks — which means that if
Sixel is descoped from the first slice (§7.1), Windows is a half-block platform
by our choice, not by its limitation, and the documentation must say which.
Passthrough under tmux and screen is fiddly and should be treated as unsupported
until someone verifies it on a real machine.

### 7.1 Descoping Sixel is the recommended first cut

The three encoders are not equally hard. Half-blocks are a resize plus two ANSI
colour codes per cell. Kitty accepts PNG bytes directly (`f=100`), so we can hand
it what the pixel source already produced. **Sixel is the outlier**: it requires
palette quantisation to at most 256 colours and a bit-plane encoding that nobody
should hand-write.

Kitty plus half-blocks already covers Kitty, Ghostty, WezTerm and every remaining
terminal at reduced quality. Sixel adds foot, older iTerm2 builds and modern
Windows Terminal at real resolution. That is a genuine gain and it is not worth
blocking the first slice on; take it as a second slice, with a library rather than
a hand-rolled encoder.

**The half-block fallback has its own precondition.** It assumes 24-bit colour.
A terminal limited to 256 colours needs quantisation, which degrades further; that
is the floor of the tiering and should be measured against a real 256-colour
terminal rather than assumed to look acceptable.

**A rendering backend must be installed** — see §2.1.

**Latency is unmeasured, and per this directory's rules the benchmark is recorded
before implementation, not after:**

- *Home:* `molsysviewer/tools/benchmark.py`, which already hosts
  `benchmark_loading`, `benchmark_coordinates`, `benchmark_serialization` and
  `run_benchmarks`. Add a `benchmark_headless_render` beside them rather than a
  standalone script.
- *Fixture, single structure:* `demo["1TCD"]` (`molsysviewer/demo.py:63`,
  `1tcd.bcif.gz`), already shipped.
- *Fixture, trajectory:* **does not exist as a demo** — `demo.py:63-64` ships only
  `1TCD` and `181L`, both single structures. A multi-frame fixture must be named
  from the test corpus or added before the trajectory arm is measured. This is a
  known hole in the benchmark plan, not an oversight to be discovered later.
- *Measurement:* wall time of one export at 1280×720, per backend (Qt and
  playwright), separating first call from subsequent calls, since playwright pays
  a full browser cold start per call today. Report median and spread over ten
  repetitions, with the two structural axes this directory requires kept separate:
  atom count and structure count.

No latency number is claimed anywhere in this document.

---

## 8. Implementation lessons from ProteinView

Drawn from `~/repos@others/ProteinView` (v0.3.0, read 2026-08-02). These are traps
already paid for by someone else. Ordered by what they save us.

### 8.1 How to prove a library does not dirty the terminal

`tests/snapshot_cli.rs:31-32`:

```rust
assert!(!result.stdout.contains(&0x1b));
assert!(!result.stderr.contains(&0x1b));
```

The ESC byte must never appear in stdout or stderr of the headless path. The
companion unit test is named `writes_a_fullhd_png_without_terminal_setup`
(`src/render/snapshot_tests.rs:48`).

This matters more to us than to them, because we are a **library**. If
`exports.image` ever emits an escape sequence — because someone reused code from
the terminal sink — it corrupts output for callers running under scripts,
`nbconvert`, or pytest. Their design rule follows from it: the snapshot path
*deliberately* skips terminal detection and alternate-screen setup
(`src/render/snapshot.rs:41-43`) so that agent tools can call it without nesting
one TUI inside another, and their panel server never emits graphics escapes at
all, keeping diagnostics on stderr.

**Adopt as an exit criterion of the first slice**, mechanically checkable, in
pytest.

### 8.2 Capability detection queries the terminal and can hang

`src/main.rs:363`:

```rust
let picker = Picker::from_query_stdio()
    .unwrap_or_else(|_| Picker::halfblocks());
```

with an ordering warning at `:353`: detection must happen *after* terminal setup.

Detecting Kitty or Sixel is not reading an environment variable — it writes a
query sequence and waits for a reply. It has ordering constraints, needs a
timeout, and hangs if nothing answers.

For us the consequences are worse: detection must never run at import time, and
must never run inside a Jupyter kernel or a pytest session, where stdin is not a
terminal and waiting for a reply means hanging the caller. **Lazy detection, only
when terminal output is explicitly requested, with a timeout and an
unconditional fallback.** Their unconditional `unwrap_or_else` is the right
shape.

### 8.3 Atomic image replacement in Kitty, or it flickers

`src/render/kitty_png.rs:38-40` and `:73-76`: a **fixed image ID**, retransmitted
with `a=T,U=1`, makes Kitty replace the image data atomically — "no flicker, no
delete-before-draw gap". No delete commands are issued during normal rendering.

The naive approach — delete, then draw — flickers on every frame.

The counterpart is `cleanup_escape()` (`:56-62`), which must be emitted when
leaving graphics mode to free terminal-side memory. Without it, dead images
accumulate in the terminal. Both are defects we would otherwise have found by
suffering them.

**Do not apply this to the first slice.** In-place atomic replacement is correct
for a full-screen TUI that redraws one frame over another. A REPL or a shell
session is a scrolling transcript: successive calls must *append*, exactly as
successive outputs do, so that the record of the session stays readable. An
implementer who applies the fixed image ID here would make the second call
overwrite the first and fight the terminal. This lesson belongs to the deferred
interactive tier of §6; what the first slice needs from this section is only
`cleanup_escape()` hygiene.

### 8.4 Terminal cells are not square

`src/ui/viewport.rs:85-99` computes pixel dimensions as `columns × font_w` by
`rows × font_h`, and only treats the terminal as graphics-capable when
`font_w > 0 && font_h > 0`. The character fallback uses a different resolution
again: `cols*2 × rows*4` for braille (`cols × rows*2` for half-blocks).

Cells are typically twice as tall as wide. Requesting a PNG sized to columns and
rows without accounting for this produces a squashed molecule. For us this
determines exactly which `width_px`/`height_px` we ask the pixel source for, and
what we do when the terminal will not report its cell size.

### 8.5 Bound dimensions before rendering — see §9

`src/render/snapshot.rs:21-23`: minimum 64, maximum 4096 per side, maximum
8,388,608 total pixels, validated before rasterising, with a dedicated test
(`snapshot_tests.rs:77`).

### 8.6 Atomic file replacement

`src/render/snapshot.rs`: a temporary file named with PID and an atomic counter,
opened `create_new(true)` so the reservation cannot race, written, `sync_all()`ed,
then renamed over the target.

We currently write straight to `output_filename`. That is harmless for a one-shot
export and stops being harmless the moment a persistent frame path exists that
another process re-reads — that is, in the deferred tier of §6. A reader can
otherwise catch a half-written PNG.

### 8.7 Compress cheaply, not well

`kitty_png.rs:68-70`: raw RGBA with zlib at **level 1, the fastest**, base64-chunked
at 4096 characters per chunk (`:100`). They measure ~10–20× smaller than
uncompressed RGBA, which is what makes pixel graphics usable over SSH
(`viewport.rs:127-129`).

Encoding sits inside the frame latency budget, so compression level is chosen for
speed. Chunking is not optional; the protocol requires it.

### 8.8 A drift lesson, free of charge

`kitty_png.rs:47`: *"Named `KittyPngImage` for historical reasons; the actual
encoding is zlib-compressed raw RGBA, not PNG."*

Their README advertises a "PNG-compressed Kitty protocol" in its first feature
line. The code says otherwise. Same §0 pattern the master plan chases in Phase 9,
with the aggravation that the type name lies too.

### What does not transfer

Everything that depends on owning the rasteriser. Rendering at half resolution
during interaction and letting Kitty upscale through `c=/r=`, compensating camera
zoom and pan so the molecule occupies the same relative area
(`viewport.rs:100-112`), is elegant and irrelevant to us: we do not drive our own
camera, we would resize the Mol\* canvas. It would only matter in the deferred
tier anyway.

---

## 9. One gap this work exposes but does not own

Verified 2026-08-02: `core.py:2948` and `core.py:3069` both do

```python
w = int(width_px or 1280)
h = int(height_px or 720)
```

with **no bounds of any kind**, and pass the result directly to
`browser.new_context(viewport={"width": w, "height": h})` and to the Qt backend.

This is not a defect of the terminal path — it already exists in image export
today, reachable through the public `exports.image` API. This work would only make
it easier to reach. §8.5 is the shape of the fix: named minimum, maximum per side,
and maximum total pixels, validated before any backend is started, with a test.

**Routing note.** This belongs to whoever triages image export, not to this
document. It is post-1.0: a caller passing an absurd dimension is user-supplied
input in the user's own process, failing immediately and visibly. It is neither a
correctness nor a distribution blocker. It is recorded here because this is where
it surfaced, with its fix already described one section above.

---

## 10. Who asks for this

Master-plan §4.B requires a demonstrated consumer before a new public surface is
created. Two exist:

1. **MolSysSuite users on an HPC cluster.** SSH session, trajectory just produced
   on disk, no browser, no port forwarding, and the need to look at what came out.
   This is the primary case and it has no answer today. **Read together with
   §2.1:** it requires installing a rendering backend from the UIBCDF conda
   channel on that cluster. That is one documented step, not a blocker, but the
   workflow must be described honestly and the missing-backend error must name
   the fix.
2. **Agent and terminal-first development sessions**, including the ones in which
   this viewer is itself developed and debugged.

The first is scientific and specific enough to satisfy the gate. The second is
convenience and should not be used to justify the work on its own.

---

## 11. Entry gates and exit criteria

**Suggested order.** §5.4 (cell C) first — it is documentation over shipped code,
gated only on the Qt prerequisite. Then the go/no-go measurement below. Then the
terminal sink and its two triggers (cells A and B) as one slice.

**Entry gates** (for the terminal sink; §5.4 has only the §2.1 prerequisite):

- the 1.0 API freeze has ended;
- **master-plan Phase 4a has landed.** The terminal path calls
  `_build_export_messages()` and `_build_lite_html()`, the same machinery Phase 4a
  canonicalises for static export. Whatever 4a decides about that path, this
  inherits. Starting first means building against a surface that is scheduled to
  change;
- a rendering backend installation path is documented for the target environment
  (§2.1).

**One measurement should precede all of it.** Before any of the above, time
`view.exports.image(...)` twice on each available backend. It costs minutes and it
answers the only question that decides whether this feature is worth building: if
a still frame takes several seconds, the ergonomics collapse and nobody will call
it twice. The full benchmark of §7 is run during implementation; this single
number is a go/no-go and should be taken first.

**Exit criteria for the first slice** (mechanical, per master-plan Phase 3
discipline):

1. A pytest asserts that no `0x1b` byte appears in stdout or stderr for
   `exports.image` and for every headless export path (§8.1).
2. The terminal sink module is imported by exactly one caller path; a structural
   check confirms no other module imports it.
3. Capability detection is never executed at import time, and is proven not to run
   under pytest.
4. The half-block fallback renders on a terminal with no graphics protocol, and
   is the path taken whenever detection fails or times out.
5. Frame selection is exercised on a multi-frame fixture from both triggers, and
   selecting frame *n* produces a different image than frame 0. The load-versus-
   display distinction of §5 is resolved in code and in the CLI help text, not
   left to the reader.
6. The caption (§4.1) is emitted at every tier, and a test asserts it names the
   displayed frame index.
7. The Python trigger returns `None`.
8. With no rendering backend installed, both triggers fail with a message naming
   the conda channel and package, not a bare `ImportError`.
9. The documented resolution ceiling (§7) appears in the public docstring of the
   trigger method, not only in this document.

**Explicitly out of scope for that slice:** IPython auto-display (§5.3, where
option (a) is the recommendation and requires no work), interactivity (§6), and
the dimension bounds (§9), each of which is owned elsewhere.
