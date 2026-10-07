# Citation and Zenodo releases

MolSysViewer uses GitHub Releases and Zenodo's native GitHub integration to
preserve citable source snapshots. A Git tag by itself is not sufficient.

The stable concept DOI is
[`10.5281/zenodo.18072956`](https://doi.org/10.5281/zenodo.18072956). Cite it for
MolSysViewer generally. Cite the distinct version DOI shown by Zenodo when you
need to identify the exact release used in a reproducible workflow.

Before tagging a release, synchronize and validate the citation metadata:

```bash
python devtools/prepare_release.py X.Y.Z
python devtools/validate_citation.py --expected-version X.Y.Z
```

The same commands accept the project's `X.Y.Z-rc.N` prerelease form.

After publishing the GitHub Release, wait for Zenodo ingestion and verify it:

```bash
python devtools/verify_zenodo_release.py X.Y.Z
```

The full metadata authority, automation, and recovery contract is maintained in
[`devguide/release_and_citation.md`](https://github.com/uibcdf/molsysviewer/blob/main/devguide/release_and_citation.md).
The package, Conda, and npm sequence is described in
{doc}`releasing`.
