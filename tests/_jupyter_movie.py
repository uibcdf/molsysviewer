"""Actual-kernel fixture for Studio Movie; no frontend or scientific substitutes."""

import hashlib
from pathlib import Path


def notebook_cells(output, expected):
    native_sha = hashlib.sha256(Path(expected["molsysmt._rust"]).read_bytes()).hexdigest()
    return [
        f"""from pathlib import Path
import asyncio, faulthandler, hashlib, importlib, json, sys, zipfile
import numpy as np
import molsysviewer as msv
import molsysmt as msm
from IPython.display import display
_output = Path({str(output / "notebooks")!r})
_thread_trace = open({str(output / "kernel-threads.log")!r}, 'w')
Path(_thread_trace.name).chmod(0o600)
faulthandler.dump_traceback_later(20, repeat=True, file=_thread_trace)
_expected = {expected!r}
_origins = {{name: str(Path(importlib.import_module(name).__file__).resolve()) for name in _expected}}
assert _origins == {{name: str(Path(path).resolve()) for name, path in _expected.items()}}, _origins
_native_sha = hashlib.sha256(Path(_origins['molsysmt._rust']).read_bytes()).hexdigest()
assert _native_sha == {native_sha!r}
Path({str(output / "kernel-origin.json")!r}).write_text(json.dumps({{'python': sys.version, 'executable': sys.executable, 'modules': _origins, 'native_sha256': _native_sha}}, indent=2))
with msv.demo['pentalanine'] as seed:
    view = seed.extract(structure_indices=[0, 8, 3])
view.whole.set_representation('ball-and-stick', color='blue')
view.regions.add(atom_indices=[0, 1], tag='site', representation='ball-and-stick', color='orange')
view.measurements.add_distance([0], [5], tag='capture-distance')
view.annotations.add('Movie control', atom_indices=[0], tag='capture-label')
_source = view.molsys
_coordinates = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit='angstrom').copy()
def movie_status():
    assert view.molsys is _source
    np.testing.assert_array_equal(msv.pyunitwizard.get_value(view.get_coordinates(), to_unit='angstrom'), _coordinates)
    def job_state(job):
        if job is None:
            return None
        return {{'action': job.action, 'result_done': job.result.done(), 'task_done': job.task.done() if job.task else None, 'stack': [{{'function': frame.f_code.co_name, 'line': frame.f_lineno}} for frame in job.task.get_stack()] if job.task else []}}
    playback = view.movie._playback
    return {{'recipe': view.movie.to_dict(), 'frame': view.player.index, 'pending': len(view._frontend_requests._pending), 'job': view.movie._studio.job is not None, 'source_unchanged': True,
        'jobs': [job_state(view.movie._studio.job), job_state(view.movie._studio.pause_job)],
        'playback': {{'pause_requested': playback.pause_requested, 'done': playback.done.done(), 'request': playback.request.request_id if playback.request else None}} if playback else None,
        'requests': [{{'id': item.request_id, 'endpoint': item.endpoint_id, 'done': item.future.done()}} for item in view._frontend_requests._pending.values()]}}
display(view)
"""
    ]
