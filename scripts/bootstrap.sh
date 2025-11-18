#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="molsysviewer@uibcdf_3.12"
MICROMAMBA_BIN="$HOME/.local/bin/micromamba"
export PATH="$HOME/.local/bin:$PATH"

install_micromamba() {
    echo "micromamba no encontrado; instalando en $MICROMAMBA_BIN ..."
    local tmpdir
    tmpdir="$(mktemp -d)"
    trap 'rm -rf "$tmpdir"' RETURN
    mkdir -p "$(dirname "$MICROMAMBA_BIN")"
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest -o "$tmpdir/micromamba.tar.bz2"
    tar -xjf "$tmpdir/micromamba.tar.bz2" -C "$tmpdir"
    install -m 755 "$tmpdir/bin/micromamba" "$MICROMAMBA_BIN"
}

cd "$REPO_ROOT"

if ! command -v micromamba >/dev/null 2>&1; then
    install_micromamba
fi

MAMBA_CMD="micromamba"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/.micromamba}"
mkdir -p "$MAMBA_ROOT_PREFIX"

# Create or update the environment from environment.yml
if ! "$MAMBA_CMD" env list | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
    "$MAMBA_CMD" env create -f environment.yml -y
else
    "$MAMBA_CMD" env update -f environment.yml --prune -y
fi

# Activate the environment and prepare Python.
eval "$($MAMBA_CMD shell hook -s bash)"
"$MAMBA_CMD" activate "$ENV_NAME"
pip install --upgrade pip
pip install -e .

# Install JS dependencies and build the widget bundle.
pushd molsysviewer/js >/dev/null
npm install
npm run build
popd >/dev/null

echo "MolSysViewer listo para usarse."
