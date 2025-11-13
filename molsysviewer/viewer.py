# molsysviewer/viewer.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from IPython.display import display

from .widget import MolSysViewerWidget
from .messaging import (
    Command,
    LOAD_PDB_STRING,
    RESET_CAMERA,
    SET_FRAME,
    SET_REPRESENTATION_BASIC,
    send_command,
)


@dataclass
class MolSysViewer:
    """High-level viewer API for MolSysViewer.

    This is what end-users will mostly interact with in notebooks.
    """

    widget: MolSysViewerWidget

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_pdb_string(cls, pdb: str) -> "MolSysViewer":
        """Create a viewer from a PDB string."""
        widget = MolSysViewerWidget()
        viewer = cls(widget=widget)
        viewer.load_pdb_string(pdb)
        return viewer

    # Más adelante:
    # @classmethod
    # def from_molysmt(cls, system: Any) -> "MolSysViewer":
    #     ...
    #
    # @classmethod
    # def from_file(cls, filename: str) -> "MolSysViewer":
    #     ...

    # ------------------------------------------------------------------
    # Notebook display
    # ------------------------------------------------------------------
    def show(self) -> MolSysViewerWidget:
        """Display the widget in a Jupyter notebook."""
        display(self.widget)
        return self.widget

    # ------------------------------------------------------------------
    # Basic operations
    # ------------------------------------------------------------------
    def load_pdb_string(self, pdb: str) -> None:
        """Send a command to load a PDB string in the frontend."""
        send_command(self.widget, Command(LOAD_PDB_STRING, {"pdb": pdb}))

    def set_basic_representation(self, repr_type: str = "cartoon") -> None:
        """Set a basic representation (cartoon, sticks, surface...) in the frontend."""
        send_command(
            self.widget,
            Command(SET_REPRESENTATION_BASIC, {"type": repr_type}),
        )

    def reset_camera(self) -> None:
        """Reset the camera in the frontend."""
        send_command(self.widget, Command(RESET_CAMERA, {}))

    # ------------------------------------------------------------------
    # Trajectory frame control (future use)
    # ------------------------------------------------------------------
    def set_frame(self, index: int) -> None:
        """Set current trajectory frame."""
        self.widget.frame = index
        send_command(self.widget, Command(SET_FRAME, {"index": index}))

