# Qt For Python UIBCDF Experiment

This scratch area supports the first experimental packaging pass for the
provisional standalone Qt family.

Current working hypothesis:

- the clean provisional route is better modeled as an aligned Qt-for-Python
  family than as a small extension on top of `qt6-main`
- the relevant family boundary is:
  - `shiboken6`
  - `PySide6_Essentials`
  - `PySide6_Addons`

What this scratch area is for:

- derive reproducible file manifests from a validated `pip` environment
- separate the three package boundaries before attempting conda recipes
- keep the first packaging work isolated from the main project packaging

Suggested first workflow:

1. Use the validated environment as the source of truth:
   - `/home/diego/Myopt/miniconda3/envs/molsyssuite-qt-spike`
2. Run:
   - `python sandbox/qt_for_python_uibcdf_experiment/inventory_qt_family.py --python-bin /home/diego/Myopt/miniconda3/envs/molsyssuite-qt-spike/bin/python --output-dir sandbox/qt_for_python_uibcdf_experiment/manifests`
3. Review the generated manifests for:
   - ownership
   - overlap
   - runtime shape
4. Use those manifests as the starting point for the first experimental conda
   recipes.

This is not the final packaging path.
It is only the first staging area for the family-level experiment.
