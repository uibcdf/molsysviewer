# String and quotation style

Use a strict quote policy.
It keeps diffs consistent and it aligns with the existing codebase.

## Policy

- Use double quotes (`"`) for string literals in Python and TypeScript.
- Use triple double quotes (`"""`) for docstrings.
- Only deviate when the alternative meaningfully improves readability (for example: fewer escapes).

## Why this is safe

- Python is formatted with Black.
- TypeScript sources already use double quotes in `molsysviewer/js/src/`.
