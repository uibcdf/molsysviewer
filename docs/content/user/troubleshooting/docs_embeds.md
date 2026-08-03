(User_Troubleshooting_DocsEmbeds)=
# HTML embeds in docs

## Iframe stays blank

HTML lite views (`view.export.html(..., shared_runtime=...)`) are embedded as iframes
in Sphinx docs. If the iframe is blank:

**1. Serve the docs — don't open `index.html` directly.**

Chrome blocks iframes loaded from `file://` URLs. Always serve with a local
server:

```bash
cd docs/_build/html
python -m http.server 8000
# then open http://localhost:8000
```

**2. Check the CDN URL in the generated file.**

Open `_static/views/your_file.html` and look for the `<script src="...">` line.
The URL should match the installed version of MolSysViewer. If it points to an
old version, regenerate the file with the current install:

```python
view.export.html("docs/_static/views/figure.html", shared_runtime="docs/_static")
```

**3. Check for Content Security Policy errors.**

In the browser console, look for `Refused to load script` CSP violations.
If your Sphinx theme enforces a strict CSP, you may need to allow the CDN
domain in `conf.py`:

```python
# conf.py
html_csp = "script-src 'self' cdn.jsdelivr.net;"
```

## Iframe height/width

The default iframe embed is 400 × 400 px. Override in the RST/MyST source:

```{raw} html
<iframe src="../../../_static/views/figure.html"
        width="100%" height="600px" frameborder="0">
</iframe>
```

## Static views out of date

After changing the scene and re-exporting, the browser may serve a cached
version. Hard-refresh with `Ctrl+Shift+R` or clear the browser cache.
