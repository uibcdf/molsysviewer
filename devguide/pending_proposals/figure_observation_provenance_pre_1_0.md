---
summary: Preserve detached producer-owned reproducibility context in retained scientific figures.
issue: uibcdf/molsysviewer#349
status: partial
opened: 2026-11-10
closed:
verification: measured
area: [figures, plots, provenance, persistence, addons]
guard:
normative:
blocked_by: []
supersedes: []
---

# Scientific figure observation context

**Core implemented and received; producer publication for review pending.** The principal maintainer
accepted this additional pre-1.0 work on 2026-11-10 under #315. It does not
change the original 46-item denominator. Cross-component boundary review is
tracked in uibcdf/molsyssuite#179; MolSysMT owns the first scientific producer.

## What and why

The retained core plot stores numeric series, labels and axes, whereas the
mounted addon report holds the exact calculation context. Clearing the report
can therefore leave a figure that cannot distinguish different populations,
weights or references. Preserve the observation context with the figure rather
than re-running calculations or retaining the entire mounted panel.

## Contract to implement

The producer supplies optional, versioned, detached JSON metadata. Core owns
safe validation, literal presentation, copying and persistence; the producer
owns scientific interpretation and population/reference correspondence. Old
plot calls and serialized figures without this extension remain valid.

Each calculated series needs its method/software/parameters, exact ordered
populations and reference, weights and mass source, native and displayed units,
structure coverage and declared input/revision linkage. Repeated indices and
nonconsecutive structures are scientifically meaningful. Use bounded decoding
and efficient exact representations rather than silently shortening provenance.
A digest is not a substitute for the data or qualified artifact it identifies.

Historical observations survive Clear and later edits. Current applicability
is separate: declared IDs/maps and managed revisions do not authenticate a
molecular source, and arbitrary external edits remain unobserved. Exact
reproduction requires preserved molecular and independent reference inputs.
Do not introduce a competing scientific result store, an implicit recalculation
or a requirement that every third-party addon adopt an unpublished schema.

## Receiving and ownership

Exercise real MolSysMT-produced observations, weighted and repeated populations,
independent references and nondefault units. Check detached copies, malformed
input rejection without scene changes, retained data after Clear, undo/redo,
state/session recovery and both popup boundaries. Render metadata as literal
content. Keep source, hosted, installed and human acceptance separate.

The implementation should settle the optional Python/serialized field and
unknown-schema behavior in a maintained core contract, with producer changes
submitted to MolSysMT as an owner-reviewed PR. This document records adopted
intent; it does not claim an implemented or stable scientific schema.

## Source receiving — 2026-11-10

The [receipt](../figure_observation_receiving_20261110.json) receives the
optional core field, public call-shape review, native producer and actual
browser/Jupyter/native Qt boundaries. The [core contract](../figure_observation_contract.md)
owns limits and historical/current semantics. The producer remains a separate
owner-reviewed contribution; this checkpoint does not declare its publication
or integration complete. Original progress stays 37/46; B4 is additional.
