# Developer guide

How MolSysViewer works under the hood and how to contribute.

````{grid} 2 2 2 2
:::{grid-item-card} Getting started
:link: intro/index.md
:columns: 6
Fork, environment setup, devcontainer, quick dev loop.
:::

:::{grid-item-card} Architecture
:link: architecture.md
:columns: 6
Layers, message flow Python→JS, Mol* plugin, shapes and tags.
:::

:::{grid-item-card} Concepts
:link: concepts.md
:columns: 6
Big-picture view: roles of Python, AnyWidget, Mol*, WebGL, and why MolSysViewer exists.
:::

:::{grid-item-card} Testing & QA
:link: testing.md
:columns: 6
Recommended test patterns and what to cover.
:::

:::{grid-item-card} Documentation
:link: docs.md
:columns: 6
How to extend these docs; style and build guidance.
:::

:::{grid-item-card} Coding style
:link: style.md
:columns: 6
Lint/format conventions, docstrings, and code patterns.
:::
````

```{toctree}
:hidden:
:maxdepth: 2

intro/index.md
architecture.md
concepts.md
testing.md
docs.md
style.md
```
