# pyside6-addons-uibcdf

Local experimental scaffold for the third UIBCDF Qt-for-Python family member.

Current target:

- Linux
- Python 3.13
- version family: `6.9.2`

Source of truth:

- validated `pip` environment:
  `/home/diego/Myopt/miniconda3/envs/molsyssuite-qt-spike`
- manifests:
  `../../manifests/pyside6_addons.files.txt`
  `../../manifests/pyside6_addons.runtime.txt`

Current reading:

- this is the package that carries the standalone-critical layer:
  - `QtPositioning`
  - `QtWebChannel`
  - `QtWebEngine*`
  - `QtWebEngineProcess`
  - WebEngine QML/resources/translations
