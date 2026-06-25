# Propuesta de Mejora: Eventos de Ciclo de Vida del Frontend para Paneles de Add-ons

## 1. Contexto y Diagnóstico

MolSysViewer coordina el ciclo de vida de los add-ons en Python a través de los hooks `on_mount(view)` y `on_unmount(view)` de `AddonPanelWidget`. Estos hooks permiten que el backend prepare el estado e inicialice recursos cuando el panel se muestra en la pantalla del visor, y los limpie de forma segura cuando el usuario navega a otra sección.

La brecha de concepto radica en que **no existe una abstracción o equivalente de ciclo de vida en el lado de JavaScript del panel**. 

El desarrollador del add-on escribe el código ESM (`_esm`) de su panel registrando la función de renderizado principal:
```javascript
export function render({ model, el }) {
    // Inicialización del panel...
}
```

Sin embargo, el entorno de JavaScript no cuenta con notificaciones explícitas de:
1. **Montado (`mounted`)**: Saber cuándo el elemento `el` ha sido físicamente insertado en el DOM activo del navegador del usuario.
2. **Desmontado (`unmounted`)**: Saber cuándo el usuario ha navegado lejos y el panel va a ser destruido de la pantalla.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Fugas de Memoria de Gráficos Pesados**: Muchos add-ons científicos avanzados necesitan inicializar gráficos 2D pesados (ej. usando Chart.js o d3.js) o lienzos WebGL secundarios (ej. Three.js). Al no saber cuándo el panel es desmontado de la pantalla, no pueden destruir de forma controlada estas instancias de renderizado, provocando fugas de memoria severas en la sesión del navegador.
* **Fricción de Desarrollo (Hacks en JS)**: Los desarrolladores de add-ons se ven obligados a escribir trucos complejos basados en temporizadores recurrentes o en observadores de mutación del DOM (`MutationObserver`) para adivinar si su elemento `el` sigue estando visible en la pantalla.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

Se propone dotar a la función de renderizado del frontend de un contrato de ciclo de vida explícito, aprovechando los patrones modernos de AnyWidget y el controlador principal de MolSysViewer:

### Alternativa A: Retorno de Función de Limpieza (Clean-up Callback)
* **Descripción**: Permitir que la función `render` en JavaScript devuelva opcionalmente una función de limpieza, emulando el comportamiento estándar de hooks en frameworks modernos como React:
  ```javascript
  export function render({ model, el }) {
      const chart = initializeInteractiveChart(el);

      // Retornar la función de limpieza
      return () => {
          chart.destroy(); // Se ejecuta automáticamente al desmontar el panel
          console.log("Panel desmontado y recursos liberados.");
      };
  }
  ```
* **Pros**: Extremadamente intuitivo y alineado con los estándares modernos de desarrollo de interfaces de usuario.
* **Contras**: Requiere que el cargador dinámico de widgets en el frontend de MolSysViewer intercepte el retorno de la función `render` y guarde la referencia para su ejecución durante el unmount.

### Alternativa B: Eventos en el Proxy del Modelo
* **Descripción**: Exponer eventos de ciclo de vida explícitos a través del proxy Backbone `model` del panel en el frontend:
  ```javascript
  export function render({ model, el }) {
      model.on("msg:custom", (msg) => {
          if (msg.type === "panel:unmounted") {
              // Realizar limpieza de recursos
          }
      });
  }
  ```
* **Pros**: Muy sencillo de implementar en el despachador de mensajes actual de MolSysViewer sin modificar la firma del cargador de AnyWidget.
* **Contras**: Más propenso a olvidos por parte del desarrollador del add-on, en comparación con el retorno explícito de la Alternativa A.

---

## 4. Criterios de Aceptación

1. Los desarrolladores de add-ons deben contar con un mecanismo nativo y explícito en JavaScript para liberar recursos y destruir instancias gráficas pesadas al desmontarse el panel.
2. Si se adopta la Alternativa A, el cargador del visor en el frontend debe invocar incondicionalmente la función de limpieza retornada por `render` inmediatamente antes de remover el elemento `el` del contenedor de la interfaz.
3. Se deben incluir ejemplos de referencia en la documentación de add-ons (`devguide`) que muestren el patrón de inicialización y destrucción segura de recursos gráficos en el panel lateral.
