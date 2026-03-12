# Guiding Principles

This document records the ideas-alma of MolSysViewer.

It is not a roadmap, and it is not a checkpoint.

Its purpose is to collect the development principles that should guide:

- prioritization,
- API design,
- interaction design,
- documentation,
- and scientific use.

These principles should be stable enough to guide future work, but they can
grow over time as the identity of the project becomes clearer.

## 1. Exploratory Science Must Become Reproducible State

Scientific work has an interactive and exploratory phase, and molecular viewers
are essential there.

But scientific results must remain reproducible.

For MolSysViewer, this means exploratory interaction is not the end goal by
itself. Its meaningful outcomes should tend to become explicit viewer state
that can be:

- represented from Python,
- replayed,
- rebuilt,
- exported,
- shared,
- and reasoned about later.

Examples of such state include:

- active selections when they become named or persisted,
- regions,
- layers,
- annotations and labels,
- measurements,
- camera and scene state,
- and derived scene artifacts created from interaction.

This principle affects prioritization:

- prefer interaction that can become reproducible state,
- prefer explicit artifacts over ephemeral UI-only behavior,
- evaluate new features by asking how they will be captured and replayed.

## Working Rule

When a new interactive feature is proposed, ask:

- what scientific decision or artifact does this produce,
- how is it represented in Python,
- how does it survive replay/rebuild/export,
- and how can a user reproduce it later without repeating the original manual interaction.

If those questions cannot be answered, the feature is not mature yet.
