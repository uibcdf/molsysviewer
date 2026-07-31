# Standalone Qt — CI headless & software-GL decisions

Decisiones cerradas el 2026-07-04 tras validar el render del standalone Qt en una
GPU real (aleph). **No re-litigar** sin un motivo nuevo.

## Gate: render en GPU real (aleph, 2026-07-04)

Se lanzó el standalone en aleph (GPU + pantalla) y **renderiza**: dialanine en 3D,
zoom/rotación con ratón, context menu nativo funcionando. Conclusión:

> El build de la familia Qt-for-Python y del standalone **está bien**. Toda la
> dificultad que tuvimos en headless era **exclusivamente software-GL** (falta de
> un contexto WebGL sin GPU), no un fallo de código ni de empaquetado.

## Decisión 1 — Estrategia CI headless (dos niveles)

No condicionar el **CI verde** a resolver el WebGL headless.

- **Nivel 1 — transporte + lógica (sin GL):** bloqueante, siempre. Ya implementado:
  `tests/test_standalone.py::test_qt_event_transport_smoke_real_qt` valida el canal
  real Qt (`fetch → molsysviewer:// handler → bridge`) en subproceso, offscreen,
  **sin GPU ni display**. Corre en cualquier CI.
- **Nivel 2 — render (necesita GL):** **job aparte, no-bloqueante, en un runner con
  GPU** (el self-hosted organizacional de UIBCDF). Como el render funciona en GPU,
  ahí va directo, sin trucos de software-GL. Arnés: `test_qt_live_model_full_render_gpu`
  (opt-in con `MOLSYSVIEWER_QT_GPU_TEST=1`).
- **Plan C** (si no hubiera GPU-runner): Mesa llvmpipe del SO + xvfb — pero resultó
  frágil y no arrancó limpio en el env conda, así que no es la vía preferida.

## Decisión 2 — Fallback software-GL de producto: DIFERIDO

Para usuarios que instalen el standalone en máquinas **sin GPU**:

- SwiftShader/ANGLE **no está** en el PySide6 upstream ni en el build de
  `qt6-webengine-uibcdf`; bundlearlo es trabajo real (traerlo de fuera y cablearlo).
- El Mesa llvmpipe del sistema como fallback headless es frágil.
- **Decisión:** el standalone **requiere un GL/GPU funcional**; documentarlo como
  requisito. **Diferir** el empaquetado de SwiftShader hasta que aparezca una
  necesidad real de usuario sin GPU. No bloquea 1.0.

## Decisión 3 — Investigación SwiftShader: CONCLUIDA

No se necesita ahora. Usuarios con GPU funcionan out-of-the-box; el caso headless
es un asunto de CI, resuelto con el GPU-runner (Decisión 1, Nivel 2).

## Estado de la familia Qt (contexto)

Los 5 paquetes (`shiboken6`, `pyside6-essentials`, `pyside6-addons`,
`qt6-positioning`, `qt6-webengine` `-uibcdf`) están **publicados en el canal
`uibcdf`**, así que el standalone se instala/prueba sin compilar. El backend
interactivo está validado en Qt real (ver
`pending_proposals/standalone_qt_interactive_backend.md`).

## Evidencia adicional sobre el Plan C (2026-07-31)

Se volvió a intentar el Plan C en el env conda, con Mesa llvmpipe del sistema
(`swrast_dri.so` presente) bajo `xvfb-run`. Resultado, que **confirma la
Decisión 1 en lugar de discutirla**:

- `test_qt_live_model_full_render_gpu` **pasó** lanzado en solitario con
  `QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu-sandbox --no-sandbox
  --ignore-gpu-blocklist --enable-unsafe-swiftshader"`, `LIBGL_ALWAYS_SOFTWARE=1`
  y `GALLIUM_DRIVER=llvmpipe`.
- El **mismo test falló** dentro de la suite completa y sin ese último flag, con
  `Error: Could not create a WebGL rendering context`.

Es decir, se reprodujo la fragilidad ya documentada: el contexto WebGL software
depende de la combinación exacta de flags y del orden de ejecución. Un paso
aislado no es una refutación.

No se cambia nada: el Plan C sigue siendo la vía no preferida, y el camino es el
runner con GPU (Nivel 2). Se registra por si alguien vuelve a intentarlo, para
que no repita el experimento desde cero.

Nota menor para quien lo intente: el docstring de
`test_qt_live_model_full_render_gpu` recomienda `--use-gl=angle
--use-angle=swiftshader`, pero **SwiftShader no está** en el build de
`PySide6_uibcdf` (comprobado), de modo que esos flags no aplican aquí.
