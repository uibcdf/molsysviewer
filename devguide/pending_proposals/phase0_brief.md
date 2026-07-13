# Brief — Fase 0: identidad y coherencia de la API

**Para:** el colaborador. **Fecha:** 2026-07-12.

---

## 0. Lee esto primero (y no implementes contra este brief)

Este brief **no describe el trabajo**: te dice **qué documentos lo describen**, en qué
orden hacerlo, y cómo se va a auditar. El detalle está en los documentos, y **ellos
mandan**:

| documento | por qué |
|---|---|
| `devguide/pending_proposals/scene_objects_contracts.md` | **Las reglas.** Lee entero el **§0** (la evidencia: cada defecto verificado ejecutando) y el **Contract T** y **Contract S0**. |
| `devguide/pending_proposals/phase0_identity_and_managers.md` | Qué aterriza y por qué. |
| `devguide/pending_proposals/phase0_identity_and_managers_implementation_plan.md` | **El orden de trabajo y el inventario del peligro.** Este es el que manda sobre el *cómo*. |
| `devguide/pending_proposals/phase0_identity_and_managers_migration.md` | Los cambios que **rompen** la API, el corpus y los tests. |

**Trabaja sobre la última versión de `devguide/pending_proposals/`.** En la ronda anterior,
nueve de tus dieciséis propuestas ya estaban escritas allí.

---

## 1. Por qué esta fase va primero, y sola

Dos problemas que resultan ser **la misma herida**:

- **La escena no tiene una noción coherente de identidad.** Cuatro registros de tags
  (`_regions`, `_scene_objects`, `_layers`, `_selections`), **tres guards** —y `_regions`
  no tiene ninguno—, y seis contadores. Hoy `view.regions.add(tag='x')` funciona con un
  shape `x` existente, pero un shape `x` y una anotación `x` **no pueden coexistir**. No
  hay ningún principio detrás de esa línea.
- **Los cinco managers se separaron al crecer.** `tags` es una *property* en dos y un
  *método* en tres. A `shapes` le faltan **seis métodos** que los demás tienen — incluido
  **`hide()`**.

Y esa última carencia **es, casi con seguridad, la razón de que el panel de Shapes se
saltara Python** y repintara Mol\* directamente (§0.2): la API no le ofrecía las mismas
jugadas. Arregla la API y el defecto de arquitectura se queda sin excusa.

**Ninguna otra fase puede hacerse antes que ésta, y ésta no puede hacerse después.**

---

## 2. Tres commits, no uno

Son **112 sitios** que indexan por tag desnudo (84 en Python, 28 en TS) y cinco cambios que
rompen la API. **Eso no es auditable en un solo commit**, así que va en tres, y cada uno
debe quedar **verde por sí solo**.

### Commit 1 — El resolver, y los `TagsManager` (no rompe nada)

1. **`scripts/api_resolver.py`**. **No está en el repo** (`scripts/` solo tiene
   `bootstrap.sh`, `dev.sh`, `validate_resources.py`): se escribió durante el rework y
   nunca se commiteó. Recupéralo o reescríbelo, **commitéalo y mételo en CI**:
   parsea los *code fences* de los `.md`, las celdas de los `.ipynb` y los `.py`, resuelve
   cada cadena `view.*` / `viewer.*` contra la API viva, y reporta lo que no existe.
   **Es la única comprobación que detecta una llamada muerta en un `.md`** — ejecutar los
   notebooks no puede.
2. **`molsysviewer/tags.py` → `TagsManager`**, uno por dominio. Se lleva: el prefijo, el
   contador, el **guard de unicidad del dominio** (`regions` gana el que nunca tuvo) y el
   **high-water mark serializado**.
   **No debe mantener su propia lista de tags vivos**: sería una segunda fuente de verdad y
   divergirá del registro. Es dueño de la **política de nombres** y **le pregunta** al
   registro qué existe.

**En este commit no cambia ningún comportamiento visible.** Es la red antes del salto.

### Commit 2 — La identidad `(dominio, tag)` — **el peligroso**

Lee el §1, §2 y §3 del *implementation plan*. El orden **no es negociable**: modelo Python
primero, wire después, runtime al final.

1. **Cualificar los registros**: `_scene_objects` y `Layer.members` pasan a estar indexados
   por `(kind, tag)`. **Se visitan los 84 sitios.** *Un sitio que sigue compilando después
   de cambiar la clave es un sitio que estaba ignorando el `kind`: trata una compilación
   limpia como sospechosa, no como éxito.*
2. **Los reescritores del historial** (`viewer/history.py:27-43`) pasan a ser *kind-aware*.
   **Es la edición de mayor riesgo de toda la fase**: hoy `_rewrite_history_layer_tag`
   reescribe **las tres historias** buscando por tag desnudo, así que renombrar el *shape*
   `site1` reescribiría también la entrada de la *anotación* `site1` — corrompiendo el
   replay, el export HTML y el popup, **sin que nada falle**.
3. **El wire tipa su direccionamiento**: `hide_layer`, `show_layer`, `delete_layer`,
   `set_layer_tag` llevan el `kind`. **El `kind` ya existe en los dos lados** —
   `SceneObject.kind` en Python, `registerTaggedRef(ref, tag, kind)` y `layerMeta` en el
   runtime. **Úsalo, no lo inventes.**
4. **`tagIndex`** (`state-handlers.ts:120`) pasa a indexarse por `(kind, tag)`.

**El riesgo es el aliasing silencioso**: cualquier sitio que siga indexando por tag desnudo
funde dos objetos **sin error y sin traza**.

### Commit 3 — Coherencia de la API + migración (rompe la API)

1. **`LayersManager`** (nuevo), copiando el molde de `RegionsManager` —**subclase de
   `dict`**, para que `view.layers['x']`, la iteración y `len()` sigan funcionando— con la
   superficie canónica y **`.add(tag, *, kind=None, meta=None)`**.
   **Explícito, nunca `**meta`**: un `**kwargs` se traga los typos en silencio
   (`layers.add('x', kidn='shape')` acabaría en `meta={'kidn': ...}` y el `kind` sin fijar),
   y ése es justo el fallo que este bloque existe para eliminar.
2. **Retirar `view.new_layer()`** (`scene_registry.py:138`) — **sin perder lo que llevaba**:
   acepta `kind` y `meta`, y `Layer.meta` se lee en **14 sitios**.
3. **`tags` pasa a método** en `selections` y `annotations`. **Rompe la API.**
4. **Completar `shapes`**: `count`, `records`, `delete`, `set_tag`, `show`, `hide`.
5. **Añadir `annotations.set_style()`** — hoy **no existe** (verificado), y sin él el panel
   de la Fase 6 tendría que **borrar y recrear** la anotación para reestilizarla, perdiendo
   tag, capa e historial.
6. **Matar los alias sin declarar**: `add_gaussian_isosurface = add_scalar_isosurface`
   (`pocket_blobs.py:142`) y `GroupLayer = Layer` (`layers.py:1194`). *(El de
   `AddonWorkbenchSectionSpec` se queda: lleva su `# Deprecated alias` y es legítimo.)*
7. **Arreglar `selections.add()`**: hoy **no se puede llamar con sus propios defaults** —
   la firma dice `items=None` pero el digestor **rechaza `None`**. Arregla el digestor, no
   la firma.
8. **Migrar `docs/`** y **`architecture.md` §Key invariants 1**, que hoy afirma una
   unicidad global de tags que el código no tiene y, tras esta fase, deliberadamente no
   tendrá.

---

## 3. Los tests obligatorios

Cada mecanismo se verifica **por mutación**: revierte el mecanismo y **su test debe
fallar**. Un test que sigue pasando bajo mutación es hueco y no cuenta.

**El test que define la fase** — el aliasing:

```python
view.shapes.add_sphere(..., tag='site1')
view.regions.add(selection='...', tag='site1')
view.shapes.hide('site1')

assert view.shapes['site1']._hidden is True
assert view.regions['site1']._hidden is False     # ← toda la fase, en una línea
```

**Mutación:** quita el `kind` de la clave del índice. **El test debe fallar.**

**El test del historial** (el riesgo del commit 2):

```python
view.shapes.add_sphere(..., tag='site1')
view.annotations.add_annotation(text='...', tag='site1')
view.shapes.set_tag('site1', 'sphere1')
assert any(r['tag'] == 'site1' for r in view._annotation_history)   # intacta
```

**El test de los contadores:**

```python
v2.import_state(estado_con_measurement1)
v2.measurements.add_distance(...)          # tag automático
assert v2.measurements.count() == 2        # hoy: 1 — el tag nuevo pisó al importado
```

**El test de superficie** (Contract S0), **por introspección**, para que el próximo manager
no se vuelva a desviar:

```python
for manager in (regions, selections, shapes, annotations, measurements, layers):
    for name in ("add", "tags", "count", "records", "info", "contains",
                 "get", "delete", "clear", "set_tag"):
        assert callable(getattr(manager, name))    # método, nunca property
```

**E2E en navegador real:** dos objetos con el mismo tag; oculta uno; **solo su nodo** sale
del árbol de render de Mol\*. El bug de `tagIndex` es invisible a los tests unitarios.

---

## 4. Lo que esta fase **no** hace

- **Ningún cambio de GUI. Ninguno.** Si el diff toca `js/src/ui/panels/`, te has salido.
- Ningún comportamiento nuevo de dominio (ni color, ni visibilidad, ni serialización más
  allá de los high-water marks).
- **Ningún refactor de `core.py`.** Los cinco `_next_*_tag()` salen porque el `TagsManager`
  se los lleva; el despachador se parte en la **Fase 2**, no aquí; los ocho `_remap_*` se
  quedan donde están (deuda declarada).
- Ningún campo `owner` en los objetos de escena.

---

## 5. Las reglas (no negociables)

- **`sandbox/` no se toca. Nunca.** Y ojo: `sandbox/Curso/Unit_07.ipynb:61` y
  `Unit_14.ipynb:61` usan `.tags` como propiedad y **tras esta fase imprimirán
  `<bound method ...>`** — no fallarán, que es peor. **Lo arregla el mantenedor**, no tú.
  No lo toques; ya está anotado.
- **`molsysviewer/viewer.js` es generado: nunca se edita a mano.** Se reconstruye con
  `npm run build:runtime`, y **como último paso** tras el último cambio en TS.
- **Verde significa todo**: `pytest` + `npm run test:js` + `npm run build:runtime` +
  `npx tsc --noEmit` (línea base: **cero** errores).
- **El corpus se migra en esta fase**, no "más tarde": el `api_resolver` debe reportar
  **cero llamadas sin resolver**.
- Los **5 tests que hoy afirman que una colisión de tags se rechaza** no se "arreglan"
  aflojando la aserción: bajo Contract T algunos de esos rechazos pasan a ser **legales**.
  **Léelos y re-decídelos uno a uno.** Un test que se arregla relajándolo hasta que pasa es
  un test borrado con pasos extra.

---

## 6. Cómo se va a auditar

**Sobre el árbol de trabajo, antes del commit, contra el código — nunca contra este brief
ni contra tu informe.** Cada mecanismo, por mutación. Y las afirmaciones se comprueban
**ejecutando**: en la última revisión, de ocho afirmaciones verificadas solo leyendo, **una
era falsa**, y detrás escondía el peor defecto de todo el bloque.

**Criterio mecánico de aceptación:**

```bash
# ningún sitio indexa ya por tag desnudo en el runtime
grep -n "tagIndex.get(tag)\|tagIndex.set(tag" molsysviewer/js/src/managers/handlers/state-handlers.ts
# -> 0 hits

# el resolver existe, corre y está limpio
python scripts/api_resolver.py docs/     # -> 0 unresolved
```
