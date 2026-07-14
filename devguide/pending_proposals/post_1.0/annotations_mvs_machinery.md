# Propuesta post-1.0: anotaciones avanzadas sobre la maquinaria MVS de Mol*

**Estado:** post-1.0 (decisión tomada el 2026-07-12)
**Contrato aplicable:** `../../scene_contracts.md` Part II, Contract V — un objeto de
dominio *posee* su realización visual; no *es* esa realización.
**Dependencia upstream:** ninguna. Es maquinaria que ya viene en Mol*
(`molstar/lib/extensions/mvs/`), sin estrenar en este repositorio.

## Contexto

Mol\* incluye, dentro de MolViewSpec, un sistema de anotaciones alimentable desde
datos externos que hoy **no usamos en absoluto**. Nuestras anotaciones se dibujan
con la representación `label` básica y un `customText`
(`js/src/managers/handlers/annotation-handlers.ts`).

Lo que MVS ofrece (`extensions/mvs/components/`):

- **`annotation-label`** — etiquetas a partir de una tabla de datos; `fieldName`
  elige qué columna lleva el texto.
- **`annotation-color-theme`** — colorea la estructura desde esos mismos datos,
  con paleta, ordenación y color para los ausentes.
- **`annotation-tooltips-prop`** — tooltips desde los datos.
- **`annotation-structure-component`** — construir componentes a partir de la
  anotación.
- **`custom-label`** — etiquetas ad hoc: `items: [{text, position}]`, donde
  `position` puede ser **una selección o unas coordenadas `x, y, z` explícitas**.

El direccionamiento admite varios niveles —`whole_structure`, `entity`, `chain`,
`residue`, `residue_range`, `atom`— y entre sus campos están **`atom_index`**
(0-based, el nuestro) y **`residue_index`**, además de **`group_id`**, que agrupa
varias filas bajo **una sola etiqueta** (su ejemplo: una etiqueta para dos
cadenas).

Es decir: se le pueden dar nuestros datos —índices de átomo o de grupo, el texto,
el color, el estilo tipográfico— y él los representa nativamente. **No hay que
elegir entre su motor y nuestros datos**, igual que ocurre con
`CustomInteractions` en el dominio de interacciones.

## Estado local pre-1.0 (lo que sí se hace antes)

El subpanel de Annotations de la 1.0 se construye sobre la representación `label`
**que ya existe**, porque lo que hoy bloquea al usuario no es MVS:

- editar el texto **in situ** (`set_text`), que hoy no tiene interfaz alguna;
- renombrar, mover a una capa, mostrar/ocultar, borrar;
- crearla desde la **selección activa**;
- y que todo ello pase por la API pública, se serialice y sea deshacible
  (Contracts S1, S2, S5, S6).

**Nada de eso necesita MVS.** Las etiquetas ancladas a coordenadas libres, el
`group_id` y los tooltips dirigidos por datos son incrementales: mejoran el
producto, pero nadie está parado por su ausencia.

### La única condición que pre-1.0 debe respetar

**El ancla de una anotación tiene que ser un concepto extensible desde el
principio**, no "una lista de átomos y punto".

Hoy `Annotation.set_coordinates` lanza `NotImplementedError` con el mensaje
*"annotation anchors are tied to atom indices"*. Si el modelo y la serialización
tratan el ancla como algo **con forma** —átomos hoy; coordenadas libres o un nivel
de residuo/cadena mañana—, entonces MVS llega después como una extensión aditiva.
Si lo cerramos en `atom_indices` para siempre, llegará como una migración de
formato.

Cuesta casi nada hacerlo bien ahora, y es lo que hace que aplazar salga barato.

## Trabajo diferido a post-1.0

1. **Migrar la realización de las anotaciones a MVS** como un `renderer`
   alternativo (Contract V): el objeto de dominio no cambia, cambia lo que dibuja.
2. **Etiquetas ancladas a coordenadas libres** — hoy imposibles.
3. **Una etiqueta para varios elementos** vía `group_id`.
4. **Tooltips dirigidos por datos**.
5. **Anotaciones a nivel de cadena / entidad / rango de residuos**, no solo de
   átomos.

## Por qué se aplaza (las tres razones)

1. **No es lo que bloquea al usuario** (ver el estado pre-1.0 arriba).
2. **El riesgo está del lado equivocado.** MVS está pensado para vistas
   **declarativas**: los datos se cargan una vez y describen una escena. Lo nuestro
   es **interactivo y mutable** —se añade, se edita y se borra en vivo—. Que el
   proveedor MVS acepte datos *inline* y se actualice con eficiencia en caliente es
   plausible (`MVSAnnotation.createEmpty(schema)` sugiere construcción
   programática) pero **está sin verificar**. Cambiar deuda cierta —el
   `import_state` que no reconstruye el modelo, los shapes que no se serializan, el
   undo destructivo— por una incógnita, camino de la 1.0, es un mal negocio.
3. **Contract V hace que aplazar sea gratis.** Cuando la anotación *posee* su
   realización en vez de serla, cambiar de renderer más adelante es puramente
   aditivo. La decisión no hay que tomarla ahora: ese es justo el trabajo que hace
   el contrato.

## Lo primero que hay que probar cuando se retome

**Que MVS aguanta datos inline y edición en vivo**, en navegador real
(`js/tests/e2e/`, el harness de la Fase 14 del rework). Si no los aguantase con
soltura, esta propuesta se cae entera y hay que quedarse con la representación
`label` — así que es la comprobación que va **antes** de cualquier compromiso, no
después.

## Dos avisos

- **Esto no toca el dominio de Interacciones.** `extensions/mvs/` y
  `extensions/interactions/` son extensiones distintas. El plan de
  `../interactions_domain.md`, que usa `CustomInteractions`, sigue en pie sin
  cambios.
- **`annotation-color-theme` solapa con nuestras capas de color por átomo**
  (Contract B, `_atom_color_layers`): reimplementamos algo que Mol\* ya traía. **No
  se toca.** Contract B funciona y se validó en navegador real en la Fase 14 del
  rework; cambiarlo ahora sería riesgo sin beneficio. Queda anotado aquí como
  salida de emergencia por si el sistema de capas topa algún día con un muro de
  rendimiento.
