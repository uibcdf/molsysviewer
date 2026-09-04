from __future__ import annotations

import asyncio
import json
import sys

from molsysviewer.demo import demo
from molsysviewer.remote import RemoteSessionService, RenderWorkerConfig
from molsysviewer.viewer import MolSysView


async def main() -> None:
    source_view = demo["pentalanine"]
    service = RemoteSessionService(
        RenderWorkerConfig(startup_timeout=30, shutdown_timeout=5)
    )
    view = MolSysView(transport=service.channel)
    try:
        view.load(source_view.molsys, skip_digestion=True)
        client_url = await service.start()
        diagnostics = await service.launch_worker()
        await service.worker_host.wait_for_structure(timeout=30)
        print(
            "MSV_REMOTE_SESSION="
            + json.dumps(
                {
                    "client_url": client_url,
                    "renderer": diagnostics.renderer,
                    "webgl2": diagnostics.webgl2,
                    "software_rendering": diagnostics.software_rendering,
                }
            ),
            flush=True,
        )
        while True:
            command = (await asyncio.to_thread(sys.stdin.readline)).strip()
            if command == "stop" or not command:
                break
            if command == "kill-worker":
                process = service.worker_host.worker._process  # noqa: SLF001
                if process is None:
                    raise RuntimeError("E2E render worker has no managed process")
                previous_pid = process.pid
                process.terminate()
                await process.wait()
                await asyncio.wait_for(
                    _wait_until(
                        lambda: service.worker_recovery_count == 1
                        or service.worker_recovery_state == "failed"
                    ),
                    timeout=45,
                )
                if service.worker_recovery_state == "failed":
                    raise RuntimeError(
                        "render-worker recovery failed: "
                        + json.dumps(
                            {
                                "service_failure": service.failure,
                                "host_failure": service.worker_host.failure,
                                "worker_failure": service.worker_host.worker.failure,
                                "worker_state": service.worker_host.worker.state,
                                "worker_connected": service.worker_host.worker_connected.is_set(),
                                "stderr_tail": service.worker_host.worker.stderr_tail,
                            }
                        )
                    )
                await service.worker_host.wait_for_structure(timeout=30)
                recovered = service.worker_host.worker.diagnostics
                print(
                    "MSV_REMOTE_WORKER_RECOVERED="
                    + json.dumps(
                        {
                            "previous_pid": previous_pid,
                            "pid": recovered.pid if recovered is not None else None,
                            "state": service.worker_recovery_state,
                        }
                    ),
                    flush=True,
                )
                continue
            raise ValueError(f"unknown E2E bridge command: {command}")
        peer_diagnostics = await service.worker_host.worker.peer_diagnostics()
        for event in (
            service.video_connected,
            service.input_channel_open,
            service.worker_input_received,
        ):
            try:
                await asyncio.wait_for(event.wait(), timeout=5)
            except TimeoutError:
                pass
        print(
            "MSV_REMOTE_RESULT="
            + json.dumps(
                {
                    "video_connected": service.video_connected.is_set(),
                    "input_channel_open": service.input_channel_open.is_set(),
                    "worker_input_received": service.worker_input_received.is_set(),
                    "whole_visible": view.whole.visible,
                    "whole_representation": view.whole.representation,
                    "trajectory_frame": view.current_structure_index,
                    "n_atoms": int(view._molsys.get_n_atoms()) if view._molsys is not None else 0,
                    "label": view._last_label,
                    "active_selection_count": len(view.active_selection.atom_indices),
                    "context_kind": (view.get_last_context_event() or {}).get("kind"),
                    "context_action": (view._last_context_action_event or {}).get("action"),  # noqa: SLF001
                    "service_failure": service.failure,
                    "worker_host_failure": service.worker_host.failure,
                    "worker_recovery_count": service.worker_recovery_count,
                    "worker_recovery_state": service.worker_recovery_state,
                    "worker_peer_diagnostics": peer_diagnostics,
                }
            ),
            flush=True,
        )
    finally:
        await service.close()
        view.close()
        source_view.close()


async def _wait_until(predicate) -> None:
    while not predicate():
        await asyncio.sleep(0.05)


asyncio.run(main())
