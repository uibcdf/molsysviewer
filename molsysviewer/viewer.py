from __future__ import annotations

from typing import Any
from collections.abc import Sequence

from .widget import MolSysViewerWidget


class MolSysView:
    """Widget de visualización basado en Mol* para sistemas de MolSysMT."""

    def __init__(self) -> None:
        self.widget = MolSysViewerWidget()

        self.widget.layout.width = "100%"
        self.widget.layout.height = "480px"  # o "600px" si lo prefieres
        self.widget.layout.min_height = "400px"

        self._ready = False
        self._pending_messages: list[dict] = []

        # Registrar callback para mensajes JS->Python
        def _handle_msg(widget, content, buffers):  # type: ignore[override]
            event = content.get("event")
            if event == "ready":
                self._ready = True
                # En cuanto el frontend esté listo, reenviamos todo
                for msg in self._pending_messages:
                    self.widget.send(msg)
                self._pending_messages.clear()

        self.widget.on_msg(_handle_msg)

    # --- util interno ---

    def _send(self, msg: dict) -> None:
        """Enviar un mensaje al frontend o encolarlo si aún no está listo."""
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

    # --- Mostrar el widget ---

    def show(self):
        """Mostrar el widget en el notebook."""
        return self.widget

    # --- Tests de vida / demos ---

    def show_test_pdb_id(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        self._send({"op": "test_pdb_id"})

    def add_sphere(
        self,
        center=(0.0, 0.0, 0.0),
        radius: float = 10.0,
        color: int = 0x00FF00,
        alpha: float = 0.4,
    ) -> None:
        """Añade una esfera (posiblemente transparente) a la escena."""
        self._send(
            {
                "op": "add_sphere",
                "options": {
                    "center": list(center),
                    "radius": float(radius),
                    "color": int(color),
                    "alpha": float(alpha),
                },
            }
        )

    def add_spheres(
        self,
        centers: Sequence[Sequence[float]],
        radius: float | Sequence[float] = 1.0,
        color: int | Sequence[int] = 0x00FF00,
        alpha: float | Sequence[float] = 0.4,
    ) -> None:
        """Añade muchas esferas a la escena.

        Parámetros
        ----------
        centers
            Secuencia de centros, cada uno (x, y, z).
        radius
            Radio (escalar para todas) o lista de radios (uno por esfera).
        color
            Color en 0xRRGGBB (escalar o lista).
        alpha
            Transparencia (0.0-1.0), escalar o lista.
        """
        # Normalizamos centers a lista de listas
        centers_list = [list(c) for c in centers]
        n = len(centers_list)

        if n == 0:
            return

        # Helpers para “broadcasting” simple de escalares a listas
        def _as_list(value, n, cast):
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if len(value) != n:
                    raise ValueError(
                        f"Esperaba {n} valores pero recibí {len(value)}."
                    )
                return [cast(v) for v in value]
            else:
                return [cast(value)] * n

        radii = _as_list(radius, n, float)
        colors = _as_list(color, n, int)
        alphas = _as_list(alpha, n, float)

        for c, r, col, a in zip(centers_list, radii, colors, alphas):
            self.add_sphere(center=c, radius=r, color=col, alpha=a)

    def show_test_sphere_transparent(
        self,
        center=(0.0, 0.0, 0.0),
        radius=10.0,
        color=0x00ff00,
        alpha=0.4,
    ):
        """Función de test que delega en add_sphere (se mantiene por compatibilidad)."""
        # La comprobación extra de widget es opcional, pero no molesta
        if self.widget is None:
            raise RuntimeError("MolSysViewerWidget no inicializado; llama antes a show()")

        self.add_sphere(center=center, radius=radius, color=color, alpha=alpha)

    # --- Carga desde strings ---

    def load_pdb_string(self, pdb_string: str, *, label: str | None = None) -> None:
        """Cargar una estructura PDB desde un string en el viewer."""
        self._send(
            {
                "op": "load_structure_from_string",
                "format": "pdb",
                "data": pdb_string,
                "label": label,
            },
        )

    def load_mmcif_string(self, mmcif_string: str, *, label: str | None = None) -> None:
        """Cargar una estructura mmCIF desde un string en el viewer."""
        self._send(
            {
                "op": "load_structure_from_string",
                "format": "mmcif",
                "data": mmcif_string,
                "label": label,
            },
        )

    # --- Carga desde URL ---

    def load_from_url(
        self,
        url: str,
        *,
        format: str | None = None,
        label: str | None = None,
    ) -> None:
        """Cargar una estructura remota desde una URL."""
        self._send(
            {
                "op": "load_structure_from_url",
                "url": url,
                "format": format,
                "label": label,
            },
        )

    # --- Gestión de escena ---

    def clear(self) -> None:
        """Limpiar la escena."""
        self._send({"op": "clear"})

    # --- Integración con MolSysMT (modo texto) ---

    def load_from_molsysmt(
        self,
        item: Any,
        *,
        selection: str | None = "all",
        structure_indices: str | None = "all",
        target_format: str = "string:pdb_text",
        label: str | None = None,
    ) -> None:
        """Cargar en el viewer un objeto de MolSysMT."""
        try:
            import molsysmt as msm
        except ImportError as exc:
            msg = "MolSysView.load_from_molsysmt requiere molsysmt instalado."
            raise ImportError(msg) from exc

        lower_target = target_format.lower()
        if lower_target != "string:pdb_text":
            msg = (
                "Por ahora, MolSysView.load_from_molsysmt sólo soporta "
                "target_format='string:pdb_text'."
            )
            raise ValueError(msg)

        # Pequeña optimización: si el item ya es string:pdb_text
        try:
            form = msm.get_form(item)
        except Exception:
            form = None

        if (
            form is not None
            and selection == "all"
            and structure_indices == "all"
            and form.lower() == lower_target
        ):
            data = item
        else:
            data = msm.convert(
                item,
                to_form=target_format,
                selection=selection,
                structure_indices=structure_indices,
            )

        self.load_pdb_string(str(data), label=label)
