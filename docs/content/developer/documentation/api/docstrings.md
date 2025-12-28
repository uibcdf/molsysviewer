# Docstrings

This page defines how you write docstrings for MolSysViewer.
Docstrings are part of the public API.
They must match real behavior.

## Style

- Use English.
- Use NumPy docstring style.
- Keep the first line as a short summary.
- Prefer short sentences.
- Use Sphinx roles for cross-links when useful (`{class}`, `{func}`, `{meth}`).

## What needs a docstring

You document every public object:

- Public functions.
- Public classes.
- Public methods and properties.
- Public modules with non-trivial behavior.

If a method is private (`_name`) you can keep the docstring minimal.

## Functions and methods

Recommended sections:

- `Parameters`
- `Returns` (or `Yields`)
- `Raises` (if it can fail in user-facing ways)
- `Notes` (only if you need to explain semantics)
- `Examples` (when it helps)

Example (minimal)

```python
def reset_viewer(self) -> None:
    """Reset the viewer to a clean state.

    This clears regions, layers, shapes, and the currently loaded structure from the frontend.

    Returns
    -------
    None

    Examples
    --------
    >>> from molsysviewer import demo
    >>> view = demo.dialanine
    >>> view.reset_viewer()  # doctest: +SKIP
    """
```

Use `# doctest: +SKIP` for widget-driven examples.
Keep non-skipped doctests free of frontend dependencies.

## Classes

For classes, you document:

- What the class represents.
- The main invariants (what stays true after initialization).
- The important parameters.
- Key attributes (if users are expected to read them).

If a class is user-facing, include a short usage snippet.

## Modules

If a module defines a user-visible API surface, add a module docstring that explains:

- What the module is responsible for.
- Which objects it exports.
- Any important conventions or invariants.

## Keep docstrings testable

If you add an `Examples` section, keep it runnable.
See {doc}`doctests` for how doctests are executed.
