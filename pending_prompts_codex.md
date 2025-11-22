* Implementar en `molsysviewer/js/src/shapes.ts` un generador de grid volumétrico a partir de centros/radios de alpha-esferas (p. ej., densidad gaussiana) y extraer una
  isosuperficie con las utilidades de geometría de Mol\*.
* Permitir parámetros de resolución de grid, umbral de iso, suavizado y color mapping por propiedad opcional.
* Incluir un transformador `PocketBlob3D` y exponer una API Python `add_pocket_blob(...)` que reciba las alpha-esferas (centros y radios) y opciones de estilo.
-------------------
* Añadir en `molsysviewer/js/src/shapes.ts` un constructor de malla que interpole los centros ordenados de alpha-esferas de un canal y genere cilindros/toros segmentados (sweep) con radio configurable por punto.
* Proveer opciones para color por distancia al solvente o por segmento, y un control de suavizado (spline) de la trayectoria.
* Exponer un transformador `ChannelTube3D` y su API Python `add_channel_tube(...)` que consuma las rutas de TopoMT.


* Implementar en `molsysviewer/js/src/shapes.ts` un constructor que genere elipsoides orientados a partir de autovalores/autovectores por átomo, o discos planos si solo se necesita dirección principal.
* Añadir el transformador `AnisotropyEllipsoids3D` con parámetros: centros (átomos/coords), matrices/tensores o autovalores+autovectores, escala global, límite de excentricidad y esquema de color por anisotropía.
* Proveer la API Python para enviar tensores/evects desde los cálculos ANM y controlar transparencia/colores.

Extender `shapes.ts` con parámetros opcionales en los nuevos shapes (triángulos/tetraedros) para dibujar líneas de
arista (wireframe sobre el mismo mesh o Shape separado con `MeshBuilder.addCylinder`) y flechas de normales por cara
(cono+cilindro). Documentar los flags en las APIs Python correspondientes (`add_triangle_faces`, `add_tetrahedra`) para
activar/desactivar contornos y normales y ajustar colores/longitudes.
