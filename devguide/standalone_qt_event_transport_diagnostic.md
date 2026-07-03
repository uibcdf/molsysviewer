# Diagnostico provisional: transporte JS -> Python en standalone Qt

## Contexto

Durante la validacion real de `standalone_qt`, el backend Qt interactivo no
llegaba a ponerse en estado `ready` aunque el entorno Qt WebEngine ya estaba
desbloqueado:

- `qt6-webengine-uibcdf` ya aportaba recursos WebEngine y scripts de activacion.
- `pyside6-addons-uibcdf` ya exponia `QWebEngineUrlScheme.setFlags`.
- Qt WebEngine arrancaba sin el error previo de `icudtl.dat`.

Sin embargo, en una ventana Qt real, `bridge.ready` no cambiaba a `True`.

## Sintoma

El frontend cargaba, pero el evento inicial:

```json
{"event": "ready"}
```

no llegaba al bridge Python.

Esto bloqueaba toda la cola Qt, porque `QtMessageBridge` no despacha mensajes
Python -> JS hasta recibir `ready`.

## Hipotesis a distinguir

Habia dos causas posibles:

1. Mol*/WebGL no terminaba de inicializar en el entorno Qt.
2. El canal JS -> Python basado en `molsysviewer://event` no entregaba eventos
   en Qt real.

Los tests con fakes no podian distinguirlas porque simulaban directamente los
eventos del frontend.

## Diagnostico aislado

Se escribio un probe temporal fuera del repositorio con una pagina HTML minima,
sin Mol*, sin WebGL y sin el bundle `viewer.js`.

La pagina intentaba enviar:

```js
{ event: "ready" }
```

al mismo bridge Qt usando tres variantes del transporte original:

- iframe oculto con `iframe.src = "molsysviewer://event?..."`
- `window.location.href = "molsysviewer://event?..."`
- click programatico sobre un `<a href="molsysviewer://event?...">`

Resultado:

- `iframe`: no llegaba ningun evento a `acceptNavigationRequest`.
- `window.location` y `<a>`: Chromium bloqueaba la navegacion y la vista acababa
  en `about:blank#blocked`.

Conclusion: el problema era el transporte por navegacion, no Mol*/WebGL.

## Solucion aplicada

Se sustituyo el envio JS -> Python por navegacion por un envio basado en
`fetch(...)` sobre el mismo esquema custom:

```js
fetch("molsysviewer://event?payload=...")
```

En Python, `standalone_qt` instala ahora un `QWebEngineUrlSchemeHandler` para el
esquema `molsysviewer`, de forma equivalente al handler ya usado para payloads
grandes en `molsysviewer-payload`.

El esquema `molsysviewer` se registra con flags compatibles con `fetch`:

- `SecureScheme`
- `CorsEnabled`
- `FetchApiAllowed`
- `LocalScheme`

`acceptNavigationRequest` se conserva como fallback, pero ya no es el camino
principal.

## Verificacion

Se ejecuto un smoke temporal con Qt WebEngine real y HTML minimo usando el
handler real de molsysviewer:

- la pagina hizo `fetch("molsysviewer://event?...")`;
- el handler Python recibio el evento;
- `QtMessageBridge.handle_frontend_event({"event": "ready"})` se ejecuto;
- `bridge.ready` paso a `True`.

Tambien se actualizaron tests unitarios para cubrir:

- los flags de registro de esquemas;
- el handler de eventos `molsysviewer://event`;
- el handler de payloads `molsysviewer-payload://payload/<id>`.

## Estado

Este documento es provisional. Registra el hallazgo y la correccion aplicada
para no perder el razonamiento.

Lo que queda por validar en Qt real ya no es el canal `ready` aislado, sino la
experiencia completa:

- carga molecular real;
- `structure_ready`;
- render visible con WebGL;
- menu contextual nativo;
- exportacion de pelicula sin bloqueo.
