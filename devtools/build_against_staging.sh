#!/usr/bin/env bash
# Build and verify the conda package against MolSysMT's staging channel.
#
# Step 3 of the release coordination agreed on 2026-09-02: before either package is
# promoted to the main channel, ours is built and tested against their staged artefacts.
# Written as a script rather than as instructions because the window is a scheduled event
# with both teams waiting, and a command recalled from prose is a command typed wrong.
#
#   ./devtools/build_against_staging.sh [output-dir]
#
# What it proves, which is the list MolSysMT asked the candidate to demonstrate from the
# noarch artefact itself:
#
#   1. `import molsysviewer`                     -- the recipe's test section
#   2. `import molsysviewer.runtime_contract`    -- idem
#   3. runtime_actions.json and viewer.js present inside the artefact
#   4. resolution on Python 3.11, 3.12 and 3.13
#   5. the solved environment honours molsysmt>=0.22.0
#
# 1, 2, 3 and 5 run inside `conda build`; 4 is the dry-run loop at the end, and is the one
# that shows a single noarch artefact serving all three interpreters.
set -euo pipefail

OUT="${1:-$(mktemp -d)}"
STAGING="uibcdf/label/staging"
RECIPE="$(dirname "$0")/conda-build"

echo "==> building against ${STAGING}, output in ${OUT}"
conda build "${RECIPE}" \
  --output-folder "${OUT}" \
  -c "${STAGING}" -c uibcdf -c conda-forge \
  --no-anaconda-upload

echo
echo "==> resolving the built artefact on each supported interpreter"
failed=0
for py in 3.11 3.12 3.13; do
  if out=$(conda create --dry-run -n _msv_staging_check \
             -c "file://${OUT}" -c "${STAGING}" -c uibcdf -c conda-forge \
             "python=${py}" molsysviewer 2>&1); then
    msv=$(echo "${out}" | grep -oE "molsysviewer +[^ ]+::molsysviewer-[^ ]+" | head -1 | awk '{print $NF}')
    msm=$(echo "${out}" | grep -oE "molsysmt +[^ ]+::molsysmt-[^ ]+"       | head -1 | awk '{print $NF}')
    printf "  python %-5s ok\n    %s\n    %s\n" "${py}" "${msv:-?}" "${msm:-?}"
  else
    printf "  python %-5s FAILED\n%s\n" "${py}" "$(echo "${out}" | tail -20)"
    failed=1
  fi
done

echo
if [ "${failed}" -eq 0 ]; then
  echo "==> all three interpreters resolve against staging"
else
  echo "==> at least one interpreter did not resolve; do not promote" >&2
  exit 1
fi
