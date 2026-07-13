# Propuesta: coste de arranque y de mensaje (medido, no estimado)

**Estado:** propuesta (2026-07-12). **Todo medido**, con el comando al lado.
**Origen:** empezó investigando por qué la suite moría por OOM en el entorno de un colaborador.
El OOM resultó ser un límite de memoria de su orquestador (§5). Lo que apareció por el camino
es esto — y es bastante más gordo.

**Los tres hallazgos, por impacto:**

| # | qué | coste | dónde se arregla |
|---|---|---|---|
| **1** | Cada mensaje reasigna un trait de ipywidgets y re-serializa **todo** el payload | **6× — 17,5 ms por mensaje** | **MolSysViewer** (trivial) |
| **2** | Los decoradores de SMonitor/DepDigest cuestan **7,5× el trabajo real, incluso apagados** | 127 µs de los 262 | SMonitor / DepDigest (ecosistema) |
| **2b** | PyUnitWizard entra en **22 funciones internas** por llamada, **repitiendo trabajo**, y las decora todas | el resto de los 262 µs (**15× pint**) | **PyUnitWizard** |
| **3a** | `molsysviewer/__init__.py` tiene **15 imports eager**; el de MolSysMT tiene **0** | 3,86 s de arranque | **MolSysViewer** |
| **3b** | PyUnitWizard importa **6 backends de unidades** para declarar unos `TypeVar` | **65 MB** siempre desperdiciados | **PyUnitWizard** |

**Tres de los cinco son de PyUnitWizard o del ecosistema; dos son nuestros.** Los nuestros son los
que más pesan (1 y 3a) y los más baratos de arreglar.

---

## 1. El peaje por mensaje: reasignar el trait completo (**el gordo, y es nuestro**)

`viewer/history.py:348`:

```python
def _send(self, msg: dict) -> None:
    self._message_history.append(msg)
    ...
    if self._ready:
        self.widget.send(msg)                                       # manda sólo el mensaje
    else:
        self._pending_messages.append(msg)
        self.widget.initial_messages = list(self._pending_messages)  # ← RE-ASIGNA TODO
```

Cuando el frontend **no está listo**, cada mensaje **reasigna el trait entero**. Y al asignar un
trait sincronizado, ipywidgets ejecuta **`_separate_buffers`**, que recorre recursivamente **toda
la lista pendiente — incluido el `load_molsys_payload` con todas las coordenadas de todos los
frames**, buscando buffers binarios.

**Medido** (`demo["pentalanine"]`, 62 átomos × 200 frames):

```
   _ready = False  (tests, scripts, bootstrap) :  20,9 ms por mensaje
   _ready = True   (frontend vivo)             :   3,4 ms por mensaje
   → la reasignación cuesta 6× (17,5 ms por mensaje)
```

El perfil, para 50 esferas: **92.675 llamadas a `_separate_buffers`** y **2.983.863 `isinstance`**
— el **85 %** del tiempo total.

**A quién afecta.** A **todo lo que corre sin navegador**:

- **la suite de tests entera** (`_ready` es siempre `False` → ~80 s de suite, y buena parte es esto);
- **el bootstrap del widget** en Jupyter, antes del handshake;
- los scripts, el export HTML y el arranque del host standalone.

**Y explica el peaje que el rework ya persiguió una vez** (`scene_contracts.md` §0: "~3 segundos
por mensaje"). Aquella vez se atacó el síntoma; ésta es la causa.

**El arreglo es trivial:** no reasignar el trait en cada mensaje. Acumular en
`_pending_messages` y **volcar al trait una sola vez**, en el handshake. La lista ya existe;
sobra la línea que la copia al trait 400 veces.

**Cuidado (verificar, no suponer):** hay que confirmar que el frontend recibe `initial_messages`
completo en el arranque. Es un cambio de *cuándo* se asigna, no de *qué*. Un e2e real de
bootstrap debe pasar.

## 2. Los decoradores: el "modo apagado" cuesta 7,5× el trabajo real

Medido sobre `puw.get_value(q, to_unit="nanometers")`:

| | coste |
|---|---|
| pint desnudo (**el trabajo real**) | **17 µs** |
| overhead de los decoradores **incluso desactivados** | **127 µs** |
| telemetría activa | 118 µs |
| **total** | **262 µs** — **15× pint** |

Perfilando 300 llamadas: **4.800 invocaciones del decorador de SMonitor** (16 por llamada) y
**3.000 de DepDigest** (10 por llamada). El trabajo real es el **10 %**.

**La causa es una línea mal puesta** (`smonitor/core/decorator.py:52`):

```python
def wrapper(*args, **kwargs):
    try:
        manager = get_manager()      # ← se ejecuta SIEMPRE
        config = manager.config      # ← SIEMPRE
    except Exception as exc:
        ...
    if not config.enabled:           # ← el check llega DESPUÉS
        return fn(*args, **kwargs)
```

**El camino rápido no es rápido:** aunque la telemetría esté apagada, cada función decorada paga
`get_manager()`, el acceso a `config` y un `try/except` **antes** de descubrir que no tenía que
hacer nada. Y como una sola llamada pública atraviesa 16 funciones internas decoradas, se paga
16 veces.

**El arreglo:** comprobar un flag de módulo **primero** (`if not _ENABLED: return fn(...)`) — una
comparación de bool, ~20 ns. Beneficia a **todo el ecosistema UIBCDF**, no sólo a nosotros.

### 2b. Y PyUnitWizard tiene su parte: 22 llamadas internas, con trabajo repetido

El decorador no es el único culpable, y sería injusto (y equivocado) dejarlo ahí. Una sola
llamada a `puw.get_value(q, to_unit="nanometers")` entra en **22 funciones internas de
PyUnitWizard**, y **repite trabajo**:

```
   3×  _private/forms.py:8    digest_form        ← detecta el "form" TRES veces
   3×  _private/forms.py:38   digest_to_form
   2×  api/introspection.py   get_form
   2×  api/conversion.py:68   convert
   2×  _private/parsers.py:3  digest_parser
```

**Doce de sus funciones de API llevan `@digest` / `@signal`** (validation 2, construction 2,
extraction 4, conversion 3, context 1), así que cada una de esas 22 entradas paga el overhead
de §2 **otra vez**.

Son **dos problemas que se multiplican**:

- **la redundancia** — detectar el mismo `form` tres veces por llamada es trabajo tirado,
  independientemente de lo que cueste un decorador;
- **la decoración de las funciones internas** — un `@signal` tiene sentido en la **frontera
  pública** de la librería, no en cada helper privado que ésta se llama a sí misma. La telemetría
  quiere saber que el usuario llamó a `get_value`, no que `get_value` llamó tres veces a
  `digest_form`.

**El arreglo, en PyUnitWizard:** cachear la detección del form dentro de la llamada, y **quitar
los decoradores de las funciones internas**, dejándolos sólo en la superficie pública. Ninguna de
las dos cosas cambia la API.

**Honestidad sobre el impacto:** en una operación real del visor (`add_sphere`), todo esto es sólo
el **11 %** del tiempo — porque el hallazgo (1) lo eclipsa. **Arreglar (1) hace que (2) y (2b)
pasen a importar de verdad.** Reportar el "15× más lento que pint" sin medir el impacto real
habría sido vender una optimización que casi no se nota.

## 3. El arranque: 3,86 s y 414 MB

| | tiempo | RSS | paquetes pesados |
|---|---|---|---|
| `import molsysmt` | — | **122 MB** | **ninguno** |
| **`import molsysviewer`** | **3,86 s** | **414 MB** | matplotlib, sympy, astropy, unyt, physipy, quantities, scipy, numba, PIL, IPython |

**Abrir un notebook cuesta casi cuatro segundos** antes de la primera celda.

### 3a. Quince imports eager frente a cero (**nuestro**) — arregla el **tiempo**, no la memoria

```
molsysviewer/__init__.py   →  15 imports eager
molsysmt/__init__.py       →   0
```

MolSysMT usa **PEP 562** (`module.__getattr__` + `_LAZY_ATTRIBUTES`): nada se carga hasta que se
pide. **El patrón ya está escrito en el repo de al lado**; no hay que inventarlo, hay que
copiarlo.

> ⚠️ **No te dejes engañar por los 122 MB de MolSysMT: no ahorra memoria, la aplaza.** Medido:
>
> ```
> import molsysmt                 122 MB   (lazy — aún no ha cargado nada)
>   …sólo tocar msm.pyunitwizard  278 MB   ← +156 MB en cuanto se usa
> import molsysviewer             414 MB   (eager — lo carga todo ya)
> ```
>
> **El import perezoso arregla el TIEMPO (3,86 s → instantáneo), no la memoria.** Quien use el
> visor cargará lo mismo, sólo que más tarde. Es una mejora real y muy visible —abrir un notebook
> deja de costar cuatro segundos— pero **no es una mejora de memoria**, y prometerlo como tal sería
> engañarse.
>
> **La única memoria que se recupera de verdad son los 65 MB de §3b**: 414 → ~349 MB. El resto es
> el coste legítimo de numpy + MolSysMT + OpenMM + pint + ipywidgets + anywidget + IPython.

Desglose del `importtime`:

```
3,86 s  molsysviewer
1,93 s    molsysviewer._pyunitwizard      ← el 50 %
0,84 s    molsysviewer.config             (user_presets)
0,61 s    molsysviewer.demo → new_view → viewer.core → unyt
```

**Cuidado:** `config.user_presets`, `_smonitor`, `_argdigest` y `_depdigest` pueden tener
**efectos secundarios en el import** (leer ficheros, registrar cosas). Hacerlos perezosos cambia
**cuándo** ocurren. Comprobar ejecutando, no razonando.

### 3b. PyUnitWizard importa seis backends para declarar unos `TypeVar` (**hermano**)

`pyunitwizard/_private/quantity_or_unit.py` importa **todos** los backends instalados —pint,
openmm.unit, unyt, astropy.units, physipy, quantities— dentro de `try/except`, **sólo para
construir unos `TypeVar`**. `unyt` arrastra `sympy` y `matplotlib`.

MolSysViewer **sólo usa pint**.

| | RSS |
|---|---|
| pint + openmm.unit — lo único que usamos | 146 MB |
| + unyt, astropy, physipy, quantities | 211 MB |
| **desperdicio puro, nunca usado** | **65 MB** |

**En runtime un `TypeVar` no valida nada.** Declararlos bajo `TYPE_CHECKING`, o construir la lista
perezosamente, elimina los 65 MB **para todo el ecosistema**.

---

## 4. Prioridad, y quién lo arregla

**En MolSysViewer (nuestro):**

1. **El peaje por mensaje (§1).** Trivial, **6× en todo lo headless**, y explica un peaje que ya
   perseguimos una vez. **Empezar aquí.**
2. **El arranque perezoso (§3a).** Es lo que **nota el usuario**: 4 s → instantáneo. El patrón ya
   está escrito en MolSysMT.

**En PyUnitWizard (repo hermano) — y hay que abrirlo allí, no improvisarlo aquí:**

3. **Los `TypeVar` que importan seis backends (§3b).** 65 MB para todo el ecosistema.
4. **Las 22 llamadas internas con trabajo repetido, y la decoración de los helpers privados
   (§2b).** El `@signal` pertenece a la **frontera pública** de una librería, no a cada función
   que se llama a sí misma.

**En SMonitor / DepDigest (ecosistema):**

5. **El fast path del decorador (§2).** Comprobar `enabled` **antes** de construir el manager.
   Beneficia a MolSysMT, a MolSysViewer y a todo lo demás.

**Nada de esto entra en el bloque de scene objects.** Es trabajo propio — y buena parte, de otros
repositorios: **ábrelo allí**. Un problema que vive en otro repo no se arregla en el nuestro,
igual que el *cosphericity guard* no se arregla en un visor que no calcula ninguna triangulación.

## 5. Lo que esto **no** arregla: el OOM de la suite

De aquí salió la investigación, y conviene cerrarlo con honestidad:

- La suite pica en **1.046 MB**, razonable para una librería que arrastra OpenMM y MolSysMT.
- **Todos los tests usan la librería**, así que el import perezoso sólo **retrasa** el coste.
- Los 65 MB de PyUnitWizard son el **15 %** del baseline. Ayudan; no salvan.

**La causa del OOM es el límite de memoria del entorno de ejecución.** La solución es subir el
techo a 2 GB o partir la suite:

```bash
pytest tests/ -q --ignore=tests/test_benchmark.py --ignore=tests/test_build_html_state.py
pytest tests/test_benchmark.py tests/test_build_html_state.py -q
```

*(`test_benchmark.py` (718 MB) y `test_build_html_state.py` (743 MB) caen justo en el 31 % de la
suite, que es exactamente donde el proceso moría.)*

**Lo que sí hará (§1) es que la suite tarde bastante menos**, porque hoy cada uno de sus miles de
mensajes paga 17,5 ms de peaje.

## 6. Cómo se mide que ha funcionado

```bash
# §1 — el peaje por mensaje
python -c "…add_sphere ×30 con _ready=False…"        # objetivo: ≈ 3,4 ms, no 20,9
python -m pytest tests/ -q                            # objetivo: bastante menos de 80 s

# §2 — el fast path
python -c "…timeit puw.get_value…"                    # objetivo: < 40 µs, no 262

# §3a — el arranque (TIEMPO, no memoria)
python -X importtime -c "import molsysviewer" | tail -1        # objetivo: < 0,5 s (hoy: 3,86 s)
python -c "import molsysviewer as m; m.new_view; m.demo; m.pyunitwizard"   # la API intacta

# §3b — la memoria (y sólo baja por aquí)
/usr/bin/time -v python -c "import molsysviewer" 2>&1 | grep Maximum
#   hoy:      414 MB
#   objetivo: ~349 MB   (los 65 MB de los backends que nunca usamos)
#   NO esperes 122 MB: eso es MolSysMT sin haber cargado nada todavía.
```
