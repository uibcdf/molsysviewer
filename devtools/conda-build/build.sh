#!/usr/bin/env bash
set -ex

# 1) Build JS bundle (viewer.js) into molsysviewer/
pushd molsysviewer/js
# Conda build sets PKG_VERSION; use it if RELEASE_VERSION is unset.
if [ -z "${RELEASE_VERSION:-}" ] && [ -n "${PKG_VERSION:-}" ]; then
  export RELEASE_VERSION="${PKG_VERSION}"
fi
# If you have a package-lock, prefer `npm ci`; otherwise fall back to `npm install`.
npm ci || npm install
npm run build
popd

# Sanity check: runtime resources must exist for packaging
if [ ! -f "molsysviewer/viewer.js" ]; then
  echo "ERROR: molsysviewer/viewer.js was not generated. JS build failed or output path changed." >&2
  exit 1
fi
if [ ! -f "molsysviewer/runtime_actions.json" ]; then
  echo "ERROR: molsysviewer/runtime_actions.json is missing." >&2
  exit 1
fi

# 2) Install Python package with build requirements supplied by the host env.
$PYTHON -m pip install . --no-deps --no-build-isolation --ignore-installed -vv
