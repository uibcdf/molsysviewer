# Contributing (quick start)

You typically contribute via a fork.
If you have write access, you can use branches in the main repo instead.

## Clone

```bash
git clone https://github.com/uibcdf/molsysviewer.git
cd molsysviewer
```

If you use the GitHub CLI:

```bash
gh repo clone uibcdf/molsysviewer
cd molsysviewer
```

## Install the dev environment

Follow {doc}`../dev_setup`.

## Run a quick sanity check

```bash
pytest
```

If you touch TypeScript:

```bash
cd molsysviewer/js
npm run test:js
```
