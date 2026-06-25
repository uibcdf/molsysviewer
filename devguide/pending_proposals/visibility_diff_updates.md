# Propuesta de Mejora: Envíos Diferenciales de Visibilidad (evitar reenviar la lista completa de átomos visibles)

## 1. Contexto y Diagnóstico

Cada cambio de visibilidad (`hide`, `show`, `isolate`, y los rebuilds) termina llamando a
`_update_visibility_in_frontend` (`molsysviewer/viewer/core.py`, ~línea 1136), que envía la
**lista completa de índices de átomos visibles**:

```python
def _update_visibility_in_frontend(self):
    if self.atom_mask is None:
        return
    self._send({
        "op": "update_visibility",
        "options": {"visible_atom_indices": self.visible_atom_indices},
    })
```

donde `visible_atom_indices` (~línea 1121) es:

```python
return np.nonzero(self.atom_mask)[0].tolist()
```

Es decir, en cada operación de visibilidad se serializa y envía un array que puede tener tamaño
≈ `n_atoms`. Para sistemas grandes (decenas o cientos de miles de átomos), ocultar/mostrar un
puñado de átomos reenvía igualmente la lista entera de visibles.

El propio `_clean_message_history` ya trata esta op de forma especial (omite el caso
"todos visibles" `vis == list(range(len(vis)))`), lo que confirma que el equipo es consciente de
que es un payload voluminoso.

## 2. Impacto

- No es un bucle caliente (solo se dispara en ops de visibilidad explícitas, no por frame), por
  lo que la severidad es media, no crítica.
- Pero en flujos interactivos con un sistema grande y cambios de visibilidad frecuentes (p. ej.
  recorrer regiones encendiéndolas/apagándolas), cada clic envía un payload proporcional al
  tamaño total del sistema, no al cambio.

## 3. Propuesta de Solución

Introducir una op de visibilidad **diferencial** que transmita solo los átomos que cambiaron de
estado desde el último envío, manteniendo `update_visibility` (lista completa) como camino de
sincronización/rebuild:

1. En Python, recordar la última máscara enviada (`self._last_visibility_mask`).
2. Al actualizar, calcular el diff vectorialmente:
   ```python
   changed = np.nonzero(new_mask != old_mask)[0]
   shown = changed[new_mask[changed]].tolist()
   hidden = changed[~new_mask[changed]].tolist()
   ```
3. Si el diff es mucho menor que el total, enviar `op: "update_visibility_delta"` con
   `{shown, hidden}`; si no (p. ej. en el primer envío o tras un rebuild), enviar la lista
   completa actual como hoy.
4. Añadir el handler TS correspondiente que aplique el delta sobre la máscara de visibilidad de
   Mol* sin reconstruir el conjunto completo.

Consideración de reproducibilidad: para export/replay conviene seguir emitiendo el **estado
completo** (la op actual) en los puntos de snapshot, de modo que un replay no dependa de
reconstruir a partir de una cadena de deltas. El delta es una optimización de la sesión viva, no
del formato exportado.

## 4. Criterios de Aceptación

1. Mostrar/ocultar un subconjunto pequeño de un sistema grande envía un payload proporcional al
   **cambio**, no al tamaño total del sistema.
2. El estado de visibilidad resultante es idéntico al del camino de lista completa (test que
   compara máscara aplicada vía delta vs vía lista completa).
3. El export/replay sigue conteniendo estado de visibilidad completo y reproducible (sin
   depender de acumular deltas).

## 5. Relación

- Misma familia de optimización de tráfico que [[jupyter_websocket_redundancy_overflow]] y
  [[high_frequency_event_saturation]], pero aplicada al canal de visibilidad.
