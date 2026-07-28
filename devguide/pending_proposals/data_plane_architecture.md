# Propuesta: Arquitectura de "Plano de Datos" (Data Plane) sobre AnyWidget y Transporte Standalone

**Estado:** Propuesta de Arquitectura (2026-07-27)  
**Módulo:** `molsysviewer/js/src/`, `molsysviewer/viewer/` y `molsysviewer/standalone/`  
**Objetivo:** Diseñar un canal de transporte binario de alto rendimiento (*Data Plane*) para trayectorias y campos volumétricos masivos, separándolo del canal de control ligero de AnyWidget (*Control Plane*), y preparando la infraestructura para la versión Standalone de escritorio.

---

## Tabla de Contenido

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura: Control Plane vs Data Plane](#2-arquitectura-control-plane-vs-data-plane)
3. [Especificación del Protocolo Binario (Python ↔ TypeScript)](#3-especificación-del-protocolo-binario-python--typescript)
   * [3.1 Empaque en Python (Kernel / Backend)](#31-empaque-en-python-kernel--backend)
   * [3.2 Deserialización $O(1)$ en TypeScript (Frontend / Navegador)](#32-deserialización-o1-en-typescript-frontend--navegador)
4. [Problemas Resueltos](#4-problemas-resueltos)
5. [Limitantes Técnicas y Trade-offs](#5-limitantes-técnicas-y-trade-offs)
6. [Mejoras en la Experiencia de Usuario (Jupyter / Web)](#6-mejoras-en-la-experiencia-de-usuario-jupyter--web)
7. [Ventajas Estratégicas para la Versión Standalone (Desktop Qt / PySide6)](#7-ventajas-estratégicas-para-la-versión-standalone-desktop-qt--pyside6)
8. [Plan de Implementación y Fases](#8-plan-de-implementación-y-fases)

---

## 1. Resumen Ejecutivo

MolSysViewer se utiliza en entornos de cuaderno (JupyterLab, VS Code, Google Colab) e interfaces de escritorio. Mientras que **AnyWidget** proporciona una capa de abstracción para la compatibilidad universal con entornos Jupyter, su modelo predeterminado de sincronización de variables (*traitlets*) está optimizado para controles simples y no para datos científicos masivos ($100,000+$ frames de coordenadas o mallas volumétricas).

Esta propuesta define la separación de la capa de comunicación de MolSysViewer en dos planos desacoplados:
* **Control Plane (Plano de Control):** Basado en AnyWidget, dedicado exclusivamente a la inicialización, eventos de UI y sincronización de estado ligero.
* **Data Plane (Plano de Datos):** Basado en *Buffers Binarios Contiguos* (`Float32Array` / `Int32Array`) transmitidos asíncronamente sin pasar por la tabla de traits de ipywidgets.

---

## 2. Arquitectura: Control Plane vs Data Plane

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                MOLSYSVIEWER ARCHITECTURE                                │
├─────────────────────────────────────────┬───────────────────────────────────────────────┤
│    PLANO DE CONTROL (Control Plane)     │          PLANO DE DATOS (Data Plane)           │
│           via AnyWidget / Traitlets     │       via Custom Binary Streamer (Typed)      │
├─────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Mensajes JSON estructurados           │ • Buffers binarios contiguos en memoria       │
│ • Acciones de UI, botones, pestañas     │ • Float32Array (Coordenadas [x,y,z])          │
│ • Configuración de vistas y capas      │ • Int32Array (Índices, topología, deltas)     │
│ • Handshake y estado ligero             │ • Transmisión asíncrona no bloqueante         │
└─────────────────────────────────────────┴───────────────────────────────────────────────┘
```

### Principios de Diseño:
1. **AnyWidget como Plano de Control:** AnyWidget garantiza la portabilidad entre JupyterLab, VS Code, Colab y Voila. Se conserva para controlar la interfaz.
2. **Evasión de Traitlets:** Los payloads masivos no se asignan a atributos sincronizados en Python; se transmiten directamente como búferes binarios en llamadas `widget.send(msg, buffers=[...])`.
3. **Transparencia en Frontend:** El `ViewerController` en TypeScript abstrae la fuente del Data Plane, permitiendo que la misma interfaz funcione idénticamente en Jupyter y en la versión Standalone de escritorio.

---

## 3. Especificación del Protocolo Binario (Python ↔ TypeScript)

### 3.1 Empaque en Python (Kernel / Backend)

```python
import struct
import numpy as np

class BinaryDataStreamer:
    """Empaquetador de datos binarios contiguos para el Data Plane de MolSysViewer."""

    def __init__(self, widget):
        self.widget = widget

    def stream_coords_chunk(self, frame_start: int, coords_array: np.ndarray):
        """Envía un bloque de coordenadas contiguas sin serialización JSON.
        
        coords_array: shape (num_frames, num_atoms, 3), dtype float32/float64
        """
        # Asegurar formato Little-Endian de 32 bits (<f4)
        raw_bytes = coords_array.astype('<f4').tobytes()
        
        # Cabecera binaria de 8 bytes: [frame_start (u32), frame_count (u32)]
        header = struct.pack('<II', frame_start, coords_array.shape[0])
        
        # Enviar buffer crudo sin tocar la tabla de traits
        self.widget.send(
            {"op": "binary_data_chunk", "header_len": len(header)},
            buffers=[header + raw_bytes]
        )
```

### 3.2 Deserialización $O(1)$ en TypeScript (Frontend / Navegador)

```typescript
export interface BinaryHeader {
    frameStart: number;
    frameCount: number;
}

export class DataPlaneReceiver {
    public handleBinaryChunk(metadata: { header_len: number }, buffers: DataView[]): void {
        const rawBuffer = buffers[0].buffer;
        const headerView = new DataView(rawBuffer, 0, metadata.header_len);
        
        const frameStart = headerView.getUint32(0, true); // Little-endian
        const frameCount = headerView.getUint32(4, true);
        
        // Crear vista Float32Array directamente sobre el ArrayBuffer en microsegundos (Zero-Copy)
        const coordsView = new Float32Array(rawBuffer, metadata.header_len);
        
        // Alimentar el caché de la trayectoria en el Web Worker o motor Mol*
        this.trajectoryCache.setChunk(frameStart, frameCount, coordsView);
    }
}
```

---

## 4. Problemas Resueltos

1. **Eliminación del Peaje de Re-serialización:**
   Al usar `widget.send(msg, buffers=[...])`, los datos evaden la rutina `_separate_buffers` de ipywidgets, eliminando el sobrecosto de re-serialización de listas históricas (~17.5 ms por mensaje).
2. **Deserialización de Latencia Cero ($O(1)$ Zero-Copy):**
   TypeScript no parsea megabytes de texto JSON; genera una vista `Float32Array` envolviendo los bytes de memoria recibidos en microsegundos.
3. **Renderizado a 60 FPS Sostenidos:**
   La interfaz gráfica de Mol* se ejecuta sin caídas de frame (*UI freezes*) durante la reproducción continuada o desplazamiento del slider.
4. **Transmisión de Campos Volumétricos:**
   Permite transmitir mapas de densidad electrónica 3D, mapas de potencial electrostático o densidades de solvente calculadas por MolSysMT en formato de búfer binario crudo.

---

## 5. Limitantes Técnicas y Trade-offs

1. **Límite de Memoria V8 en Navegador:**
   * Almacenar 500,000 frames de coordenadas en memoria sin comprimir puede consumir > 2 GB de memoria RAM.
   * **Solución:** Implementar una memoria caché en anillo (*Ring Buffer / Least-Recently-Used Cache*) en TypeScript que mantenga en memoria solo los frames activos (ej. 5,000 frames) y solicite el resto al backend según sea necesario.
2. **Ordenación de Bytes (*Endianness*):**
   * Python debe forzar la ordenación Little-Endian (`<f4`) para evitar corrupción de datos al leer los TypedArrays en arquitecturas x86 o ARM64.
3. **Mapeo de Reconexiones en WebSockets:**
   * En caso de micro-desconexiones del servidor de Jupyter, cada chunk debe incluir un identificador secuencial (`chunk_id`) para reenviar paquetes omitidos.

---

## 6. Mejoras en la Experiencia de Usuario (Jupyter / Web)

* **Scrubbing Suave:** Desplazamiento continuo en trayectorias de más de 100,000 frames a 60 FPS.
* **Sincronización Host ↔ Popout:** El buffer binario recibido en la ventana principal de Jupyter puede compartirse con la ventana emergente Popout mediante `BroadcastChannel` o `SharedArrayBuffer` sin volver a descargarlo desde Python.

---

## 7. Ventajas Estratégicas para la Versión Standalone (Desktop Qt / PySide6)

En la versión Standalone de escritorio (basada en Python + PySide6 / QWebEngineView):

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   STANDALONE DESKTOP ARCHITECTURE                      │
├───────────────────────────────────┬────────────────────────────────────┤
│     PLANO DE CONTROL (PySide6)    │      PLANO DE DATOS (Local IPC)    │
│           via QWebChannel         │      via Shared Memory / Sockets   │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Menús nativos de sistema        │ • Transferencia Ultra-Rápida       │
│ • Diálogos de archivos y disco    │ • Mapeo Directo de Archivos SSD    │
│ • Eventos de ventana y atajos     │ • Cero Overhead de Red/WebSocket   │
└───────────────────────────────────┴────────────────────────────────────┘
```

1. **Desacoplamiento de Jupyter:**
   La versión Standalone no depende de AnyWidget ni de la infraestructura de cuadernos. Implementa su propio conector del `DataPlane` usando transporte de memoria compartida o IPC local en C++/Qt.
2. **Rendimiento de Aplicación de Escritorio:**
   Al ejecutarse localmente, el Plano de Datos Standalone puede mapear archivos de trayectoria de gigabytes directamente desde disco SSD a la memoria gráfica.
3. **Reutilización del Código Frontend:**
   El **95% del código TypeScript** (subpaneles de Studio, visualización Mol*, manipulación de geometrías) permanece intacto entre la versión Jupyter y la versión Standalone de escritorio.

---

## 8. Plan de Implementación y Fases

1. **Fase 1 (Prueba de Concepto en TypeScript):**
   * Crear la clase `BinaryDataStreamer` en Python y `DataPlaneReceiver` en TypeScript.
   * Validar el envío de chunks de 500 frames binarios usando `buffers=[memoryview]`.
2. **Fase 2 (Ring Buffer & Worker Cache):**
   * Implementar la memoria en anillo (LRU Cache) en TypeScript para gestionar trayectorias masivas sin agotar la RAM del navegador.
3. **Fase 3 (Conector Standalone IPC):**
   * Adaptar el `DataPlaneReceiver` para aceptar conectores de memoria compartida en la arquitectura Standalone PySide6/QWebEngineView.
