// src/messages/viewer-messages.ts

import { PocketSurfaceOptions } from "../shapes/pocket-surface";
import {
    AnisotropyEllipsoidOptions,
    ChannelTubeOptions,
    DisplacementVectorOptions,
    NetworkLinkOptions,
    PharmacophoreOptions,
    PocketBlobOptions,
    TetrahedraOptions,
    TriangleFacesOptions,
} from "../shapes";
import { MolSysPayload } from "../plugin/structure";

export type AddSphereMessage = {
    op: "add_sphere";
    options?: {
        center?: [number, number, number];
        radius?: number;
        color?: number;
        alpha?: number;
    };
};

export type AddAlphaSphereSetMessage = {
    op: "add_alpha_sphere_set";
    options?: {
        alpha_spheres?: {
            centers: [number, number, number][];
            radii: number[];
            color?: number;
            alpha?: number;
        };
        atom_spheres?: {
            centers: [number, number, number][];
            radius?: number;
            color?: number;
            alpha?: number;
        };
        tag?: string;
    };
};

export type AddPocketSurfaceMessage = {
    op: "add_pocket_surface";
    options?: PocketSurfaceOptions;
};

export type AddPocketBlobMessage = {
    op: "add_pocket_blob";
    options?: PocketBlobOptions;
};

export type AddChannelTubeMessage = {
    op: "add_channel_tube";
    options?: ChannelTubeOptions;
};

export type AddAnisotropyEllipsoidsMessage = {
    op: "add_anisotropy_ellipsoids";
    options?: AnisotropyEllipsoidOptions;
};

export type AddPharmacophoreMessage = {
    op: "add_pharmacophore_features";
    options?: PharmacophoreOptions;
};

export type AddNetworkLinksMessage = {
    op: "add_network_links";
    options?: NetworkLinkOptions;
};

export type AddDisplacementVectorsMessage = {
    op: "add_displacement_vectors";
    options?: DisplacementVectorOptions;
};

export type AddTetrahedraMessage = {
    op: "add_tetrahedra";
    options?: TetrahedraOptions;
};

export type AddTriangleFacesMessage = {
    op: "add_triangle_faces";
    options?: TriangleFacesOptions;
};

export type LoadStructureMessage = {
    op: "load_structure_from_string" | "load_pdb_string";
    data?: string;
    pdb?: string;
    pdb_text?: string;
    format?: string;
    label?: string;
};

export type LoadMolSysPayloadMessage = {
    op: "load_molsys_payload";
    payload: MolSysPayload;
    label?: string;
};

export type LoadStructureFromUrlMessage = {
    op: "load_structure_from_url";
    url: string;
    format?: string;
    label?: string;
};

export type UpdateVisibilityMessage = {
    op: "update_visibility";
    options?: {
        visible_atom_indices?: number[];
    };
};

export type ClearSceneMessage = {
    op: "clear_scene";
    options?: {
        shapes?: boolean;
        styles?: boolean;
        labels?: boolean;
    };
};

export type ClearAllMessage = {
    op: "clear_all";
};

export type ClearByTagMessage = {
    op: "clear_shapes_by_tag";
    tag?: string;
};

export type LoadPdbIdMessage = {
    op: "load_pdb_id";
    pdb_id: string;
};

export type ViewerMessage =
    AddSphereMessage |
    AddAlphaSphereSetMessage |
    AddPocketSurfaceMessage |
    AddPocketBlobMessage |
    AddChannelTubeMessage |
    AddAnisotropyEllipsoidsMessage |
    AddPharmacophoreMessage |
    AddNetworkLinksMessage |
    AddDisplacementVectorsMessage |
    AddTetrahedraMessage |
    AddTriangleFacesMessage |
    LoadStructureMessage |
    LoadMolSysPayloadMessage |
    LoadStructureFromUrlMessage |
    LoadPdbIdMessage |
    UpdateVisibilityMessage |
    ClearSceneMessage |
    ClearAllMessage |
    ClearByTagMessage |
    Record<string, unknown>;
