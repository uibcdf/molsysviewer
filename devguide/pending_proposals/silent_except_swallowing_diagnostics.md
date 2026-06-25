# Propuesta de Mejora: Reducir el "Tragado" Silencioso de Excepciones en Puntos de Estado

## 1. Contexto y Diagnóstico

Un barrido del paquete encuentra **~198 manejadores `except` que silencian el error**
(`except Exception:` seguido de `pass` / `continue` / `return None` / `return []`), repartidos
por `colors.py`, `regions.py`, `measurements.py`, `selections.py`, `layers.py`, `addons.py`,
`player.py`, `shapes/__init__.py`, `viewer/index_mapper.py`, `viewer/visibility.py`,
`viewer/panel_mode.py`, `viewer/interaction.py`, `standalone_qt/utils.py`, etc.

Muchos son **defensivos legítimos** (parseo tolerante de color, atributos opcionales de features
de TopoMT, lectura de configuración de disco). El problema no es que existan, sino su **densidad
en puntos donde el resultado del `except` cambia el estado** del visor sin dejar rastro:

- `IndexMapper` devuelve `[]` o cae a identidad ante cualquier excepción (ver
  [[index_mapper_silent_drop_and_identity_fallback]]).
- `regions.py` (~líneas 63, 95) y `measurements.py` (~líneas 101, 258, 301) descartan valores o
  devuelven vacío ante errores de conversión.
- `viewer/visibility.py`, `viewer/panel_mode.py`, `viewer/interaction.py` hacen `pass` en
  handlers que afectan a lo que el usuario ve.

En estos puntos, un error real (datos corruptos, API de MolSysMT que cambió, índice fuera de
rango por desincronización) queda **indistinguible del caso normal "no había nada que hacer"**:
no hay log, no hay señal, no hay traza. El síntoma aparece tarde y lejos de la causa.

Este hueco es **distinto** del que describe [[silent_exception_desync]]: aquella propuesta trata
las excepciones de Python que **no se propagan al frontend**; esta trata las excepciones que se
**capturan y se descartan internamente** sin dejar diagnóstico. Son complementarias.

## 2. Impacto

- **Depuración costosa**: cuando algo va mal en producción (notebook del científico), no hay
  ninguna pista de qué `except` se activó ni por qué.
- **Bugs latentes**: un cambio de contrato en una librería hermana (MolSysMT, PyUnitWizard) que
  empiece a lanzar donde antes no lo hacía pasaría completamente desapercibido.

## 3. Propuesta de Solución

No se trata de eliminar los `except` defensivos, sino de hacerlos **observables** y **precisos**:

1. **Estrechar el tipo capturado** donde se conozca: sustituir `except Exception` por los tipos
   esperados (`ValueError`, `TypeError`, `KeyError`, `AttributeError`) de modo que lo inesperado
   se propague en vez de tragarse.
2. **Instrumentar los `except` en puntos de estado** con una señal de diagnóstico vía
   `smonitor` (a nivel `debug`/`warning`), incluyendo el contexto (qué se intentaba, con qué
   entrada). Priorizar: `index_mapper`, `visibility`, `regions`, `measurements`, el rebuild.
3. **Auditoría guiada**: clasificar los ~198 sitios en tres categorías —
   (a) defensivo aceptable (parseo de color, atributos opcionales) → dejar, opcionalmente con
   comentario `# defensive: <motivo>`;
   (b) punto de estado → instrumentar con smonitor;
   (c) tipo demasiado amplio → estrechar.

No requiere un cambio masivo de una vez; puede abordarse por módulo, empezando por los de la
categoría (b).

## 4. Criterios de Aceptación

1. Los `except` en `index_mapper`, `visibility`, `regions`, `measurements` y el rebuild emiten
   una señal de diagnóstico cuando se activan, en lugar de descartar el error en silencio.
2. Ningún `except Exception` permanece en esos puntos de estado salvo que esté justificado con
   comentario explícito.
3. Existe (al menos) un test que verifica que un fallo inyectado en uno de esos puntos produce
   una señal de smonitor observable, no un descarte silencioso.

## 5. Relación

- Complementaria a [[silent_exception_desync]] (propagación al frontend) y a
  [[index_mapper_silent_drop_and_identity_fallback]] (caso concreto más grave de este patrón).
