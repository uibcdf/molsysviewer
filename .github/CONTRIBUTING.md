# Contributing to MolSysViewer

We welcome contributions! Please follow these guidelines:

## Getting started
- Fork the repository and clone your fork locally.
- Create a feature branch (avoid working directly on `main`).
- Set up the dev environment (conda + Node) per `README_DEVELOPERS.md`.

## Making changes
- Keep changes scoped and focused; prefer small PRs.
- If you touch TypeScript, do **not** edit `molsysviewer/viewer.js` directly; rebuild from `molsysviewer/js/src/` only when needed.
- Add or update tests for new features (Python unit tests; JS/TS logic tests where applicable).
- Update documentation (docs pages, docstrings) when user-facing behavior changes.

## Before opening a PR
- Run the test suite (`pytest`); include MolSysMT if your changes depend on it.
- Optionally run lint/format (`ruff`, `black`) if configured in your env.
- For docs demos, use static exports (`write_html`) instead of executing widgets in CI.

## Opening a PR
- Use a clear title/description explaining the change and impact.
- Check the “Ready to go” box when the PR is ready for review.
- Address review feedback; keep commits clean (no unrelated changes).

## Resources
- [GitHub documentation](https://help.github.com/)
- [PR best practices](http://codeinthehole.com/writing/pull-requests-and-other-good-practices-for-teams-using-github/)
* [A guide to contributing to software packages](http://www.contribution-guide.org)
* [Thinkful PR example](http://www.thinkful.com/learn/github-pull-request-tutorial/#Time-to-Submit-Your-First-PR)
