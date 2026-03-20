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
