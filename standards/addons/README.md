# Add-on Standards

This directory is the stable reference point for teams implementing MolSysViewer
add-ons.

Use it when you need the most normative version of the contract, separate from
the more explanatory docs and cookbook pages.

Read in this order:

1. [`IMPLEMENTATION_CONTRACT.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/IMPLEMENTATION_CONTRACT.md)
2. [`docs/content/developer/addons.md`](/home/diego/repos@uibcdf/molsysviewer/docs/content/developer/addons.md)
3. [`docs/content/user/cookbook/addon_development.md`](/home/diego/repos@uibcdf/molsysviewer/docs/content/user/cookbook/addon_development.md)
4. [`minimal_topomt.py`](/home/diego/repos@uibcdf/molsysviewer/molsysviewer/addon_templates/minimal_topomt.py)

The bundled `minimal_topomt.py` template should now be read as a small but
credible workspace-shaped reference add-on, not as a bare one-panel toy.

Bundled references can also be activated through:

- `molsysviewer.addon_templates.list_reference_addons()`
- `molsysviewer.addon_templates.register_reference_addon(...)`
- `molsysviewer.addon_templates.build_reference_demo_view(...)`

The last helper should now be treated as the canonical bundled smoke path for
external teams evaluating the add-on contract.

What belongs here:

- stable vocabulary
- packaging rules
- registration/discovery contract
- lifecycle contract
- workspace guidance
- first-milestone expectations for downstream teams

What does not belong here:

- long historical explanation
- speculative UI designs
- release notes

Those should stay in `devguide/` or in the public docs.
