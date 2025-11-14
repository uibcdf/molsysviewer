# molsysviewer/messaging.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SupportsSend(Protocol):
    """Minimal protocol for objects that can send custom messages (ipywidgets)."""

    def send(self, content: dict[str, Any]) -> None:
        ...


# Opcodes: names for frontend operations
LOAD_PDB_STRING = "LOAD_PDB_STRING"
SET_REPRESENTATION_BASIC = "SET_REPRESENTATION_BASIC"
RESET_CAMERA = "RESET_CAMERA"
SET_FRAME = "SET_FRAME"

DRAW_TEST_SPHERE = "DRAW_TEST_SPHERE"

# Más adelante:
# SET_CAVITY_POINTCLOUD = "SET_CAVITY_POINTCLOUD"
# SET_CAVITY_MESH = "SET_CAVITY_MESH"
# SET_DYNAMIC_LINES = "SET_DYNAMIC_LINES"
# ...


@dataclass
class Command:
    """Simple container for commands MolSysViewer -> frontend."""

    op: str
    payload: dict[str, Any]


def send_command(widget: SupportsSend, command: Command) -> None:
    """Send a structured command to the frontend.

    Parameters
    ----------
    widget:
        Any object with a `.send()` method (e.g. a DOMWidget).
    command:
        Command to be sent, with `op` and `payload`.
    """
    widget.send({"op": command.op, "payload": command.payload})

