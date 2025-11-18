#!/usr/bin/env bash
set -ex

# 1) Build JS bundle (viewer.js) into molsysviewer/
pushd js
# Si usas package-lock, mejor npm ci; si no, npm install
npm ci || npm install
npm run build
popd

# 2) Install Python package (which now includes viewer.js as package-data)
$PYTHON -m pip install . --no-deps --ignore-installed -vv
