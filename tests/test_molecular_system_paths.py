"""Path inputs stay valid across platforms before trusted MolSysMT delegation."""

from pathlib import Path

import molsysmt as msm
from molsysviewer._private.argdigest.argument.molecular_system import (
    digest_molecular_system,
)
from molsysviewer._private.argdigest.argument.output_filename import (
    digest_output_filename,
)


def test_bundled_bcif_path_is_normalized_before_trusted_delegation():
    path = msm.systems["T4 lysozyme L99A"]["181l.bcif.gz"]
    assert isinstance(path, Path)

    result = digest_molecular_system(path, caller="molsysviewer.new_view.new_view")

    assert result == str(path.absolute())


def test_path_collections_preserve_container_shape_without_mutating_input():
    path = msm.systems["alanine dipeptide"]["alanine_dipeptide.h5msm"]
    original = [path]

    as_list = digest_molecular_system(original, caller="molsysviewer.new_view.new_view")
    as_tuple = digest_molecular_system((path,), caller="molsysviewer.new_view.new_view")

    assert as_list == [str(path.absolute())]
    assert as_tuple == (str(path.absolute()),)
    assert original == [path]


def test_export_filename_accepts_the_native_platform_path(tmp_path):
    path = tmp_path / "scene.html"
    assert digest_output_filename(path, caller="molsysviewer.exports.html") == str(path.absolute())
