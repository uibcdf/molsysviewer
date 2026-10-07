# Contributing

You contribute through GitHub pull requests.
You prefer small, reviewable diffs.

## Basic workflow

1. Create a fork (or a branch if you have write access).
2. Create a feature branch.
3. Make focused changes.
4. Run the relevant tests locally.
5. Open a pull request and describe what changed and why.

## What to include in a PR

- A clear description of the user-facing impact.
- The minimal tests or manual checks that validate your change.
- Documentation updates when you change public behavior.

## What to avoid

- Editing generated artifacts (`molsysviewer/viewer.js`, `molsysviewer/viewer.js.map`).
- Committing large notebook widget states (use HTML lite exports and the notebook strip workflow).
- Mixing unrelated refactors with functional changes.

## Issues

If you find a bug or you want to request a feature, use the GitHub issues board.
Link issues from PRs when possible.

