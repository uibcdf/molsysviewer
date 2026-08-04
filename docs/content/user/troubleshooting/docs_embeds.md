(User_Troubleshooting_DocsEmbeds)=
# HTML embeds in docs

The mechanism itself is documented in
{doc}`../export/sphinx_html_embedding`. This page is for when it does not work.

## The iframe is blank

**1. Are you opening the built site from disk?**

That is the common one, and it is not a broken export. A view that shares a
runtime (`view.export.html(..., shared_runtime="docs/_static")`) has to load
`viewer.js` from beside it, and a browser refuses to let a page opened from a
disk load a file next to it: the page has no origin. The console says

```
Access to script at 'file:///…/viewer.js' from origin 'null' has been blocked by CORS policy
```

Serve the build instead:

```bash
python -m molsysviewer.tools.preview docs/_build/html
```

A published site is served, so it never has this problem. If you want a file that
opens with a double click, export it without `shared_runtime`: it carries the
runtime inside and needs nobody.

**2. Is the runtime where the page looks for it?**

Open the view's HTML and read the `molsysviewer-runtime-candidates` block near
the bottom. It lists what the page will try, in order, relative to itself. Check
that the first one resolves from the page's location in the **built** site, not
in your sources. In the preview server's log, a missing runtime shows up as a
`404` on `viewer.js`, which is the quickest answer there is.

If you are exporting from a script, `msv.tools.embed_iframe(view, path=page)`
computes the relative path for you, which is the step that usually goes wrong.

**3. Content Security Policy.**

If your theme enforces a strict CSP, a runtime beside your views needs
`script-src 'self'`. Only if you exported with `shared_runtime="cdn"` do you also
need to allow `cdn.jsdelivr.net`.

## The view renders but is out of date

The browser caches `viewer.js` and the view aggressively. Hard-refresh with
`Ctrl+Shift+R`.

If the scene changed and the page did not, remember that exported views are build
artifacts: regenerate them with the script that produced them (in this project,
`docs/generate_static_views/`) rather than editing the HTML.

## Changing the size of an embed

The defaults are `100%` wide and `480px` tall. Both are arguments:

```python
msv.tools.embed_iframe("docs/_static/views/figure.html",
                       path="docs/content/my_page.md",
                       width="100%", height="640px")
```

Or write the markup yourself:

```{raw} html
<iframe src="../../../_static/views/figure.html"
        width="100%" height="640px" style="border:none;"></iframe>
```
