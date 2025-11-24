
• Ideas de formas y capacidades que sumarían valor para TopoMT y PharmacophoreMT:

  - Blobs/pockets enriquecidos: usar mallas isosuperficie ya implementadas para pockets, pero añadiendo:
      1. canales con grosor variable por distancia al solvente,
      2. mapas de color por propiedad (hidrofobicidad, carga, energía) sobre la superficie,
      3. clip interactivo por “mouths” múltiples.
  - Glyphs farmacofóricos:
      - Esferas y discos codificados por tipo (donor, acceptor, aromatic, hydrophobe, positive/negative ionizable) con leyenda y colores/patterns estandarizados.
      - Flechas cónicas para direccionalidad de aceptores/donors.
      - Anillos planos (discos o tori) para aromáticos.
      - Elipsoides para anisotropía de interacciones (p.ej. dirección preferente de enlace de hidrógeno).
  - Objetos de campo/escalares:
      - Grid volumétrico de propiedades (p.ej., mapas de energía o campos electrostáticos) con cortes por plano y paletas ajustables.
      - Iso-contornos múltiples del mismo campo (multi-iso) para ver umbrales de accesibilidad o energía.
  - Geometría topográfica:
      - Curvas de “ridge/valley” de la superficie del pocket derivadas de TopoMT (líneas o tubos con gradiente).
      - Discos/bandas para “mouths” con normales visibles y radio según apertura.
  - Vínculos y anotaciones:
      - Segmentos etiquetados entre features farmacofóricas y sitios de superficie (ligaduras virtuales, constraints).
      - Labels 3D con offset y fondo semitransparente para IDs de pocket, energía, tipo de feature.
  - Gestión de grupos/tagging:
      - Tags obligatorios para cada entidad (pocket_id, feature_id) y métodos clear(tag=…), set_visibility(tag, on/off) para alternar TopoMT vs PharmacophoreMT overlays.
  - Interacción y filtros:
      - Selección por rectángulo/volumen para ocultar/mostrar subconjuntos de shapes (p.ej. solo features dentro de cierto pocket).
      - Control global de transparencia por grupo (todas las features farmacofóricas vs. todas las mallas de pocket).
  - Export/inspección:
      - Serialización de shapes a JSON (centers, radios, colores, tags) para que TopoMT/PharmacophoreMT puedan guardar escenas reproducibles.


