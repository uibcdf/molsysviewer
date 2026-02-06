import pytest

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.smonitor import CATALOG, PACKAGE_ROOT, META
from smonitor.integrations import emit_from_catalog


def test_smonitor_catalog_emit():
    event = emit_from_catalog(
        CATALOG["viewer_init_failed"],
        package_root=PACKAGE_ROOT,
        meta=META,
        extra={"reason": "test", "message": "failed"},
    )
    assert event.get("code") == "MOLSYSVIEWER-VIEWER-INIT-FAILED"


def test_argument_error_message():
    exc = ArgumentError("selection", value="bad", caller="molsysviewer.test")
    assert str(exc)
