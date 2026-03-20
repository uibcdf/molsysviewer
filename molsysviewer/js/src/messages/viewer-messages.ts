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
    tag?: string;
    options?: {
        center?: [number, number, number];
        radius?: number;
        color?: number;
        alpha?: number;
        tag?: string;
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

export type AddLabelMessage = {
    op: "add_label";
    tag?: string;
    options?: {
        text?: string;
        atom_indices?: number[];
        tag?: string;
    };
};

export type UpdateLabelMessage = {
    op: "update_label";
    tag?: string;
    options?: {
        text?: string;
        atom_indices?: number[];
        tag?: string;
    };
};

export type AddDistanceMeasurementMessage = {
    op: "add_distance_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        tag?: string;
    };
};

export type AddAngleMeasurementMessage = {
    op: "add_angle_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        tag?: string;
    };
};

export type AddDihedralMeasurementMessage = {
    op: "add_dihedral_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        tag?: string;
    };
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
    /** Hint from Python side: true when the molsys has more than one structure. */
    multiple_structures?: boolean;
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

export type ResetCameraMessage = {
    op: "reset_camera";
};

export type ToggleFullscreenMessage = {
    op: "toggle_fullscreen";
    enable?: boolean;
};

export type ToggleBackgroundMessage = {
    op: "toggle_background";
    mode?: "light" | "dark";
};

export type ToggleSwingMessage = {
    op: "toggle_swing";
    enable?: boolean;
};

export type ToggleSpinMessage = {
    op: "toggle_spin";
    enable?: boolean;
};

export type StepTrajectoryMessage = {
    op: "step_trajectory";
    by?: number;
};

export type SetTrajectoryFrameMessage = {
    op: "set_trajectory_frame";
    index?: number;
};

export type SetTrajectoryPlaybackMessage = {
    op: "set_trajectory_playback";
    action?: "play" | "stop";
    fps?: number;
    step?: number;
    mode?: "loop" | "palindrome" | "once";
    direction?: "forward" | "backward";
};

export type SetAddonRuntimeSummaryMessage = {
    op: "set_addon_runtime_summary";
    addons?: string[];
    panel_specs?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        target?: string;
    }>;
    workbench_sections?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        target_panel?: string;
    }>;
};

export type LoadPdbIdMessage = {
    op: "load_pdb_id";
    pdb_id: string;
};

export type CreateRegionMessage = {
    op: "create_region";
    tag?: string;
    selection?: string;
    atom_indices?: number[];
    representation?: string;
    params?: Record<string, unknown>;
};

export type SetRegionRepresentationMessage = {
    op: "set_region_representation";
    tag?: string;
    representation?: string;
    preset?: string;
    user_preset?: any;
    params?: Record<string, unknown>;
};

export type ShowRegionMessage = {
    op: "show_region";
    tag?: string;
};

export type HideRegionMessage = {
    op: "hide_region";
    tag?: string;
};

export type DeleteRegionMessage = {
    op: "delete_region";
    tag?: string;
};

export type CreateLayerMessage = {
    op: "create_layer";
    tag?: string;
    kind?: string;
    meta?: Record<string, unknown>;
};

export type ShowLayerMessage = {
    op: "show_layer";
    tag?: string;
};

export type HideLayerMessage = {
    op: "hide_layer";
    tag?: string;
};

export type DeleteLayerMessage = {
    op: "delete_layer";
    tag?: string;
};

export type SetLayerTagMessage = {
    op: "set_layer_tag";
    tag?: string;
    new_tag: string;
};

export type SetGlobalRepresentationMessage = {
    op: "set_global_representation";
    representation?: string;
    preset?: string;
    user_preset?: any;
    params?: Record<string, unknown>;
};

export type ShowGlobalMessage = {
    op: "show_global";
    target?: "global" | "all";
};

export type HideGlobalMessage = {
    op: "hide_global";
    target?: "global" | "all";
};

export type ZoomMessage = {
    op: "zoom";
    atom_indices: number[];
    options?: {
        duration_ms?: number;
        extra_radius?: number;
        min_radius?: number;
    };
};

export type SetCameraSnapshotMessage = {
    op: "set_camera_snapshot";
    snapshot: any;
    duration_ms?: number;
};

export type RequestCameraSnapshotMessage = {
    op: "request_camera_snapshot";
};

export type RequestImageExportMessage = {
    op: "request_image_export";
    width?: number;
    height?: number;
    scale?: number;
    transparent?: boolean;
};

export type ClearActiveSelectionMessage = {
    op: "clear_active_selection";
};

export type SetActiveSelectionMessage = {
    op: "set_active_selection";
    atom_indices?: number[];
};

export type SaveSelectionMessage = {
    op: "save_selection";
    tag: string;
    source_kind?: string;
    element_level?: string;
    target_level?: string;
    items?: Record<string, unknown>[];
    atom_indices?: number[];
    group_indices?: number[];
    component_indices?: number[];
    chain_indices?: number[];
    molecule_indices?: number[];
    entity_indices?: number[];
};

export type SetSelectionTagMessage = {
    op: "set_selection_tag";
    tag?: string;
    new_tag: string;
};

export type DeleteSelectionMessage = {
    op: "delete_selection";
    tag?: string;
};

export type ClearSelectionsMessage = {
    op: "clear_selections";
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
    AddLabelMessage |
    UpdateLabelMessage |
    AddDistanceMeasurementMessage |
    AddAngleMeasurementMessage |
    AddDihedralMeasurementMessage |
    LoadStructureMessage |
    LoadMolSysPayloadMessage |
    LoadStructureFromUrlMessage |
    LoadPdbIdMessage |
    UpdateVisibilityMessage |
    ClearSceneMessage |
    ClearAllMessage |
    ClearByTagMessage |
    ResetCameraMessage |
    ToggleFullscreenMessage |
    ToggleBackgroundMessage |
    ToggleSwingMessage |
    ToggleSpinMessage |
    StepTrajectoryMessage |
    SetTrajectoryFrameMessage |
    SetTrajectoryPlaybackMessage |
    SetAddonRuntimeSummaryMessage |
    CreateRegionMessage |
    SetRegionRepresentationMessage |
    ShowRegionMessage |
    HideRegionMessage |
    DeleteRegionMessage |
    CreateLayerMessage |
    ShowLayerMessage |
    HideLayerMessage |
    DeleteLayerMessage |
    SetLayerTagMessage |
    SetGlobalRepresentationMessage |
    ShowGlobalMessage |
    HideGlobalMessage |
    ZoomMessage |
    SetCameraSnapshotMessage |
    RequestCameraSnapshotMessage |
    RequestImageExportMessage |
    ClearActiveSelectionMessage |
    SetActiveSelectionMessage |
    SaveSelectionMessage |
    SetSelectionTagMessage |
    DeleteSelectionMessage |
    ClearSelectionsMessage |
    Record<string, unknown>;
