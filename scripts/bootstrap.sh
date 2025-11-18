#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

# 1. Crear o actualizar el entorno Conda/Mamba desde environment.yml
if ! conda env list | grep -q 'molsysviewer@uibcdf_3\.12'; then
    conda env create -f environment.yml
else
    conda env update -f environment.yml --prune
fi

# 2. Activar el entorno y preparar Python.
eval "$(conda shell.bash hook)"
conda activate molsysviewer@uibcdf_3.12
pip install --upgrade pip
pip install -e .

# 3. Instalar dependencias JS y construir el bundle del widget.
pushd molsysviewer/js >/dev/null
npm install
npm run build
popd >/dev/null

echo "MolSysViewer listo para usarse."
