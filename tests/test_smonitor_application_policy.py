"""Qualify provider registration without replacing an application's diagnostics.

SMonitor 0.19.0 separates registration from policy (uibcdf/molsyssuite#106).
Older supported versions retain their behavior; these receiving checks do not
raise MolSysViewer's dependency floor or select a new default capture policy.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import smonitor.integrations

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not callable(getattr(smonitor.integrations, "register_provider", None)),
    reason="Application-policy preservation requires SMonitor 0.19.0 provider registration",
)
@pytest.mark.parametrize("first_provider", ["molsysviewer", "molsysmt", "argdigest"])
@pytest.mark.parametrize("enabled", [False, True])
def test_cold_imports_and_reload_preserve_application_policy(tmp_path, first_provider, enabled):
    # A subprocess is necessary: pytest's conftest has already imported both
    # molecular libraries and cannot exercise first-use registration.
    code = """
import importlib
import logging
import sys
import warnings

source_root, first_provider, enabled = sys.argv[1:]
if source_root:
    sys.path.insert(0, source_root)

import smonitor

enabled = enabled == 'True'
smonitor.configure(
    profile='debug' if enabled else 'agent',
    level='ERROR',
    enabled=enabled,
    capture_logging=False,
    capture_warnings=False,
    capture_exceptions=False,
    args_summary=False,
    trace_depth=1,
    profiling=False,
)
manager = smonitor.get_manager()
fields = ('profile', 'level', 'enabled', 'capture_logging', 'capture_warnings',
          'capture_exceptions', 'args_summary', 'trace_depth', 'profiling')

def policy():
    return {field: getattr(manager.config, field) for field in fields}

expected = policy()
warning_handler = warnings.showwarning
logging_handlers = tuple(logging.getLogger().handlers)
for provider in (first_provider, 'molsysviewer', 'molsysmt', 'argdigest'):
    importlib.import_module(provider)
    assert policy() == expected, (provider, expected, policy())
    assert warnings.showwarning is warning_handler, provider
    assert tuple(logging.getLogger().handlers) == logging_handlers, provider

import molsysviewer
importlib.reload(molsysviewer)
assert policy() == expected, (expected, policy())
assert warnings.showwarning is warning_handler
assert tuple(logging.getLogger().handlers) == logging_handlers

# Resolve without emitting: a disabled manager deliberately emits no event.
# The explicit rendering audience must not replace the application's profile.
message, _hint = smonitor.resolve(code='MOLSYSVIEWER-VIEWER-INIT-FAILED', profile='user',
                                  extra={'reason': 'policy-probe', 'message': 'registration-probe'})
assert 'policy-probe' in message and 'registration-probe' in message, message
assert policy() == expected, (expected, policy())
"""
    source_root = "" if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") == "1" else str(ROOT)
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, source_root, first_provider, str(enabled)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
