#!/usr/bin/env bash
set -e

ENV_NAME="molsysviewer_dev"
ENV_FILE="devtools/conda_envs/development_env.yaml"

if command -v mamba &>/dev/null; then
  CMD="mamba"
  echo "Using mamba to manage environments."
else
  CMD="conda"
  echo "Using conda to manage environments."
fi

echo "Updating environment '${ENV_NAME}' from '${ENV_FILE}'..."
$CMD env update -f "${ENV_FILE}" --prune

echo
echo "Environment '${ENV_NAME}' is ready."
echo "To activate it, run:"
echo "  conda activate ${ENV_NAME}"
echo
echo "Then you can start JupyterLab with:"
echo "  jupyter lab"
