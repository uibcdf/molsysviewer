# Propuesta de Mejora: Formalizar el Contrato del Paquete `viewer/` (Estado de Mixins y Resolución de Caller)

## 1. Contexto y Diagnóstico

`MolSysView` (`molsysviewer/viewer/core.py`) se compone de **11 mixins**:

```python
class MolSysView(
    SceneRegistryMixin, HistoryMixin, ExportMixin, RegionsMixin, PanelModeMixin,
    LoadMixin, VisibilityMixin, SceneMixin, MolSysMTInterfaceMixin, StateMixin,
    InteractionMixin,
):
```

Esta división nació para gestionar el tamaño del núcleo (core.py ~1850 líneas, ~75 KB). La
descomposición es defendible, pero introduce **dos deudas de mantenibilidad** que conviene
saldar antes de 1.0, porque la superficie de `MolSysView` es estable y cada mixin nuevo
amplifica el problema.

### Deuda 1: Los mixins comparten estado sin contrato tipado

Cada mixin es una clase plana (`class XxxMixin:`) **sin clase base común ni `Protocol`**. Sin
embargo, todos acceden a un estado compartido amplio que **solo** se inicializa en
`MolSysView.__init__` o se define en mixins hermanos. Atributos/métodos compartidos observados
(muestra real, ~33 distintos): `self._regions`, `self._layers`, `self._scene_objects`,
`self._selections`, `self._molsys`, `self._index_mapper`, `self._message_history`,
`self._shape_history`, `self._annotation_history`, `self._measurement_history`,
`self._selection_history`, `self._send`, `self._send_replay`,
`self._rebuild_view_from_current_molsys`, `self._update_visibility_in_frontend`,
`self._split_into_regions`, los contadores `_region_counter` / `_layer_counter` / etc.

Consecuencias:

- **Cero verificación estática.** Un nombre de atributo mal escrito (o renombrado en un solo
  sitio) no se detecta hasta runtime. Este es exactamente el modo de fallo del bug registrado
  en el checkpoint "twenty-first batch": `this.addonRuntimeSummary` (campo inexistente) hacía
  caer el panel; el equivalente Python es igual de invisible para el linter y el type checker.
- **Dependencias implícitas entre mixins.** `RegionsMixin` asume que existe
  `self._rebuild_view_from_current_molsys` (definido en core), `SceneMixin` asume `self._send`
  (de `HistoryMixin`), etc. El orden de mixins en la herencia importa pero no está documentado
  ni protegido.
- **Onboarding costoso.** Para saber de dónde sale un `self._algo` hay que buscar a mano entre
  12 archivos.

### Deuda 2: Doble contabilidad en la resolución del "caller" de ArgDigest

El decorador `@digest()` valida argumentos resolviendo el **nombre cualificado** del método a
partir de su `__module__`, y la whitelist de digestión indexa los métodos públicos como
`molsysviewer.viewer.core.MolSysView.<método>`. Como los métodos están físicamente repartidos
entre archivos de mixin (`molsysviewer.viewer.regions`, `...scene`, etc.), el repo usa **dos
mecanismos compensatorios independientes para el mismo problema del split de paquete**:

1. **Falseo de `__name__`**: 8 módulos de mixin declaran al inicio
   `__name__ = "molsysviewer.viewer.core"` para que sus funciones reporten el módulo "correcto".
   (`interaction.py`, `regions.py`, `load.py`, `state.py`, `panel_mode.py`, `visibility.py`,
   `scene.py`, `molsysmt_interface.py`.)
2. **Cirugía de strings**: `normalize_viewer_caller()` en
   `molsysviewer/_private/arg_digestion/helpers.py:14` reescribe
   `molsysviewer.viewer.core.` → `molsysviewer.viewer.` "para mantener estables las rutas
   históricas del viewer tras el split del paquete".

Problemas:

- **Frágil y silencioso.** Si alguien añade un mixin nuevo y **olvida** la línea `__name__`, sus
  métodos se indexan bajo el módulo equivocado y la búsqueda en la whitelist falla; según el
  caso, la validación se salta o lanza `ArgumentError` espurio. No hay test que lo proteja.
- **Olor de diseño.** Falsear `__name__` a nivel de módulo afecta a *todo* lo que dependa del
  nombre del módulo (logging, tracebacks, `pickle`, `inspect`), no solo a la digestión.
- **Redundancia.** Dos mecanismos para lo mismo: si uno cambia y el otro no, se desincronizan.

## 2. Por qué importa

El núcleo del producto (regiones, capas, escena, carga, rebuild) vive aquí. Esta es la parte
del código que **más cambia** y la que más addons y mixins futuros van a tocar. Un contrato
implícito sin verificación estática es precisamente el tipo de fragilidad que el mantra advierte
("cada nueva capa debe justificarse; cada nueva pieza debe encajar limpiamente").

## 3. Propuestas de Solución

### Para la Deuda 1 (contrato de estado)

**Opción A (recomendada, no invasiva): un `Protocol` de estado compartido.**

Definir `molsysviewer/viewer/_protocol.py` con un `class _ViewerState(Protocol)` que declare la
superficie compartida (atributos + firmas de métodos cross-mixin). Cada mixin anota
`self: _ViewerState` (o hereda de un stub bajo `TYPE_CHECKING`). Beneficios: mypy/pyright
detectan typos y dependencias rotas **sin cambiar el runtime** ni la jerarquía de herencia.

**Opción B (más estructural): extraer el estado a un dataclass.**

Mover el estado compartido a un objeto `ViewerState` que `MolSysView` componga (`self.state`),
en lugar de docenas de atributos sueltos en `self`. Más limpio a largo plazo, pero es un
refactor amplio que toca los 11 mixins; probablemente post-1.0.

Recomendación: **A antes de 1.0** (barato, alto retorno en seguridad); considerar B como
dirección post-1.0 si el número de mixins sigue creciendo.

### Para la Deuda 2 (resolución de caller)

1. **Unificar en un solo mecanismo.** Preferir `normalize_viewer_caller` (ya centralizado y
   testeable) y **eliminar el falseo de `__name__`** de los 8 módulos. Para ello, la resolución
   del caller en `@digest()` debe basarse en el `__qualname__`/clase real
   (`molsysviewer.viewer.core.MolSysView`) y no en el `__module__` del archivo físico del mixin.
2. **Test de protección.** Añadir un test que recorra todos los métodos públicos decorados con
   `@digest()` de `MolSysView` y verifique que su caller resuelto coincide con la entrada de
   whitelist esperada. Así, olvidar el registro de un método nuevo falla en CI, no en runtime
   del usuario.

## 4. Criterios de Aceptación

1. Existe un `Protocol` (o stub `TYPE_CHECKING`) que declara el estado compartido de los mixins,
   y un type checker (mypy/pyright) ejecutado sobre `molsysviewer/viewer/` no reporta accesos a
   atributos no declarados.
2. La resolución del caller de ArgDigest usa un único mecanismo; los 8 `__name__ = "...core"`
   se han eliminado sin que ningún test de digestión se rompa.
3. Un test verifica que todo método público de `MolSysView` decorado con `@digest()` resuelve a
   su entrada de whitelist correcta, de forma que añadir un mixin/método nuevo mal registrado
   falle en CI.

## 5. Notas de alcance

- Esta propuesta es de **mantenibilidad**, no corrige ningún comportamiento observable por el
  usuario. No debe priorizarse por encima de huecos de reproducibilidad como
  [[scene_look_state_reconstruction]], pero sí antes de 1.0 en su variante barata (Protocol +
  test de caller), porque reduce el riesgo de regresiones silenciosas en la zona más activa del
  código.
- No reabrir la arquitectura de mixins en sí: la división es válida; lo que falta es el
  **contrato** sobre ella.
