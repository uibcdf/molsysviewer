from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError


def digest_runtime_assets_dir(runtime_assets_dir, caller=None):

    # Optional: when absent the exported page keeps the runtime beside itself.
    if runtime_assets_dir is None:
        return None

    if isinstance(runtime_assets_dir, Path):
        return str(runtime_assets_dir)
    if isinstance(runtime_assets_dir, str) and runtime_assets_dir:
        return runtime_assets_dir

    raise ArgumentError(
        'runtime_assets_dir', value=runtime_assets_dir, caller=caller, message=None
    )
