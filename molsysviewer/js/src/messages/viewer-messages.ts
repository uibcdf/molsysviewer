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
        layer_tag?: string;
        structures_coords?: Array<[number, number, number] | null>;
    };
};

export type UpdateSphereMessage = {
    op: "update_sphere";
    tag?: string;
    options?: {
        center?: [number, number, number];
        radius?: number;
        color?: number;
        alpha?: number;
        tag?: string;
        layer_tag?: string;
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

export type AddHbondsMessage = {
    op: "add_hbonds";
    options?: {
        structures_atom_pairs: Array<[number, number][] | null>;
        tag?: string;
        layer_tag?: string;
        radii?: number[];
        colors?: number[];
        alpha?: number;
        radial_segments?: number;
    };
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

export type LabelStyle = {
    color?: string;
    size_em?: number;
    background?: boolean;
    background_opacity?: number;
};

export type AddLabelMessage = {
    op: "add_label";
    tag?: string;
    options?: {
        text?: string;
        atom_indices?: number[];
        tag?: string;
        layer_tag?: string;
        style?: LabelStyle;
    };
};

export type UpdateLabelMessage = {
    op: "update_label";
    tag?: string;
    options?: {
        text?: string;
        atom_indices?: number[];
        tag?: string;
        style?: LabelStyle;
    };
};

export type AddDistanceMeasurementMessage = {
    op: "add_distance_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        endpoint_kinds?: string[];
        endpoint_policy?: string;
        endpoint_labels?: string[];
        endpoint_atom_indices?: number[][];
        tag?: string;
        layer_tag?: string;
        style?: LabelStyle;
    };
};

export type AddAngleMeasurementMessage = {
    op: "add_angle_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        endpoint_kinds?: string[];
        endpoint_policy?: string;
        endpoint_labels?: string[];
        endpoint_atom_indices?: number[][];
        tag?: string;
        layer_tag?: string;
        style?: LabelStyle;
    };
};

export type AddDihedralMeasurementMessage = {
    op: "add_dihedral_measurement";
    tag?: string;
    options?: {
        picks_atom_indices?: number[][];
        endpoint_kinds?: string[];
        endpoint_policy?: string;
        endpoint_labels?: string[];
        endpoint_atom_indices?: number[][];
        tag?: string;
        layer_tag?: string;
        style?: LabelStyle;
    };
};

export type SetMeasurementSettingsMessage = {
    op: "set_measurement_settings";
    options?: {
        endpoint_policy_default?: string;
        representative_atoms?: Record<string, string>;
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
    speed?: number;
};

export type ToggleSpinMessage = {
    op: "toggle_spin";
    enable?: boolean;
    speed?: number;
};

export type SetFogMessage = {
    op: "set_fog";
    enable?: boolean;
    intensity?: number;
};

export type SetBackgroundColorMessage = {
    op: "set_background_color";
    /** 0xRRGGBB integer. */
    color: number;
};

export type SetLightingMessage = {
    op: "set_lighting";
    ambient?: number;
    diffuse?: number;
    specular?: number;
};

export type SetClipPlanesMessage = {
    op: "set_clip_planes";
    near?: number;
    far?: boolean;
    min_near?: number;
};

export type SectionEntry = {
    tag: string;
    /** Point on the plane in nm (Python convention). */
    point: [number, number, number];
    /** Unit normal vector. */
    normal: [number, number, number];
    invert?: boolean;
};

export type SetSectionsMessage = {
    op: "set_sections";
    sections: SectionEntry[];
};

export type SetSectionDragMessage = {
    op: "set_section_drag";
    tag: string;
    enabled?: boolean;
};

export type ZoomToPositionMessage = {
    op: "zoom_to_position";
    /** Camera target center in Å (scene units). */
    center: [number, number, number];
    /** Bounding radius in Å used to set the zoom level. */
    radius?: number;
    duration_ms?: number;
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

export type RenameRegionMessage = {
    op: "rename_region";
    tag?: string;
    new_tag?: string;
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

export type SetFigureSpecMessage = {
    op: "set_figure_spec";
    figure_preset?: string;
    figure_scale?: number;
    figure_variants?: string[];
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

export type SetPanelModeMessage = {
    op: "set_panel_mode";
    panel?: "navigate" | "workbench" | null;
    expanded?: boolean;
};

export type SetWorkspaceMessage = {
    op: "set_workspace";
    workspace?: string;
};

export type SetWorkspacePanelMessage = {
    op: "set_workspace_panel";
    panel?: string;
    workspace?: string;
};

export type SetAddonRuntimeSummaryMessage = {
    op: "set_addon_runtime_summary";
    addons?: string[];
    workspace_specs?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        entry_panel?: string | null;
        description?: string | null;
        order?: number;
        meta?: Record<string, unknown>;
    }>;
    panel_specs?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        entry?: string | null;
        description?: string | null;
        order?: number;
        target?: string;
        meta?: Record<string, unknown>;
    }>;
    workbench_sections?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        entry?: string;
        target_panel?: string;
        order?: number;
        meta?: Record<string, unknown>;
    }>;
    context_action_specs?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        entry?: string;
        target_kinds?: string[];
        group?: string | null;
        order?: number;
        meta?: Record<string, unknown>;
    }>;
    export_helper_specs?: Array<{
        addon?: string;
        id?: string;
        title?: string;
        entry?: string;
        formats?: string[];
        order?: number;
        meta?: Record<string, unknown>;
    }>;
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
    preset?: string;
    camera_snapshot?: any;
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

export type SetAtomColorsMessage = {
    op: "set_atom_colors";
    /** Atom indices (model-level, 0-based). */
    atom_indices: number[];
    /** Parallel array of 0xRRGGBB color integers. */
    colors: number[];
    /** When true, replace existing per-atom color map (default true). */
    replace?: boolean;
};

export type ClearAtomColorsMessage = {
    op: "clear_atom_colors";
};

export type MovieKeyframe = {
    time_ms: number;
    camera?: { position: [number, number, number]; target: [number, number, number]; up: [number, number, number] };
    structure_index?: number;
    layer_visibility?: Record<string, boolean>;
    easing?: string;
};

export type PlayMovieMessage = {
    op: "play_movie";
    keyframes: MovieKeyframe[];
    loop?: boolean;
    mode?: "play" | "export";
    fps?: number;
    total_frames?: number;
    width_px?: number;
    height_px?: number;
};

export type StopMovieMessage = {
    op: "stop_movie";
};

export type ViewerMessage =
    SetAtomColorsMessage |
    ClearAtomColorsMessage |
    SetSectionDragMessage |
    AddSphereMessage |
    UpdateSphereMessage |
    AddAlphaSphereSetMessage |
    AddPocketSurfaceMessage |
    AddPocketBlobMessage |
    AddChannelTubeMessage |
    AddAnisotropyEllipsoidsMessage |
    AddPharmacophoreMessage |
    AddNetworkLinksMessage |
    AddHbondsMessage |
    AddDisplacementVectorsMessage |
    AddTetrahedraMessage |
    AddTriangleFacesMessage |
    AddLabelMessage |
    UpdateLabelMessage |
    AddDistanceMeasurementMessage |
    AddAngleMeasurementMessage |
    AddDihedralMeasurementMessage |
    SetMeasurementSettingsMessage |
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
    RenameRegionMessage |
    CreateLayerMessage |
    ShowLayerMessage |
    HideLayerMessage |
    DeleteLayerMessage |
    SetLayerTagMessage |
    SetGlobalRepresentationMessage |
    SetFigureSpecMessage |
    ShowGlobalMessage |
    HideGlobalMessage |
    ZoomMessage |
    ZoomToPositionMessage |
    SetCameraSnapshotMessage |
    SetPanelModeMessage |
    SetWorkspaceMessage |
    SetWorkspacePanelMessage |
    RequestCameraSnapshotMessage |
    RequestImageExportMessage |
    ClearActiveSelectionMessage |
    SetActiveSelectionMessage |
    SaveSelectionMessage |
    SetSelectionTagMessage |
    DeleteSelectionMessage |
    ClearSelectionsMessage |
    PlayMovieMessage |
    StopMovieMessage |
    Record<string, unknown>;
