# Type annotations (Python ≥3.10)

We follow modern type hinting conventions:

- All code assumes **Python 3.10 or newer**.
- Do **not** include `from __future__ import annotations`.
- Write type hints **without quotes**, unless referencing a class not yet defined
  (forward reference).
  ```python
  def ensure_path_exists(path: Path, description: str) -> None:  # ✅ correct
  ```
  ```python
  def connect(self, other: "Feature") -> None:  # ✅ forward reference
  ```
- Use `typing` types in their modern form (`list[int]`, `dict[str, Any]`, etc.),
  not legacy imports (`List`, `Dict`).
- Avoid unnecessary abstraction layers like `TypeAlias` or `Protocol` unless you
  really need structural typing.
- Prefer explicit, concrete types for clarity and readability.

---

**Example:**

```python
from pathlib import Path

def ensure_path_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"The {description} '{path}' does not exist.")
    if not path.is_file():
        raise ValueError(f"The {description} '{path}' is not a file.")
```
