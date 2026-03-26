# UIBCDF Qt Family Repo Plan

This plan translates the current standalone packaging conclusion into a local
three-repo experiment structure.

Scope for the first pass only:

- platform: Linux
- Python: 3.13

Target family:

1. `shiboken6-uibcdf`
2. `pyside6-essentials-uibcdf`
3. `pyside6-addons-uibcdf`

Why this order:

- `PySide6_Essentials` depends on `shiboken6`
- `PySide6_Addons` depends on both `shiboken6` and `PySide6_Essentials`
- the first practical packaging pressure therefore appears in that same order

First success criteria:

1. `shiboken6-uibcdf`
   - builds a package boundary that matches the validated wheel family
   - exposes `Shiboken.abi3.so`
   - exposes `libshiboken6.abi3.so.6.9`

2. `pyside6-essentials-uibcdf`
   - packages the Essentials runtime tree from the validated family
   - exposes `libpyside6.abi3.so.6.9`
   - exposes the Qt base runtime under `PySide6/Qt`

3. `pyside6-addons-uibcdf`
   - packages the Addons runtime tree from the validated family
   - exposes `QtWebEngineWidgets`
   - exposes `QtWebEngineProcess`, WebEngine QML/resources/translations

Packaging approach for the first pass:

- start from the validated wheel-family manifests already generated in
  `sandbox/qt_for_python_uibcdf_experiment/manifests`
- keep the experiment separate from the main `molsysviewer` package recipe
- treat this as a boundary-finding pass, not a polished release recipe
