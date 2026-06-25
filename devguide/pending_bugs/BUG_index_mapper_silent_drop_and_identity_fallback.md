# BUG: `IndexMapper` descarta índices y cae a identidad en silencio

## Severidad

Media (riesgo de corrupción silenciosa de correspondencias; impacto mayor en datos posicionales
emparejados como enlaces, bonds y medidas).

## Diagnóstico

`molsysviewer/viewer/index_mapper.py` traduce índices originales/globales ↔ locales del visor.
Tiene dos comportamientos de manejo de errores que enmascaran fallos:

### 1. Descarte silencioso de índices no mapeables

`to_local_atoms`, `to_original_atoms`, `to_local_structures`, `to_original_structures` solo
añaden al resultado los índices que mapean correctamente:

```python
# to_local_atoms (~líneas 71-82)
res = []
for idx in original_indices:
    local_idx = self.to_local_atom(idx)
    if local_idx is not None:        # <-- índices no mapeables se omiten
        res.append(local_idx)
...
except Exception:
    return []                        # <-- ante cualquier error, lista vacía
```

Consecuencia: si la entrada mezcla índices válidos e inválidos, **la salida es más corta que la
entrada, sin aviso**. Para listas que codifican correspondencia posicional (pares de átomos de
un enlace, tripletas/cuádruplas de una medida, vértices de una malla), perder un elemento
**desalinea todo el resto** y produce geometría/medidas incorrectas en vez de un error.

Además, el `except Exception: return []` global convierte cualquier fallo inesperado en una
"traducción vacía" indistinguible de "no había nada que traducir".

### 2. Fallback a mapeo identidad si `msm.select` falla

En el constructor (~líneas 23-34):

```python
try:
    original_atoms = msm.select(molecular_system, selection=selection, syntax=syntax)
    ...
except Exception:
    try:
        n_atoms = int(msm.get(molecular_system, element="system", n_atoms=True))
    except Exception:
        n_atoms = 1
    self.original_atoms = list(range(n_atoms))   # <-- asume identidad
```

Si la selección era un subconjunto real pero `msm.select` falla por un motivo transitorio, el
mapper asume **identidad** (`0..n-1`) en lugar de señalar el error. A partir de ahí, todos los
picks, hovers, selecciones y zooms traducen con un mapeo silenciosamente **incorrecto**.

## Impacto

- Geometrías de shapes basadas en pares/tripletas de átomos pueden conectar átomos equivocados.
- Medidas (distancias/ángulos/diedros) pueden calcularse sobre átomos distintos a los pedidos.
- Picks/hovers pueden reportar el átomo equivocado cuando el sistema se cargó con una selección
  parcial y el fallback de identidad se activó.
- En todos los casos, **sin error ni traza**: el síntoma aparece tarde y lejos de la causa.

## Propuestas de corrección

1. **Modo estricto / aviso en mismatch de longitud.** Cuando una traducción descarta elementos
   (longitud de salida < entrada), emitir un warning vía `smonitor` con el detalle (cuántos y
   cuáles índices se cayeron), o lanzar si se invoca en modo estricto. Para datos posicionales
   emparejados, ofrecer preservar la posición con un centinela en vez de comprimir la lista.
2. **No tragar excepciones genéricas.** Sustituir `except Exception: return []` por captura de
   tipos esperados (`TypeError`/`ValueError`) y propagar lo inesperado, o al menos registrarlo.
3. **Fallback de identidad explícito.** Si `msm.select` falla en el constructor, registrar el
   fallo (smonitor) y marcar el mapper como "degradado a identidad" en un atributo inspeccionable
   (`self.degraded = True`), de modo que el estado anómalo sea visible y testeable, no silencioso.

## Criterios de aceptación

1. Traducir una lista con índices no mapeables produce un aviso/diagnóstico (o un error en modo
   estricto), no una lista silenciosamente más corta.
2. Un fallo de `msm.select` en construcción deja el mapper en un estado inspeccionable, no en un
   mapeo identidad indistinguible del caso correcto.
3. Existe un test que cubre: (a) entrada mixta válida/inválida; (b) construcción con selección
   que falla; verificando que el comportamiento es observable y no silencioso.

## Relación

- Instancia concreta de [[silent_exception_desync]].
- Relacionado con [[index_mapper_out_of_sync]] (este se centra en el manejo de errores; aquel en
  la sincronización reactiva del mapeo).
