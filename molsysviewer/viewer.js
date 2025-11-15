async function addTransparentSphere(viewer, options = {}) {
  const {
    center = [0, 0, 0],
    radius = 10.0,
    color = 0x00ff00,
    alpha = 0.4,
    label = "transparent-sphere",
  } = options;

  const mol = window.molstar;
  if (!mol) {
    console.error("MolSysViewer: molstar global not found.");
    return;
  }

  const {
    MeshBuilder,
    Mesh,
    Mat4,
    Vec3,
    Sphere,
    Shape,
    ShapeRepresentation,
  } = mol;

  if (!MeshBuilder || !Sphere || !Shape || !ShapeRepresentation) {
    console.error(
      "MolSysViewer: faltan piezas de Mol* para shapes. Mira window.molstar en la consola para ajustar nombres.",
      mol,
    );
    return;
  }

  // 1. Construir la malla de la esfera
  const builderState = MeshBuilder.createState(128, 64);
  const t = Mat4.identity();
  const v = Vec3.zero();
  const primitiveSphere = Sphere(1); // radio base 1, escalamos por Mat4

  Vec3.set(v, center[0], center[1], center[2]);
  Mat4.identity(t);
  Mat4.setTranslation(t, v);
  Mat4.scaleUniformly(t, t, radius);

  MeshBuilder.addPrimitive(builderState, t, primitiveSphere);
  const mesh = MeshBuilder.getMesh(builderState);

  // 2. Crear el Shape
  const c = mol.Color(color);
  const getColor = () => c;
  const getSize = () => 1;
  const getLabel = () => label;

  const shape = Shape.create(label, {}, mesh, getColor, getSize, getLabel);

  // 3. Crear la representación de Shape y añadirla al canvas3d
  const repr = ShapeRepresentation(
    async (ctx, data, props, existingShape) => {
      // data es el shape; ignoramos props en este test
      return shape;
    },
    Mesh.Utils,
  );

  const reprProps = {
    alpha,
  };

  // Ejecutar la tarea de creación/actualización
  await repr.createOrUpdate(reprProps, shape).run();

  const canvas3d = viewer.plugin?.canvas3d;
  if (!canvas3d) {
    console.warn("MolSysViewer: canvas3d no disponible.");
    return;
  }

  canvas3d.add(repr);
  canvas3d.requestCameraReset();
}


export async function render({ model, el }) {
  console.log("MolSysViewer: render called", { model, el });

  // Limpiar contenido previo
  el.innerHTML = "";

  // Contenedor explícito para Mol*
  const container = document.createElement("div");
  container.style.position = "relative";
  container.style.width = "100%";
  container.style.height = "500px";
  container.style.border = "1px solid #ccc";
  el.appendChild(container);

  // Cargar Mol* desde CDN (JS + CSS) si no está ya cargado
  async function loadMolstar() {
    if (window.molstar) {
      return window.molstar;
    }

    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src =
        "https://cdn.jsdelivr.net/npm/molstar@latest/build/viewer/molstar.js";
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Failed to load Mol* script"));
      document.head.appendChild(script);

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.type = "text/css";
      link.href =
        "https://cdn.jsdelivr.net/npm/molstar@latest/build/viewer/molstar.css";
      document.head.appendChild(link);
    });

    return window.molstar;
  }

  const molstar = await loadMolstar();

  // Crear el viewer de Mol* dentro del contenedor
  const viewer = await molstar.Viewer.create(container, {
    layoutIsExpanded: false,
    layoutShowControls: false,
    layoutShowRemoteState: false,
    layoutShowSequence: false,
    layoutShowLog: false,
    layoutShowLeftPanel: false,
    viewportShowExpand: true,
  });

  // Utilidad: inferir formato a partir de la URL si es posible
  function inferFormatFromUrl(url) {
    const lower = url.toLowerCase();
    if (lower.endsWith(".cif") || lower.endsWith(".mmcif")) {
      return "mmcif";
    }
    if (lower.endsWith(".pdb") || lower.endsWith(".ent")) {
      return "pdb";
    }
    return "pdb"; // por defecto
  }

  // Escuchar mensajes desde Python
  model.on("msg:custom", async (msg) => {
    if (!msg || typeof msg.op !== "string") {
      return;
    }

    console.log("MolSysViewer: received message", msg);

    // Test de vida: carga 7bv2 por ID
    if (msg.op === "test_sphere") {
      await viewer.loadPdb("7bv2");
    }

    // Cargar estructura desde string (PDB o mmCIF)
    if (msg.op === "load_structure_from_string") {
      const format = msg.format || "pdb";
      const data = msg.data;
      const label =
        msg.label ||
        (format === "pdb"
          ? "PDB from MolSysViewer"
          : "Structure from MolSysViewer");

      if (!data || typeof data !== "string") {
        console.warn(
          "MolSysViewer: 'data' vacío o no-string en load_structure_from_string",
        );
        return;
      }

      try {
        if (format === "pdb") {
          await viewer.loadStructureFromData(data, "pdb", { dataLabel: label });
        } else if (format === "mmcif") {
          await viewer.loadStructureFromData(data, "mmcif", {
            dataLabel: label,
          });
        } else {
          console.warn(
            `MolSysViewer: formato no soportado todavía: ${format}`,
          );
          return;
        }

        if (viewer.plugin.canvas3d) {
          viewer.plugin.canvas3d.requestCameraReset();
        }
      } catch (e) {
        console.error(
          "MolSysViewer: error cargando estructura desde string",
          e,
        );
      }
    }

    // Cargar estructura desde URL remota
    if (msg.op === "load_structure_from_url") {
      const url = msg.url;
      if (!url || typeof url !== "string") {
        console.warn(
          "MolSysViewer: 'url' vacío o no-string en load_structure_from_url",
        );
        return;
      }

      let format = msg.format || "auto";
      const label = msg.label || `From URL: ${url}`;

      if (format === "auto" || !format) {
        format = inferFormatFromUrl(url);
      }

      try {
        const response = await fetch(url);
        if (!response.ok) {
          console.error(
            `MolSysViewer: error HTTP ${response.status} al descargar ${url}`,
          );
          return;
        }
        const text = await response.text();

        if (format === "pdb") {
          await viewer.loadStructureFromData(text, "pdb", { dataLabel: label });
        } else if (format === "mmcif") {
          await viewer.loadStructureFromData(text, "mmcif", {
            dataLabel: label,
          });
        } else {
          console.warn(
            `MolSysViewer: formato desde URL no soportado todavía: ${format}`,
          );
          return;
        }

        if (viewer.plugin.canvas3d) {
          viewer.plugin.canvas3d.requestCameraReset();
        }
      } catch (e) {
        console.error(
          "MolSysViewer: error al cargar estructura desde URL",
          e,
        );
      }
    }

    if (msg.op === "test_transparent_sphere") {
      try {
        await addTransparentSphere(viewer, msg.options || {});
      } catch (e) {
        console.error("MolSysViewer: error en test_transparent_sphere", e);
      }
    }

    // Limpiar escena
    if (msg.op === "clear") {
      try {
        if (typeof viewer.clear === "function") {
          await viewer.clear();
        } else if (
          viewer.plugin &&
          typeof viewer.plugin.clear === "function"
        ) {
          await viewer.plugin.clear();
        }
      } catch (e) {
        console.warn("MolSysViewer: error al limpiar la escena", e);
      }
    }
  });

  // Notificar que el viewer está listo y puede recibir mensajes
  model.send({ event: "ready" });
}

