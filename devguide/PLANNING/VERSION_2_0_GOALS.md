# MolSysViewer — Objetivos versión 2.0

Este documento recoge los objetivos de **medio y largo plazo** para la
versión **2.0** de MolSysViewer. Parte de una versión 1.0 ya estable y se
centra en convertir al visor en un **motor de visualización y análisis
científico integrado** dentro del ecosistema MolSys*.

Mientras que la 1.0 consolida la base (carga, regions/layers, popup,
trayectorias, shapes básicos), la 2.0 persigue:

- exponer APIs científicas de más alto nivel,
- integrar más profundamente TopoMT y PharmacophoreMT,
- ofrecer herramientas de inspección y callbacks,
- y plantear opciones de rendimiento y multi-engine para casos intensivos.

---

## 1. Visión general de la 2.0

La 2.0 debe ser la versión en la que MolSysViewer pasa de ser “un visor
robusto” a ser un **entorno de trabajo** para análisis estructural y
visualización avanzada:

- Permite **consultas cuantitativas** (distancias, contactos, ejes, etc.)
  desde `MolSysView` sin que el usuario tenga que ir manualmente a MolSysMT
  para todo.
- Ofrece **overlays especializados** para TopoMT (cavidades, canales) y
  PharmacophoreMT (features farmacofóricas) como ciudadanos de primera
  clase.
- Proporciona un **inspector de escena ligero** y callbacks que ayudan a
  construir flujos interactivos en notebooks y docs sin necesidad de
  reimplementar UI.
- Mantiene la división conceptual: MolSysMT hace la ciencia, Mol\* dibuja;
  MolSysViewer orquesta y expone APIs cómodas.

---

## 2. Módulo “structure” y API científica integrada

### 2.1. Objetivo

Introducir gradualmente un módulo lógico `structure` accesible desde
`MolSysView` que envuelva operaciones frecuentes de análisis geométrico y
topológico:

- `get_*` → devuelven datos numéricos (vía MolSysMT).
- `show_*` → añaden overlays visuales en Mol\* correspondientes.

Sin intentar replicar todo MolSysMT, la idea es ofrecer **atajos de alto
valor** directamente en el visor.

### 2.2. Candidatos iniciales

En una primera fase de 2.0, los focos razonables serían:

- Distancias:
  - `get_distances(sel1, sel2, engine="molsysmt")`.
  - `show_distances(sel1, sel2, ...)` con etiquetas y líneas en Mol\*.

- Contactos / vecinos:
  - `get_contacts(sel1, sel2, cutoff, engine="molsysmt")`.
  - `show_contacts(...)` como overlays (líneas/aristas con filtro por
    distancia o tipo).

- Ejes principales / movilidad:
  - `get_principal_axes(selection)`.
  - `show_principal_axes(selection, ...)` (vectores/glyphs representando
    ejes principales).

Las funciones más costosas (PCA, RMSD globales, etc.) pueden llegar más
adelante, pero conviene sentar desde el principio una **convención limpia
de nombres** y firmas.

### 2.3. Diseño API

Principios:

- Todos los `get_*` delegan en MolSysMT siempre que sea posible, usando
  selecciones y estructuras internas (`_molsys`) para evitar duplicar
  lógica científica.
- Los `show_*` construyen overlays usando el sistema de `layers` y
  `ShapesManager`, reutilizando los mismos mecanismos de tagging y
  limpieza que el resto de shapes.
- El parámetro `engine` se mantiene como puerta de entrada a futuros
  motores (sección 5), pero inicialmente `"molsysmt"` será el único
  soportado oficialmente.

Objetivo 2.0: disponer de un **subset bien pensado** de `get_*` / `show_*`
que cubra casos comunes y sirva de patrón para extensiones futuras.

---

## 3. Integración profunda con TopoMT y PharmacophoreMT

### 3.1. TopoMT (cavidades, pockets, canales)

MolSysViewer ya tiene soporte para shapes avanzados como superficies de
pocket y tubos de canal. La 2.0 debería:

- Definir APIs de alto nivel en Python que acepten directamente salidas
  de TopoMT (o de funciones intermedias en MolSysMT), por ejemplo:
  - `view.shapes.pockets.from_topomt(result, ...)`.
  - `view.shapes.tubes.from_topomt(route, ...)`.

- Acordar y documentar esquemas de datos para:
  - cavidades (centros, radios, valores escalares para color),
  - superficies (isosuperficies, bocas, planos de corte),
  - canales (centros a lo largo del canal, radios, distancias a solvente).

- Asegurar que estas integraciones:
  - generan layers bien etiquetadas (`tag=` significativo),
  - son fáciles de limpiar/manipular via `Layer` y API de shapes.

Objetivo 2.0: que un flujo típico “TopoMT → visualización en MolSysViewer”
se pueda expresar en pocas líneas de código legibles y que la escena sea
fácil de inspeccionar y ajustar.

### 3.2. PharmacophoreMT (features farmacofóricas)

Análogo a TopoMT, pero centrado en features farmacofóricas:

- Spheres y glyphs para:
  - donores/aceptores,
  - anillos aromáticos (discos),
  - puntos hidrofóbicos,
  - exclusión volumétrica.

- API de alto nivel:
  - `view.shapes.ph4.from_pharmacophoremt(model, ...)`.
  - Helpers por tipo de feature (`add_donor_features`, etc.).

- Integración con regiones:
  - Posibilidad de asociar features a regiones o layers con tags
    significativos para facilitar la inspección y manejo de visibilidad.

Objetivo 2.0: que MolSysViewer sea el “visor natural” de resultados
PharmacophoreMT, no sólo un visor genérico donde el usuario se compone
todo a mano.

---

## 4. Inspector de escena y callbacks

### 4.1. Inspector ligero

Sin llegar a construir una UI pesada, la 2.0 puede introducir un
“inspector ligero”:

- En Python:
  - Helpers que devuelvan un resumen de la escena:
    - lista de regiones (tag, selección, estado de visibilidad,
      tipo de rep principal),
    - lista de layers (tag, tipo/kind, número de objetos, visibilidad).

- En TS/UI:
  - Opcionalmente, un panel simple (overlay) que liste tags y permita
    toggles rápidos de visibilidad (pensado para más adelante, y siempre
    respetando la filosofía de minimalismo en UI).

Objetivo 2.0: hacer visible al usuario qué hay en la escena sin obligarle
a inspeccionar estructuras internas o leer logs.

### 4.2. Callbacks y eventos

De forma muy controlada, la 2.0 podría introducir:

- Callbacks Python asociables a ciertos eventos del viewer:
  - click sobre un átomo o región,
  - hover sobre una feature farmacofórica,
  - cambios de frame de trayectoria,
  - etc. (empezando con un pequeño subconjunto).

- Esto implica:
  - Eventos JS→Py adicionales enviados desde la capa TS (Mol\* ya dispone
    de mucha información interactiva).
  - Un mecanismo en `MolSysView` para registrar callbacks de usuario
    (probablemente con alguna cola / filtrado para no saturar).

Objetivo 2.0: habilitar flujos interactivos razonables en notebooks/doc
sin convertir MolSysViewer en un framework de UI genérico.

---

## 5. Motores y rendimiento

### 5.1. Multi-engine (a medio plazo)

El parámetro `engine` mencionado en `DESIGN/OVERVIEW.md` abre la puerta a
otros motores además de MolSysMT:

- `"molsysmt"` (por defecto) para ciencia general.
- `"molstar"` para operaciones muy específicas donde Mol\* sea más rápido
  (p.ej., distancia en masa).
- `"numpy"`, `"numba"`, `"cupy"` para experimentos de rendimiento (GPU, etc.).

Objetivo para 2.0 no es soportar todos los motores, sino:

- Definir claramente cómo se selecciona el motor (argumento, config global).
- Elegir 1–2 casos donde merezca la pena (`engine="molstar"` para ciertas
  distancias, por ejemplo) y demostrar la viabilidad.

### 5.2. Benchmarking básico

Complementario al multi-engine:

- Conjunto de pruebas simples de rendimiento:
  - tiempo de carga para ciertas clases de sistemas,
  - coste de añadir shapes masivas (múltiples miles de objetos),
  - coste de reproducción de trayectorias largas.

- No se trata de construir un “benchmark suite” formal, sino de tener
  suficiente telemetría interna para:
  - detectar regresiones de rendimiento,
  - guiar optimizaciones aisladas cuando verdaderamente hagan falta.

---

## 6. Documentación avanzada y ejemplos integrados

La 2.0 también debería elevar el nivel de la documentación:

- **Guías completas de flujo científico**:
  - “Carga MolSysMT → selección → análisis básico (`get_*`) → overlays
    (`show_*`) → exportación HTML para docs.”
  - “TopoMT → cavidades/canales → visualización avanzada en MolSysViewer.”
  - “PharmacophoreMT → features farmacofóricas → blending con estructura.”

- **Ejemplos reproducibles**:
  - Notebooks de showcase que utilicen exclusivamente APIs públicas de
    MolSysViewer y sus dependencias, con vistas HTML exportadas integradas
    en la doc.

- **Devguide ampliado**:
  - Secciones específicas para:
    - el módulo `structure` y su mapeo sobre MolSysMT,
    - integraciones con TopoMT/PharmacophoreMT,
    - eventos/callbacks,
    - motores y consideraciones de rendimiento.

Objetivo 2.0: que alguien que ya conoce MolSysMT, TopoMT o
PharmacophoreMT pueda adoptar MolSysViewer como visor y herramienta de
presentación sin tener que deducir detalles de implementación.

---

## 7. Camino gradual hacia 2.0

Es probable que 2.0 no llegue de golpe, sino como una serie de versiones
1.x que incorporen piezas de esta visión. Una posible secuencia:

1. **1.1–1.2**  
   - Primeras funciones `get_*` / `show_*` (distancias/contactos) con
     integración MolSysMT.  
   - Algunos helpers de inspector de escena (Python).

2. **1.3–1.4**  
   - Integraciones de alto nivel con TopoMT y PharmacophoreMT.  
   - Overlays más ricos y documentación de esos flujos.

3. **1.5–1.9**  
   - Primeros callbacks/eventos JS→Py.  
   - Exploración limitada de motores alternativos para casos concretos.  
   - Mejora incremental del inspector y de la UI (sin reescribirla por
     completo).

4. **2.0**  
   - Congelación de un conjunto claro de APIs avanzadas (`structure`,
     integraciones, callbacks básicos, quizá un motor alternativo oficial).  
   - Documentación consolidada de todos estos aspectos.  
   - Revisión de compatibilidad hacia atrás (qué se garantiza, qué se
     depreca).

---

## 8. Resumen

La versión 2.0 de MolSysViewer se concibe como:

- Un visor que no sólo muestra estructuras y shapes, sino que:
  - ofrece APIs `get_*` / `show_*` para análisis geométrico/topológico
    frecuente,
  - se integra estrechamente con TopoMT y PharmacophoreMT,
  - permite inspeccionar y manipular la escena de forma cómoda,
  - admite callbacks bien definidos para flujos interactivos.

- Un proyecto donde:
  - MolSysMT sigue siendo el motor científico central,
  - Mol\* sigue siendo el motor de render,
  - y MolSysViewer actúa como la “fachada” integrada del ecosistema MolSys*.

El objetivo de este documento es servir de guía a medio/largo plazo: cuando
la 1.0 esté consolidada, las decisiones de diseño y prioridades deberán
medirse contra estas metas 2.0.

