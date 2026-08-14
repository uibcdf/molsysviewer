---
name: Bug report
about: Something behaves incorrectly, raises where it should not, or contradicts the documentation
title: ""
labels: bug, needs-triage
assignees: ""
---

<!--
Three questions. Answer what you can — a partial report we can reproduce is worth more
than a complete one we cannot. Paste output rather than describing it.

A view is drawn by a browser, so two extra things help a great deal: whether you are in
Jupyter, in an exported page, or in the Qt window; and anything the browser console said.
-->

**What** — What goes wrong, in a sentence.


**How** — The shortest snippet that shows it, and the traceback if there is one.

```python
import molsysviewer as msv
...
```

```
paste the error here
```

**Why** — Which call or workflow this blocks, and what you did instead.


**Where** — Jupyter / exported HTML page / Qt standalone, and the browser if it is one of
the first two. Paste anything from the browser console if you can reach it.


<!--
Versions, if you have them to hand:

python -c "import molsysviewer, molsysmt; print(molsysviewer.__version__, molsysmt.__version__)"
-->
