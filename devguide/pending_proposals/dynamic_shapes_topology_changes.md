# Propuesta de Mejora: Gestión de Formas Dinámicas ante Cambios de Topología

## 1. Contexto y Diagnóstico

En MolSysViewer 1.0.0+ se introdujo el soporte para **resolución dinámica de coordenadas en el frontend (Shapes por Selección)**. Al llamar a `view.shapes.add_sphere` con una selección o listas de índices, el frontend en JavaScript calcula reactivamente el centroide en 3D del conjunto de átomos consultando la conformación activa de Mol* (`unit.conformation.position`) ante cada cambio de frame.

El problema potencial surge en simulaciones moleculares con **topología dinámica** (sistemas donde el número de átomos, enlaces o la composición molecular cambia de forma interactiva o entre frames de una trayectoria, como en simulaciones de protonación reactiva, hibridación, evaporación de solventes o inserción de ligandos).

Si el conjunto de índices de átomos provisto originalmente (ej. `atom_indices` o la expresión evaluada en el frame inicial) apunta a índices que, en un frame posterior de la trayectoria, están fuera de rango o ya no existen en la conformación activa de Mol*:
1. El código de JavaScript (`shapes/index.ts` y `shape-handlers.ts`) intercepta el error de forma segura mediante cláusulas `if (!locA || !locB)` para evitar que el visor colapse o bloquee el hilo de renderizado de WebGL.
2. Sin embargo, la forma geométrica (ej. la esfera) **desaparece silenciosamente de la escena** durante esos frames de la simulación.
3. **El backend de Python no se entera de la desaparición**, manteniendo una inconsistencia entre lo que el código en Python asume que está renderizado y lo que el usuario ve en pantalla.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Inconsistencia Visual Desconcertante**: Durante la reproducción de una trayectoria dinámica, la forma (ej. una esfera que representa el centroide de un sitio activo de unión) parpadea o desaparece sin explicación cuando los átomos de la selección se eliminan o alteran en la topología de un frame específico.
2. **Falta de Fiabilidad para Análisis**: Si el usuario asume que la forma está presente para guiar su exploración científica, la ausencia de feedback de renderizado impide conocer si la forma no se muestra por un fallo de selección, por un error de coordenadas o por la desaparición de los átomos subyacentes.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta A: Degradación Gradual y Representación Alternativa
* **Descripción**: Si un subconjunto de los átomos especificados en `atom_indices` desaparece en un frame, pero al menos un átomo de la selección sigue existiendo, el frontend debe calcular el centroide basándose únicamente en los átomos sobrevivientes de la selección en lugar de fallar de forma total. Si todos los átomos de la selección desaparecen, en lugar de eliminar la forma de la escena, se puede renderizar de forma translúcida en la última posición conocida o en las coordenadas por defecto `[0, 0, 0]`, con un color de advertencia (ej. rojo opaco o gris) que indique visualmente el estado de desactualización.
* **Pros**: Previene la desaparición abrupta e invisible del objeto en el espacio tridimensional.
* **Contras**: Puede generar confusión si la forma se renderiza en una ubicación fija que no tiene sentido físico actual.

### Propuesta B: Canal de Notificación de Renderizado Fallido (`shape_render_failed`)
* **Descripción**: Cuando el frontend intente calcular el centroide para un frame y determine que la selección de átomos es inválida o vacía, debe emitir un mensaje de evento `"shape_render_failed"` hacia Python que contenga el tag de la forma, el frame actual y la causa del fallo.
* **Pros**: Sincronización de estado perfecta en Python, permitiendo al desarrollador de add-ons o al notebook alertar proactivamente al usuario en el kernel.
* **Contras**: Requiere añadir tráfico de mensajes asíncronos en cambios de frame dinámicos.

---

## 4. Criterios de Aceptación

1. Las formas dinámicas resueltas por selección deben calcular su centroide de forma adaptativa si al menos un átomo de la lista sigue existiendo en el frame activo del visualizador.
2. Si una forma geométrica dinámica no puede ser renderizada debido a una selección vacía en un frame específico, el visor no debe colapsar y debe registrar el estado de forma que pueda ser consultado o notificado al backend.
3. Se deben incorporar controles robustos en las pruebas de frontend y de backend para convalidar el comportamiento de las formas dinámicas frente a cambios drásticos de topología.
