# Propuesta de Mejora: Desacoplamiento y Robustez del Decorador de Señales de SMonitor

## 1. Contexto y Diagnóstico

MolSysViewer integra la biblioteca SMonitor (`_smonitor.py` y `SMONITOR_GUIDE.md`) para profiling de rendimiento, instrumentación y diagnóstico de liveness. Esta integración se realiza decorando los métodos críticos de la API pública con el decorador `@signal(tags=[...])`.

El problema de diseño radica en el **acoplamiento rígido y el riesgo de fuga de tipos a través del decorador**. Muchos de los métodos decorados en la API pública de Python (como `add_sphere` en `spheres.py` o `new_region` en `regions.py`) no son funciones puramente ejecutorias de tipo "disparar y olvidar" (*fire-and-forget*); en su lugar, retornan instancias complejas de objetos funcionales (como `Layer`, `Region` o `Selection`) destinados a soportar el encadenamiento de métodos (*fluent API*).

Si el decorador `@signal` o el gestor interno de SMonitor introduce envoltorios asíncronos o proxies sobre los valores de retorno sin preservar de forma transparente e incondicional el tipo nativo, la firma exacta del método y las propiedades del objeto retornado:
1. Las llamadas encadenadas de la API (tales como `view.shapes.add_sphere(...).set_color(...)` o `view.regions.new(...).set_representation(...)`) fallarán abruptamente con errores de tipo de Python (`AttributeError: 'NoneType' or 'SignalWrapper' object has no attribute 'set_color'`).
2. Cualquier fallo o retardo en la inicialización interna del sistema de diagnóstico de SMonitor puede propagarse en cascada hacia la API pública del visor, bloqueando la ejecución normal del modelado científico.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Inestabilidad Inesperada**: Los desarrolladores de add-ons o científicos experimentan fallos en celdas de Jupyter que antes funcionaban perfectamente, debido a sutiles fugas de tipo de SMonitor que alteran el comportamiento del encadenamiento de métodos.
* **Falta de Desacoplamiento**: El sistema de diagnóstico de rendimiento (que es una herramienta auxiliar opcional de desarrollo) queda fuertemente acoplado a la API funcional de producción, haciendo que el visor dependa de la estabilidad de SMonitor para su funcionamiento básico.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Aislamiento Transparente y Desacoplamiento del Decorador de Señales

Se propone robustecer la integración de SMonitor aplicando los siguientes principios de diseño:

1. **Asegurar Preservación Absoluta de Firma y Tipo (Passthrough Perfecto)**:
   Garantizar que el decorador `@signal` en SMonitor actúe como una envoltura de paso directo (*perfect passthrough*) utilizando `functools.wraps(func)` y retornando estrictamente el valor de retorno nativo sin alteraciones:
   ```python
   # Estructura del decorador seguro
   def signal(tags=None, extra_factory=None):
       def decorator(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               # Registrar la señal y métricas de forma segura en segundo plano
               try:
                   record_signal(func.__name__, tags, args, kwargs)
               except Exception:
                   # NUNCA permitir que un fallo de diagnóstico rompa la ejecución
                   pass
               # Retornar incondicionalmente el resultado original de la función
               return func(*args, **kwargs)
           return wrapper
       return decorator
   ```

2. **Desacoplamiento Dinámico en Entornos de Producción**:
   Si SMonitor no está presente, no está inicializado o el visor se ejecuta en modo de producción, el decorador `@signal` debe resolverse instantáneamente como una función de identidad (*no-op*), eliminando cualquier sobrecosto de envoltura y reduciendo a cero el acoplamiento a nivel de ejecución.

---

## 4. Criterios de Aceptación

1. La presencia o ausencia de instrumentación mediante SMonitor y el decorador `@signal` no debe alterar de ninguna forma el tipo de retorno, la firma o el comportamiento de encadenamiento de métodos de la API pública de MolSysViewer.
2. Cualquier excepción lanzada dentro de la lógica interna de recolección de métricas de SMonitor debe ser atrapada de forma silenciosa e inofensiva, impidiendo su propagación al flujo principal de ejecución del usuario.
3. Se deben incorporar pruebas unitarias específicas que convaliden que el encadenamiento de métodos de la API (como crear una forma y alterar su color en la misma línea de código) funciona correctamente bajo perfiles con instrumentación activa e inactiva.
