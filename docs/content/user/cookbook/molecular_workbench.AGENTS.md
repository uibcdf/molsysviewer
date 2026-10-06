# Molecular workbench tutorial contract

Preserve the five stages: progressive loading, region visibility and enablement,
batch loading, three-structure interaction calculation, and session recovery.
Use bundled 1VII protein, caffeine and pentalanine sources. Keep coordinates
unchanged during composition, distinguish calculation from display filtering,
and explain the permissive 4 Å Buch cutoff. Use canonical view variable names
and the explicit interaction query vocabulary.

Keep session and analyses-only H5MSM examples within a TemporaryDirectory,
including declared same-axis import. Generate web previews through
`docs/generate_static_views/molecular_workbench.py`, using the shared local
runtime and transparent backgrounds. Never generate HTML during notebook
execution. The notebook's executable outputs and the human review record supply
distinct evidence; executing the tutorial does not certify manual UI checks.
