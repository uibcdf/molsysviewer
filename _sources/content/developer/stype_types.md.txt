# 🧩 String and Quotation Style

To ensure consistency across all UIBCDF libraries and agents, follow these conventions for quotation marks and string formatting.

## Quotation Marks

- Use **single quotes (`'`)** for strings by default.

  ```python
  shape_type = 'concavity'
  filename = 'surface_data.json'
  ```

- Use **double quotes (`"`)** only when the string itself contains an apostrophe:

  ```python
  msg = "It's a shared boundary between two cavities."
  ```

- Use **triple double quotes (`"""`)** for **docstrings**, both for modules and functions:

  ```python
  def add_feature(feature):
      """Add a new feature to the current topography."""
  ```

- When embedding JSON or other data formats that require double quotes by specification, preserve their native quoting style:

  ```python
  json_str = '{"pocket": 42, "volume": 128.5}'
  ```

## Docstrings and Text Formatting

- Always use **PEP 257-compliant** docstrings (`"""Triple double quotes"""`).
- Write the first line as a concise summary, followed by a blank line, then a more detailed description if needed.

  ```python
  def connect_features(child, parent):
      """Connect a child feature to its parent feature.

      This function registers a bidirectional relationship between features
      of different dimensionalities (e.g., Mouth–Pocket).
      """
  ```

## Formatting Tools

- All repositories are formatted automatically with **Black** using:

  ```toml
  [tool.black]
  line-length = 88
  skip-string-normalization = false
  ```

- This configuration enforces **single quotes** by default and ensures consistent formatting across the ecosystem.

- Contributors should run:

  ```bash
  black .
  isort .
  flake8
  ```

  before submitting any pull request.
