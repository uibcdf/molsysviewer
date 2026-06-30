import { PluginContext } from "molstar/lib/mol-plugin/context";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Structure } from "molstar/lib/mol-model/structure";
import {
    addAnisotropyEllipsoidsFromPython,
    addChannelTubeFromPython,
    addDisplacementVectorsFromPython,
    addNetworkLinksFromPython,
    addPharmacophoreFromPython,
    addPocketBlobFromPython,
    addRingsFromPython,
    addTetrahedraFromPython,
    addTransparentSphereFromPython,
    addTransparentSpheresFromPython,
    addTriangleFacesFromPython,
    AnisotropyEllipsoidOptions,
    ChannelTubeOptions,
    RingsOptions,
    DisplacementVectorOptions,
    NetworkLinkOptions,
    PharmacophoreOptions,
    PocketBlobOptions,
    TetrahedraOptions,
    TransparentSphereSpec,
    TriangleFacesOptions,
    computeCentroidFromAtoms,
} from "../../shapes";
import { addPocketSurfaceFromPython, PocketSurfaceOptions } from "../../shapes/pocket-surface";
import {
    AddAlphaSphereSetMessage,
    AddAnisotropyEllipsoidsMessage,
    AddChannelTubeMessage,
    AddDisplacementVectorsMessage,
    AddHbondsMessage,
    AddNetworkLinksMessage,
    AddPharmacophoreMessage,
    AddPocketBlobMessage,
    AddPocketSurfaceMessage,
    AddScalarIsosurfaceMessage,
    AddRingsMessage,
    AddSphereMessage,
    AddTetrahedraMessage,
    AddTriangleFacesMessage,
} from "../../messages/viewer-messages";

type RegisterRefCallback = (ref: StateObjectRef | undefined, tag?: string) => void;

export interface ShapeHandlersContext {
    clearByTag: (tag: string) => Promise<void>;
    subscribeToTrajectoryState?: (cb: (frame: number) => void) => () => void;
    notifyShapeRenderStatus?: (status: TrajectoryShapeRenderStatus) => void;
}

export type TrajectoryShapeRenderStatus = {
    tag: string;
    op: string;
    frame: number;
    status: "rendered" | "missing-frame-data" | "missing-structure" | "empty-selection" | "invalid-indices" | "render-error";
    requested_atoms?: number;
    used_atoms?: number;
    reason?: string;
};

type TrajectoryShapeEntry = {
    op: string;
    baseOptions: Record<string, any>;
    framesCoords: Array<any | null>;
};

export class ShapeHandlers {
    private readonly trajectoryShapes = new Map<string, TrajectoryShapeEntry>();
    private trajectoryUnsub?: () => void;
    private currentFrame = 0;
    private frameUpdateInProgress = false;
    private readonly lastRenderStatus = new Map<string, TrajectoryShapeRenderStatus>();

    constructor(
        private plugin: PluginContext,
        private registerRef: RegisterRefCallback,
        private context?: ShapeHandlersContext,
    ) {}

    private ensureTrajectorySubscription() {
        if (this.trajectoryUnsub || !this.context?.subscribeToTrajectoryState) return;
        this.trajectoryUnsub = this.context.subscribeToTrajectoryState((frame) => {
            if (frame !== this.currentFrame) {
                this.currentFrame = frame;
                void this.applyFrame(frame);
            }
        });
    }

    private storeTrajectoryShape(tag: string, op: string, baseOptions: Record<string, any>, framesCoords: Array<any | null>) {
        this.trajectoryShapes.set(tag, { op, baseOptions, framesCoords });
        this.ensureTrajectorySubscription();
    }

    private makeStatus(
        tag: string,
        op: string,
        frame: number,
        status: TrajectoryShapeRenderStatus["status"],
        details: Partial<Omit<TrajectoryShapeRenderStatus, "tag" | "op" | "frame" | "status">> = {}
    ): TrajectoryShapeRenderStatus {
        return { tag, op, frame, status, ...details };
    }

    private emitRenderStatus(status: TrajectoryShapeRenderStatus) {
        const previous = this.lastRenderStatus.get(status.tag);
        if (
            previous &&
            previous.status === status.status &&
            previous.requested_atoms === status.requested_atoms &&
            previous.used_atoms === status.used_atoms &&
            previous.reason === status.reason
        ) {
            return;
        }
        this.lastRenderStatus.set(status.tag, status);
        this.context?.notifyShapeRenderStatus?.(status);
    }

    private async applyFrame(frame: number) {
        if (this.frameUpdateInProgress) return;
        this.frameUpdateInProgress = true;
        try {
            for (const [tag, entry] of this.trajectoryShapes) {
                const fc = entry.framesCoords[frame] ?? null;
                await this.context!.clearByTag(tag);
                if (fc === null) {
                    this.emitRenderStatus(this.makeStatus(tag, entry.op, frame, "missing-frame-data"));
                    continue;
                }
                try {
                    const status = await this.renderTrajectoryFrame(tag, entry.op, entry.baseOptions, fc, frame);
                    if (status) this.emitRenderStatus(status);
                } catch (err) {
                    const reason = err instanceof Error ? err.message : String(err);
                    this.emitRenderStatus(this.makeStatus(tag, entry.op, frame, "render-error", { reason }));
                }
            }
        } finally {
            this.frameUpdateInProgress = false;
        }
    }

    private async renderTrajectoryFrame(
        tag: string,
        op: string,
        baseOptions: any,
        frameCoords: any,
        frame: number = this.currentFrame
    ): Promise<TrajectoryShapeRenderStatus> {
        if (op === "add_sphere_from_atoms") {
            const requested = Array.isArray(frameCoords) ? frameCoords.length : 0;
            const structureRef = this.plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
            const structure = structureRef?.cell.obj?.data as Structure | undefined;
            if (!structure) {
                return this.makeStatus(tag, op, frame, "missing-structure", { requested_atoms: requested, used_atoms: 0 });
            }
            const centroid = computeCentroidFromAtoms(structure, frameCoords);
            if (!centroid.ok) {
                return this.makeStatus(tag, op, frame, centroid.reason, {
                    requested_atoms: centroid.requested,
                    used_atoms: centroid.used,
                });
            }
            const ref = await addTransparentSphereFromPython(this.plugin, {
                center: centroid.center,
                radius: baseOptions.radius ?? 10,
                color: baseOptions.color ?? 0x00ff00,
                alpha: baseOptions.alpha ?? 0.4,
            });
            this.registerRef(ref, tag);
            return this.makeStatus(tag, op, frame, "rendered", {
                requested_atoms: centroid.requested,
                used_atoms: centroid.used,
            });
        } else if (op === "add_sphere") {
            const ref = await addTransparentSphereFromPython(this.plugin, {
                center: frameCoords as [number, number, number],
                radius: baseOptions.radius ?? 10,
                color: baseOptions.color ?? 0x00ff00,
                alpha: baseOptions.alpha ?? 0.4,
            });
            this.registerRef(ref, tag);
        } else if (op === "add_triangle_faces") {
            const ref = await addTriangleFacesFromPython(this.plugin, { ...baseOptions, vertices: frameCoords });
            this.registerRef(ref, tag);
        } else if (op === "add_channel_tube") {
            const ref = await addChannelTubeFromPython(this.plugin, { ...baseOptions, centers: frameCoords });
            if (Array.isArray(ref)) ref.forEach(r => this.registerRef(r, tag));
            else if (ref) this.registerRef(ref, tag);
        } else if (op === "add_network_links") {
            const ref = await addNetworkLinksFromPython(this.plugin, { ...baseOptions, coordinate_pairs: frameCoords });
            this.registerRef(ref as any, tag);
        } else if (op === "add_hbonds") {
            const requested = Array.isArray(frameCoords) ? frameCoords.length * 2 : 0;
            const structureRef = this.plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
            const structure = structureRef?.cell.obj?.data as Structure | undefined;
            if (!structure) {
                return this.makeStatus(tag, op, frame, "missing-structure", { requested_atoms: requested, used_atoms: 0 });
            }
            const ref = await addNetworkLinksFromPython(this.plugin, { ...baseOptions, mode: "atom-indices", atom_pairs: frameCoords });
            this.registerRef(ref as any, tag);
            return this.makeStatus(tag, op, frame, "rendered", { requested_atoms: requested, used_atoms: requested });
        }
        return this.makeStatus(tag, op, frame, "rendered");
    }

    async addSphere(msg: AddSphereMessage) {
        const options = msg.options ?? {};
        const tag = options.tag ?? msg.tag;
        
        if (options.structures_atom_indices) {
            const baseOptions = { ...options };
            delete (baseOptions as any).structures_atom_indices;
            this.storeTrajectoryShape(tag!, "add_sphere_from_atoms", baseOptions, options.structures_atom_indices);
            const fc = options.structures_atom_indices[this.currentFrame] ?? null;
            if (fc !== null) {
                const structureRef = this.plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
                const structure = structureRef?.cell.obj?.data as Structure | undefined;
                if (structure) {
                    const centroid = computeCentroidFromAtoms(structure, fc);
                    if (centroid.ok) {
                        const ref = await addTransparentSphereFromPython(this.plugin, {
                            center: centroid.center,
                            radius: options.radius ?? 10,
                            color: options.color ?? 0x00ff00,
                            alpha: options.alpha ?? 0.4,
                        });
                        this.registerRef(ref, tag);
                        this.emitRenderStatus(this.makeStatus(tag!, "add_sphere_from_atoms", this.currentFrame, "rendered", {
                            requested_atoms: centroid.requested,
                            used_atoms: centroid.used,
                        }));
                    } else {
                        this.emitRenderStatus(this.makeStatus(tag!, "add_sphere_from_atoms", this.currentFrame, centroid.reason, {
                            requested_atoms: centroid.requested,
                            used_atoms: centroid.used,
                        }));
                    }
                } else {
                    this.emitRenderStatus(this.makeStatus(tag!, "add_sphere_from_atoms", this.currentFrame, "missing-structure", {
                        requested_atoms: Array.isArray(fc) ? fc.length : 0,
                        used_atoms: 0,
                    }));
                }
            }
            return;
        }
        
        if (options.structures_coords) {
            const baseOptions = { ...options };
            delete (baseOptions as any).structures_coords;
            this.storeTrajectoryShape(tag!, "add_sphere", baseOptions, options.structures_coords);
            const fc = options.structures_coords[this.currentFrame] ?? null;
            if (fc !== null) {
                const ref = await addTransparentSphereFromPython(this.plugin, {
                    center: fc as [number, number, number],
                    radius: options.radius ?? 10,
                    color: options.color ?? 0x00ff00,
                    alpha: options.alpha ?? 0.4,
                });
                this.registerRef(ref, tag);
                this.emitRenderStatus(this.makeStatus(tag!, "add_sphere", this.currentFrame, "rendered"));
            }
            return;
        }
        
        let center = options.center ?? [0, 0, 0];
        if (options.atom_indices) {
            const structureRef = this.plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
            const structure = structureRef?.cell.obj?.data as Structure | undefined;
            const resolvedCenter = structure ? computeCentroidFromAtoms(structure, options.atom_indices) : null;
            if (resolvedCenter === null || !resolvedCenter.ok) {
                console.warn("[MolSysViewer] addSphere: could not compute centroid for atom_indices");
                return;
            }
            center = resolvedCenter.center;
        }
        
        const ref = await addTransparentSphereFromPython(this.plugin, {
            center,
            radius: options.radius ?? 10,
            color: options.color ?? 0x00ff00,
            alpha: options.alpha ?? 0.4,
        });
        this.registerRef(ref, tag);
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

    async addScalarIsosurface(msg: AddScalarIsosurfaceMessage) {
        const options = msg.options ?? {};
        if (!options.centers || !options.radii || options.centers.length === 0 || options.radii.length === 0) {
            console.warn("[MolSysViewer] add_scalar_isosurface without centers or radii");
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
            console.error("[MolSysViewer] Error creando scalar isosurface", err);
        }
    }

    async addChannelTube(msg: AddChannelTubeMessage) {
        const options = msg.options ?? {};
        if (options.structures_coords) {
            const tag = options.tag;
            const baseOptions = { ...options };
            delete (baseOptions as any).structures_coords;
            this.storeTrajectoryShape(tag!, "add_channel_tube", baseOptions, options.structures_coords);
            const fc = options.structures_coords[this.currentFrame] ?? null;
            if (fc !== null) {
                try {
                    const ref = await addChannelTubeFromPython(this.plugin, { ...baseOptions, centers: fc });
                    if (Array.isArray(ref)) ref.forEach(r => this.registerRef(r, tag));
                    else if (ref) this.registerRef(ref, tag);
                } catch (err) {
                    console.error("[MolSysViewer] Error creando channel tube (trajectory frame)", err);
                }
            }
            return;
        }
        if (!options.centers || !options.radii || options.centers.length < 2 || options.radii.length < 2) {
            console.warn("[MolSysViewer] add_channel_tube requires at least two centers and radii");
            return;
        }
        try {
            const ref = await addChannelTubeFromPython(this.plugin, options);
            if (Array.isArray(ref)) ref.forEach(r => this.registerRef(r, options.tag));
            else if (ref) this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando channel tube", err);
        }
    }

    async addRings(msg: AddRingsMessage) {
        const options: RingsOptions = msg.options ?? {};
        if (
            !options.centers || !options.normals || !options.radii ||
            options.centers.length === 0
        ) {
            console.warn("[MolSysViewer] add_rings requires centers, normals and radii");
            return;
        }
        try {
            const ref = await addRingsFromPython(this.plugin, options);
            if (ref) this.registerRef(ref, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando rings", err);
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
        if (options.structures_coords) {
            const tag = options.tag;
            const baseOptions = { ...options };
            delete (baseOptions as any).structures_coords;
            this.storeTrajectoryShape(tag!, "add_network_links", baseOptions, options.structures_coords);
            const fc = options.structures_coords[this.currentFrame] ?? null;
            if (fc !== null) {
                try {
                    const ref = await addNetworkLinksFromPython(this.plugin, { ...baseOptions, coordinate_pairs: fc });
                    this.registerRef(ref as any, tag);
                } catch (err) {
                    console.error("[MolSysViewer] Error creando network links (trajectory frame)", err);
                }
            }
            return;
        }
        try {
            const ref = await addNetworkLinksFromPython(this.plugin, options);
            this.registerRef(ref as any, options.tag);
        } catch (err) {
            console.error("[MolSysViewer] Error creando network links", err);
        }
    }

    async addHbonds(msg: AddHbondsMessage) {
        const options = msg.options;
        if (!options?.structures_atom_pairs?.length) {
            console.warn("[MolSysViewer] add_hbonds: missing structures_atom_pairs");
            return;
        }
        const tag = options.tag;
        const { structures_atom_pairs, ...baseOptions } = options;
        this.storeTrajectoryShape(tag!, "add_hbonds", baseOptions, structures_atom_pairs);
        const fc = structures_atom_pairs[this.currentFrame] ?? null;
        if (fc !== null && fc.length > 0) {
            try {
                const ref = await addNetworkLinksFromPython(this.plugin, {
                    ...baseOptions,
                    mode: "atom-indices",
                    atom_pairs: fc,
                });
                this.registerRef(ref as any, tag);
            } catch (err) {
                console.error("[MolSysViewer] Error creando hbonds", err);
            }
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
        if (options.structures_coords) {
            const tag = options.tag;
            const baseOptions = { ...options };
            delete (baseOptions as any).structures_coords;
            this.storeTrajectoryShape(tag!, "add_triangle_faces", baseOptions, options.structures_coords);
            const fc = options.structures_coords[this.currentFrame] ?? null;
            if (fc !== null) {
                try {
                    const ref = await addTriangleFacesFromPython(this.plugin, { ...baseOptions, vertices: fc });
                    this.registerRef(ref, tag);
                } catch (err) {
                    console.error("[MolSysViewer] Error creando triangle faces (trajectory frame)", err);
                }
            }
            return;
        }
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
