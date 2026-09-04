from __future__ import annotations

import asyncio
import json
import sys

from molsysviewer.demo import demo
from molsysviewer.remote import RemoteSessionService
from molsysviewer.viewer import MolSysView


async def main() -> None:
    source_view = demo["pentalanine"]
    service = RemoteSessionService(render_on="client")
    view = MolSysView(transport=service.channel)
    try:
        view.load(source_view.molsys, skip_digestion=True)
        client_url = await service.start()
        print("MSV_CLIENT_RENDER_SESSION=" + json.dumps({"client_url": client_url}), flush=True)
        while True:
            command = (await asyncio.to_thread(sys.stdin.readline)).strip()
            if command == "stop" or not command:
                break
            if command == "camera":
                for _ in range(20):
                    if view._last_camera_snapshot is not None:  # noqa: SLF001
                        break
                    await asyncio.sleep(0.05)
                print(
                    "MSV_CLIENT_RENDER_CAMERA="
                    + json.dumps(view._last_camera_snapshot),  # noqa: SLF001
                    flush=True,
                )
                continue
            if command == "selection-count":
                print(
                    "MSV_CLIENT_RENDER_SELECTION="
                    + json.dumps({"count": len(view.active_selection.atom_indices)}),
                    flush=True,
                )
                continue
            if command == "state":
                print(
                    "MSV_CLIENT_RENDER_STATE="
                    + json.dumps(
                        {
                            "n_atoms": int(view._molsys.get_n_atoms()),  # noqa: SLF001
                            "selection_count": len(view.active_selection.atom_indices),
                            "trajectory_frame": view.current_structure_index,
                            "whole_representation": view.whole.representation,
                        }
                    ),
                    flush=True,
                )
                continue
            raise ValueError(f"unknown E2E bridge command: {command}")
        try:
            await asyncio.wait_for(service.client_structure_complete.wait(), timeout=30)
        except TimeoutError:
            pass
        print(
            "MSV_CLIENT_RENDER_RESULT="
            + json.dumps(
                {
                    "ready": service.client_render_ready.is_set(),
                    "structure_complete": service.client_structure_complete.is_set(),
                    "n_atoms": int(view._molsys.get_n_atoms()),  # noqa: SLF001
                    "registrations": service.client_registration_count,
                    "whole_representation": view.whole.representation,
                    "active_selection_count": len(view.active_selection.atom_indices),
                    "trajectory_frame": view.current_structure_index,
                    "service_failure": service.failure,
                }
            ),
            flush=True,
        )
    finally:
        await service.close()
        view.close()
        source_view.close()


asyncio.run(main())
