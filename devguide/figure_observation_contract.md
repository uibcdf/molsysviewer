# Historical figure observations

This additive core contract preserves optional producer-owned scientific
context. The new source surface is experimental until its covering receiving
and candidate review; it does not establish a common scientific result format.
Scientific schema ownership remains with the producer. B4 is tracked in #349,
with the cross-component boundary in uibcdf/molsyssuite#179.

`view.trajectory_plot.show(..., observations=[...])` and `update(...)` accept
one JSON object or `None` per series in display order. Each object declares a
nonempty `schema` string. Core preserves unknown schemas as literal opaque
context; it does not interpret them, recalculate results, infer a molecular
source or silently migrate scientific semantics. Omitting observations on a
replacement supplies a figure without context; restoring `show(tag=...)`
retains the existing context. Supplying context without replacement series is
an error. Earlier calls and saved cards without this extension remain valid.

An observation is a detached UTF-8 JSON object, limited to 4 MiB, depth 24 and
200,000 visited nodes. Numbers must be finite; integers must be interoperable
with binary64 consumers. Producers explicitly encode larger integers and exact
binary values where needed. Cycles, unsupported Python objects, invalid keys,
and oversized records are rejected before attachment, without truncation.
The MolSysMT producer uses the registered PyUnitWizard QuantityRecord
contract, including explicit units and reader handshakes; core preserves those
envelopes as opaque JSON and does not authenticate their scientific source.
These per-record limits are not a universal scene, input-file or process RAM
limit. Scientific input artifacts remain necessary when a complete recipe
cannot fit; their bytes must be preserved, not replaced by a digest alone.

Each retained series stores `observation`, `observation_count` and
`observation_rows`. Initially the row map is `0..n-1`. Extraction slices plotted
values and the row map together, including repeated/nonconsecutive structures,
while preserving the original context and original row count. Further
extractions compose through that retained map. Atom extraction likewise does
not rewrite historical scientific inputs into a new analysis. The current
plotted frame is local; its observation row refers to the original calculation.

Context survives hidden cards, state/session recovery, copying, canvas-popup
projection and scene checkpoints. Plot operations retain their existing lack
of a dedicated Undo promise. Ordinary undoable scene changes preserve the
figure's context through restoration. Detached Studio controls its canvas;
it does not become an additional figure renderer. A DataCard popup retains the
same context as its source card. Explicit figure clearing removes the figure;
clearing a producer's mounted report leaves an adopted core figure intact.

Calculation details are initially collapsed, populated on opening and rendered
as literal selectable text. Opening a record or following the trajectory never
executes metadata or turns supplied strings into HTML or links. This is a
historical observation, separate from current applicability. Managed revisions
and declared IDs/maps do not authenticate molecular origins or observe arbitrary
raw-array edits. Exact reproduction also requires the original molecular and
independent reference inputs, environment and qualified scientific method.

The first native producer uses `molsysmt.figure_observation@1`. MolSysMT owns
its method/default/parameter encoding, ordered population/reference axes,
mass-source readings and effective weights, units, software observations and
series projection. Core does not require that schema of third-party addons.
Consumer guards are `tests/test_figure_observations.py` and the existing real
trajectory-plot browser entry; source, hosted, installed and human acceptance
remain separate in the owning receiving record.
