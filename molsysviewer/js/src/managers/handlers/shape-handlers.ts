import { PluginContext } from "molstar/lib/mol-plugin/context";
import { StateObjectRef } from "molstar/lib/mol-state";
import {
    addAnisotropyEllipsoidsFromPython,
    addChannelTubeFromPython,
    addDisplacementVectorsFromPython,
    addNetworkLinksFromPython,
    addPharmacophoreFromPython,
    addPocketBlobFromPython,
    addTetrahedraFromPython,
    addTransparentSphereFromPython,
    addTransparentSpheresFromPython,
    addTriangleFacesFromPython,
    AnisotropyEllipsoidOptions,
    ChannelTubeOptions,
    DisplacementVectorOptions,
    NetworkLinkOptions,
    PharmacophoreOptions,
    PocketBlobOptions,
    TetrahedraOptions,
    TransparentSphereSpec,
    TriangleFacesOptions,
} from "../../shapes";
import { addPocketSurfaceFromPython, PocketSurfaceOptions } from "../../shapes/pocket-surface";
import {
    AddAlphaSphereSetMessage,
    AddAnisotropyEllipsoidsMessage,
    AddChannelTubeMessage,
    AddDisplacementVectorsMessage,
    AddNetworkLinksMessage,
    AddPharmacophoreMessage,
    AddPocketBlobMessage,
    AddPocketSurfaceMessage,
    AddSphereMessage,
    AddTetrahedraMessage,
    AddTriangleFacesMessage,
} from "../../messages/viewer-messages";

type RegisterRefCallback = (ref: StateObjectRef, tag?: string) => void;

export class ShapeHandlers {
    constructor(private plugin: PluginContext, private registerRef: RegisterRefCallback) {}

    async addSphere(msg: AddSphereMessage) {
        const options = msg.options ?? {};
        const ref = await addTransparentSphereFromPython(this.plugin, {
            center: options.center ?? [0, 0, 0],
            radius: options.radius ?? 10,
            color: options.color ?? 0x00ff00,
            alpha: options.alpha ?? 0.4,
        });
        this.registerRef(ref, options.tag ?? msg.tag);
    }

    async addAlphaSphereSet(msg: AddAlphaSphereSetMessage) {
        const options = msg.options;
        if (!options?.alpha_spheres?.centers || !options.alpha_spheres.radii) {
            console.warn("[MolSysViewer] add_alpha_sphere_set missing alpha_spheres");
            return;
        }

        const centers = options.alpha_spheres.centers;
        const radii = options.alpha_spheres.radii;
        if (!Array.isArray(centers) || !Array.isArray(radii) || centers.length !== radii.length || centers.length === 0) {
            console.warn("[MolSysViewer] add_alpha_sphere_set inconsistent data");
            return;
        }

        const alphaColor = options.alpha_spheres.color ?? 0x00ff00;
        const alphaAlpha = options.alpha_spheres.alpha ?? 0.3;
        const alphaSpecs: TransparentSphereSpec[] = centers.map((c, i) => ({
            center: [c[0], c[1], c[2]],
            radius: radii[i],
            color: alphaColor,
            alpha: alphaAlpha,
        }));

        const tag = options.tag ?? "molsysviewer:alpha-spheres";
        const alphaRef = await addTransparentSpheresFromPython(this.plugin, alphaSpecs, alphaAlpha, tag);
        this.registerRef(alphaRef, tag);

        if (options.atom_spheres?.centers && options.atom_spheres.centers.length > 0) {
            const atomRadius = options.atom_spheres.radius ?? 1.0;
            const atomColor = options.atom_spheres.color ?? 0x0000ff;
            const atomAlpha = options.atom_spheres.alpha ?? 0.5;
            const atomSpecs: TransparentSphereSpec[] = options.atom_spheres.centers.map(c => ({
                center: [c[0], c[1], c[2]],
                radius: atomRadius,
                color: atomColor,
                alpha: atomAlpha,
            }));
            const atomRef = await addTransparentSpheresFromPython(this.plugin, atomSpecs, atomAlpha, tag);
            this.registerRef(atomRef, tag);
        }
    }

    async addPocketSurface(msg: AddPocketSurfaceMessage) {
        const options = msg.options ?? ({} as PocketSurfaceOptions);
        if (!Array.isArray(options.atom_indices) || options.atom_indices.length === 0) {
            console.warn("[MolSysViewer] add_pocket_surface without atom_indices");
            return;
        }
        try {
            const ref = await addPocketSurfaceFromPython(this.plugin, options);
            if (Array.isArray(ref)) {
                ref.forEach(r => this.registerRef(r, options.tag));
            } else {
                this.registerRef(ref, options.tag);
            }
        } catch (err) {
            console.error("[MolSysViewer] Error creando pocket surface", err);
        }
    }

    async addPocketBlob(msg: AddPocketBlobMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.radii || options.centers.length === 0 || options.radii.length === 0) {
            console.warn("[MolSysViewer] add_pocket_blob without centers or radii");
            return;
        }
        try {
            const ref = await addPocketBlobFromPython(this.plugin, options);
            if (Array.isArray(ref)) {
                ref.forEach(r => this.registerRef(r, options.tag));
            } else {
                this.registerRef(ref, options.tag);
            }
        } catch (err) {
            console.error("[MolSysViewer] Error creando pocket blob", err);
        }
    }

    async addChannelTube(msg: AddChannelTubeMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.radii || options.centers.length < 2 || options.radii.length < 2) {
            console.warn("[MolSysViewer] add_channel_tube requires at least two centers and radii");
            return;
        }
        try {
            const ref = await addChannelTubeFromPython(this.plugin, options);
            this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando channel tube", err);
        }
    }

    async addAnisotropyEllipsoids(msg: AddAnisotropyEllipsoidsMessage) {
        const options = msg.options ?? {};
        if (!options.centers && !options.atom_indices) {
            console.warn("[MolSysViewer] add_anisotropy_ellipsoids requires centers or atom_indices");
            return;
        }
        try {
            const ref = await addAnisotropyEllipsoidsFromPython(this.plugin, options);
            this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando anisotropy ellipsoids", err);
        }
    }

    async addPharmacophore(msg: AddPharmacophoreMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.kinds || options.centers.length === 0 || options.kinds.length !== options.centers.length) {
            console.warn("[MolSysViewer] add_pharmacophore_features requires centers and kinds of same length");
            return;
        }
        try {
            const ref = await addPharmacophoreFromPython(this.plugin, options);
            this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando pharmacophore features", err);
        }
    }

    async addNetworkLinks(msg: AddNetworkLinksMessage) {
        const options = msg.options ?? {};
        try {
            const ref = await addNetworkLinksFromPython(this.plugin, options);
            this.registerRef(ref as any, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando network links", err);
        }
    }

    async addDisplacementVectors(msg: AddDisplacementVectorsMessage) {
        const options = msg.options ?? {};
        if (!options.vectors || options.vectors.length === 0) {
            console.warn("[MolSysViewer] add_displacement_vectors without vectors");
            return;
        }
        try {
            const ref = await addDisplacementVectorsFromPython(this.plugin, options);
            this.registerRef(ref as any, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando displacement vectors", err);
        }
    }

    async addTetrahedra(msg: AddTetrahedraMessage) {
        const options = msg.options ?? {};
        if (!options.tetraCoords && !options.tetra_coords && !options.atomQuads && !options.atom_quads) {
            console.warn("[MolSysViewer] add_tetrahedra without tetraCoords or atom_quads");
            return;
        }
        try {
            const ref = await addTetrahedraFromPython(this.plugin, options);
            this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando tetrahedra", err);
        }
    }

    async addTriangleFaces(msg: AddTriangleFacesMessage) {
        const options = msg.options ?? {};
        if (!options.vertices && !options.atom_triplets && !options.atomTriplets) {
            console.warn("[MolSysViewer] add_triangle_faces without vertices or atom_triplets");
            return;
        }
        try {
            const ref = await addTriangleFacesFromPython(this.plugin, options);
            this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando triangle faces", err);
        }
    }
}
