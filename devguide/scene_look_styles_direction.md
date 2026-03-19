# Scene Look Styles Direction

This page defines the next careful step after the first implemented
scene-style slice.

The goal is to clarify what future visual styles such as `default-look` and
`illustrative` should mean before any new runtime layer is introduced.

## Why This Needs A Separate Step

MolSysViewer now has a real first public `Style` object and a working
`view.styles` manager.

That current slice is healthy because it is:

- reproducible
- Python-first
- backed by the existing representation/preset pathway
- conceptually narrow

The next temptation would be to add more built-in names quickly.

That would be a mistake if those names silently mix two different concerns:

- the structural scene recipe
- the visual appearance of that scene

So this step is about defining the second concern carefully.

## The Distinction To Preserve

MolSysViewer should keep the same distinction Mol* makes, but express it in its
own product language:

- scene recipe
  - what baseline structural representations are built
- scene look
  - how that baseline visually appears

Current built-in scene styles such as:

- `polymer-cartoon`
- `polymer-and-ligand`
- `atomic-detail`

are really recipe-oriented names.

Future names such as:

- `default-look`
- `illustrative`

should be look-oriented names.

## Design Vocabulary vs Public API Vocabulary

At the design level, it is useful to reason with several distinct concepts:

- `preset`
- `style`
- `look`
- `focus style`

These four concepts help separate different responsibilities cleanly:

- `preset`
  - structural baseline machinery
- `style`
  - semantic reusable recipe
- `look`
  - scene-wide visual appearance
- `focus style`
  - local emphasis treatment

But this does **not** mean MolSysViewer must expose four independent public
categories forever.

Current working hypothesis:

- keep the richer vocabulary in `devguide` while the model is being designed
- let the public API converge later toward the smallest comfortable surface
- prefer a user mental model centered on `Style`

So if experience confirms it, the future public API may compact some of these
concepts inside `Style` instead of presenting them as peers.

For example:

- `look` may become one dimension of a richer `Style`
- `focus style` may become a specialized style mode or layer rather than a
  fully separate top-level API family

## Summary Table

| Concept | Main question | Typical responsibility | Current status |
| --- | --- | --- | --- |
| `preset` | What structural baseline is built? | Engine-level representation recipe | Real and public |
| `style` | What reusable scene intention do I want? | Public semantic recipe for scene setup | Real and public |
| `look` | How should that scene visually appear? | Global visual appearance layer | Design concept, future runtime slice |
| `focus style` | How should a specific target be emphasized? | Local emphasis treatment composed with structural targeting | Design concept, future |

Working rule:

- this table is a design aid, not a commitment to four permanent public API families
- the likely public direction is still to keep `Style` as the main user-facing concept

## What `default-look` Should Mean

`default-look` should become the neutral visual appearance layer.

Its intent should be:

- readable
- non-distracting
- scientifically trustworthy
- suitable as the baseline for routine work

It should not imply:

- a different target
- a different structural preset
- a strong communication-oriented stylization

So `default-look` is not "another preset".
It is the visual baseline that sits on top of a scene recipe.

## What `illustrative` Should Mean

`illustrative` should become a communication-oriented visual look.

Its intent should be:

- stronger figure readability
- clearer separation of shape layers
- more presentation/publication-friendly rendering

It may later involve things such as:

- stronger outlines
- softened clutter
- different lighting/material emphasis
- clearer separation between focus and context

It should not mean:

- arbitrary artistic rendering
- a replacement for explicit structural targeting
- a hidden bundle of unexplained structural changes

## Design Rule

When these looks arrive, the healthy mental model should be:

- scene recipe answers "what structural baseline is shown?"
- scene look answers "how does that baseline look?"

So a future scene could conceptually be described as:

- recipe: `polymer-and-ligand`
- look: `illustrative`

not as one opaque mega-preset.

## What Not To Do Yet

Do not rush to implement a second runtime state family just to expose these
names.

Before implementation, the project should answer:

- where look state lives in Python
- how it is serialized and replayed
- whether it is global-only in the first slice
- how it composes with current scene recipes
- whether docs-lite and export pathways preserve it cleanly

## Recommended First Implementation Slice For Looks

When the project is ready, the first look slice should be:

- scene-level only
- global-only
- exclusive
- explicit in Python
- replay/export safe

That means:

- no region-specific looks yet
- no focus looks yet
- no canvas authoring yet
- no ad hoc parameter soup exposed to the user

## Candidate Public Shape

The exact API does not need to be finalized now, but the direction should be
something explicit and composable.

Healthy shapes might later look like:

```python
view.styles.apply(tag="polymer-and-ligand")
view.styles.set_look("illustrative")
```

or:

```python
view.styles.apply(
    scene="polymer-and-ligand",
    look="illustrative",
)
```

The key invariant is more important than the exact spelling:

- recipe and look should remain distinguishable

The same principle applies even if the public API becomes more compact:

- distinct responsibilities may live inside one `Style` model
- but they should not collapse into conceptual ambiguity

## Relationship With MolSysMT

This page does not change the targeting rule already established elsewhere.

- MolSysMT defines structural targets
- MolSysViewer defines visual treatment

Scene looks are purely on the MolSysViewer side.
They must not become a vehicle for hidden structural selection logic.

## Recommendation

The next healthy work is not to implement `default-look` or `illustrative`
immediately.

It is to keep them documented as explicit future targets while the current
scene-style slice is hardened and used in practice.
