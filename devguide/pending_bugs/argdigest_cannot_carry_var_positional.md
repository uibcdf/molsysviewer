# `@digest` breaks a `*args` function, and one of ours is decorated

**Found:** 2026-08-12, while executing gate 9. **Upstream:**
[`../../../argdigest/devguide/pending_bugs/var_positional_arguments_are_lost.md`](../../../argdigest/devguide/pending_bugs/var_positional_arguments_are_lost.md).

## The defect here

`molsysviewer/shapes/pharmacophore.py:add_pharmacophore_features` carries `@digest()` and
takes `*args`. ArgDigest invokes the wrapped function by keyword only
(`fn_to_wrap(**bound)`), so a positional call raises:

```python
view.shapes.add_pharmacophore_features(centers=…, kinds=…, tag="a")   # works
view.shapes.add_pharmacophore_features(some_positional, kinds=…)      # TypeError:
                                                                      # too many positional arguments
```

It is public and appears in `docs/content/showcase/pharmacophore.ipynb` — with keywords,
which is why nothing has failed. The only test that calls it passes keywords **and**
`skip_digestion=True`, bypassing digestion entirely, so the decoration it was meant to
exercise was never exercised.

The function is a deprecated alias for `add_interaction_sites`.

## Why it is recorded rather than fixed

Three fixes exist and the cheapest is not obviously the right one:

1. **Remove `@digest()` from it.** One line, restores positional calls immediately.
   It also removes the only case that keeps this visible, and the alias is deprecated —
   so it fixes the symptom on a function scheduled to disappear.
2. **Give it a closed signature.** It forwards to `add_interaction_sites`, which has one;
   writing the parameters out makes the decoration meaningful instead of merely legal. It
   is also a signature change on a deprecated alias.
3. **Wait for ArgDigest.** The upstream fix is small — rebuild the call from
   `BoundArguments` rather than flattening to keywords — and closes the whole class,
   including the three region boolean methods that cannot be decorated today.

Option 3 is preferred and the others stay available if it does not land before 1.0.

## What holds the line meanwhile

- `tests/test_public_api_inventory.py::test_no_decorated_callable_takes_var_positional`
  fails if any *other* `*args` function acquires `@digest`. This one is the single
  recorded exception.
- `Region.difference`, `Region.intersection` and `Region.union` are recorded in
  `DELIBERATELY_NOT_DIGESTED` with this as the reason. They were decorated during gate 9
  and reverted when their tests failed — which is the outcome the pharmacophore alias did
  not get, because nothing there checks its operands.

## The general rule this produced

**A decoration that cannot be exercised is not a contract.** The pharmacophore test passed
for months while asserting nothing about digestion, because `skip_digestion=True` turned
the decorator off. When a test needs that flag, it is testing the body, not the seam.
