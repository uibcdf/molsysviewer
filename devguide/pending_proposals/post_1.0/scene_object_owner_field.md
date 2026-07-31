# An `owner` field on scene objects

**Status:** post-1.0. Deferred on purpose, recorded so it stays a choice.

**Origin:** `scene_contracts.md` §0.12, which decided the behaviour and deferred
the field in the same breath.

## The situation

Add-ons do not have a private channel. They create shapes by calling the public
API — ElastNetMT does exactly this:

```python
layer = view.shapes.add_displacement_vectors(...)   # adapters/modes.py
layer = view.shapes.add_links(...)                  # adapters/contacts.py
```

So an add-on's shape lands in `_scene_objects` like any other, appears in
`shapes.info()`, and shows up in the Shapes panel **with a trash button next to
it**.

**That was decided to be correct and it stays.** It is the user's scene; a viewer
that displays an object it refuses to let you remove is worse than one that lets
you delete something an add-on made. The add-on's obligation is to tolerate it:
the handle it kept goes `_active = False`, and it must check rather than assume.

## What is missing

There is no `owner` field in the model, so a shape produced by ElastNetMT is
**indistinguishable** from one the user drew by hand. The panel cannot say
`· from elastnetmt`, and the user has no way to tell which objects will
reappear if the add-on re-runs and which are theirs.

## Why it was deferred

It is new public API surface, and the block that surfaced it already carried
enough. That reasoning still holds; this is not urgent.

## What it would take

- an `owner` on the scene-object record, set at creation from the calling add-on
  when there is one, `None` otherwise;
- the field in the authoritative summary (Contract S1) so the panel can render it
  without a second projection;
- serialisation (Contract S5), or an explicit decision that ownership is a
  session-scoped annotation and does not survive a reload — either is defensible,
  but it must be *decided*, because an owner that silently disappears on import
  is worse than no owner at all;
- a row affordance that is informative, not a second permission system. Ownership
  labels what made an object; it does not restrict what the user may do to it.

## Related, and deliberately not the same thing

Transient regions (`focus`, `orientation`, `plane`) are already filtered from the
panel and from `export_state` by `_TRANSIENT_REGION_TAG`, and Contract V's
*owned primitives* — shapes a measurement creates for its own realisation — must
be filtered the same way. Both are about objects the user did not create and
should not manage directly.

`owner` is different: an add-on's shape **is** the user's to manage. Do not
implement `owner` by generalising the transient mechanism; they answer opposite
questions.
