# User presets

User presets let you define reusable styling rules for `whole` and `regions`.

Use user presets when you want a named “style recipe” you can reuse across notebooks.

## How it works

1. You define presets in a JSON or YAML file.
2. You load them with `molsysviewer.config.load_user_presets(...)`.
3. You apply them with `preset="your-preset-name"` in `whole` or `regions`.

## File format (conceptual)

Each preset name maps to:

- `base`: an optional built-in preset to start from (for example `auto`).
- `options`: optional preset-level options.
- `rules`: a list of rules that apply representations to selections or explicit atom indices.

This page is a placeholder for the full schema and examples.

## Loading

```python
import molsysviewer as mv

mv.config.load_user_presets("presets.yaml")
```

## Applying

```python
view.whole.set_representation(preset="my-style")
```
