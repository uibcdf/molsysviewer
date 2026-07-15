// src/messages/viewer-messages.ts

import { PocketSurfaceOptions } from "../shapes/pocket-surface";
import {
    AnisotropyEllipsoidOptions,
    ChannelTubeOptions,
    DisplacementVectorOptions,
    NetworkLinkOptions,
    PharmacophoreOptions,
    PocketBlobOptions,
    RingsOptions,
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
        atom_indices?: number[];
        structures_atom_indices?: number[][];
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

export type AddScalarIsosurfaceMessage = {
    op: "add_scalar_isosurface";
    options?: PocketBlobOptions;
};

export type AddChannelTubeMessage = {
    op: "add_channel_tube";
    options?: ChannelTubeOptions;
};

export type AddRingsMessage = {
    op: "add_rings";
    options?: RingsOptions;
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
        layer_tag?: string;
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

export type LoadMolSysPayloadRefMessage = {
    op: "load_molsys_payload_ref";
    ref?: {
        kind?: "file";
        url?: string;
    };
    label?: string;
    /** Hint from Python side: true when the molsys has more than one structure. */
    multiple_structures?: boolean;
    n_structures?: number;
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
        version?: number;
    };
};

export type UpdateVisibilityDeltaMessage = {
    op: "update_visibility_delta";
    options?: {
        base_version: number;
        version: number;
        shown?: number[];
        hidden?: number[];
    };
};

export type SetFocusFadeMessage = {
    op: "set_focus_fade";
    options?: {
        focus_atom_indices?: number[] | null;
        fade?: number;
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

export type SetCanvasVisibilityMessage = {
    op: "set_canvas_visibility";
    visible?: boolean;
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

export type SetLegendMessage = {
    op: "set_legend";
    options?: {
        items?: Array<{ label: string; color: number }>;
        position?: string;
    };
};

export type SetTrajectoryPlotMessage = {
    op: "set_trajectory_plot";
    options?: {
        visible?: boolean;
        series?: Array<{ label: string; values: number[]; color?: number }>;
        n_frames?: number;
        x?: number[];
        events?: Array<{ frame: number; label?: string; color?: number }>;
        x_label?: string;
        y_label?: string;
        title?: string;
    };
};

export type SectionEntry = {
    tag: string;
    /** Point on the plane in nm (Python convention). */
    point: [number, number, number];
    /** Unit normal vector. */
    normal: [number, number, number];
    invert?: boolean;
    hidden?: boolean;
};

export type SetSectionsMessage = {
    op: "set_sections";
    sections: SectionEntry[];
};

export type SetSectionSummariesMessage = {
    op: "set_section_summaries";
    sections?: Array<SectionEntry & { owner?: string | null; unit: string }>;
    active_selection_count?: number;
    system_loaded?: boolean;
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
    order?: number;
    representation?: string;
    preset?: string;
    user_preset?: any;
    params?: Record<string, unknown>;
};

export type SetRegionRepresentationMessage = {
    op: "set_region_representation";
    tag?: string;
    order?: number;
    representation?: string;
    preset?: string;
    user_preset?: any;
    params?: Record<string, unknown>;
};

export type SetRegionOrderMessage = {
    op: "set_region_order";
    tag?: string;
    order?: number;
};

export type ShowRegionMessage = {
    op: "show_region" | "show_only_region";
    tag?: string;
};

export type HideRegionMessage = {
    op: "hide_region";
    tag?: string;
};

export type SetRegionsVisibilityMessage = {
    op: "set_regions_visibility";
    tags?: string[];
    hidden: boolean;
};

export type SetRegionSummariesMessage = {
    op: "set_region_summaries";
    regions?: Array<{
        tag: string;
        owner?: string | null;
        atom_indices?: number[];
        atom_count?: number;
        selection?: string;
        hidden?: boolean;
        /** Tag of the layer this region belongs to, or null (Phase 9). */
        layer?: string | null;
        mode?: "static" | "dynamic";
        frame_dependent?: boolean;
        representation?: string | null;
        preset?: string | null;
        representation_params?: Record<string, unknown>;
        overlap_tags?: string[];
        available_attributes?: string[];
    }>;
    representations?: string[];
    presets?: string[];
};

export type SetLayerSummariesMessage = {
    op: "set_layer_summaries";
    layers?: Array<{
        tag: string;
        owner?: string | null;
        provenance: "auto" | "user";
        hidden?: boolean;
    }>;
};

export type SetWholeSummaryMessage = {
    op: "set_whole_summary";
    representation?: string | null;
    preset?: string | null;
    params?: Record<string, unknown>;
    visible?: boolean;
    color_scheme?: string | null;
    scene_style_name?: string | null;
    available_attributes?: string[];
    color_schemes?: string[];
    inheriting_region_count?: number;
    none_state_region_count?: number;
    covering_layer_count?: number;
};

export type SetAnnotationSummariesMessage = {
    op: "set_annotation_summaries";
    annotations?: Array<{
        kind?: string;
        tag: string;
        owner?: string | null;
        layer_tag?: string | null;
        text?: string | null;
        style?: LabelStyle | null;
        n_atoms?: number;
        atom_indices?: number[];
        anchor?: { type?: string; indices?: number[] };
        hidden?: boolean;
        broken?: boolean;
        broken_reason?: string | null;
    }>;
    active_selection_count?: number;
    system_loaded?: boolean;
};

export type SetMeasurementSummariesMessage = {
    op: "set_measurement_summaries";
    measurements?: Array<{
        kind?: string;
        tag: string;
        owner?: string | null;
        layer_tag?: string | null;
        n_picks?: number;
        atom_indices?: number[];
        value?: number | null;
        unit?: string | null;
        endpoint_labels?: string[];
        endpoint_policy?: string;
        hidden?: boolean;
        broken?: boolean;
        broken_reason?: string | null;
    }>;
    endpoint_policy_default?: "atom" | "centroid" | "representative_atom";
    representative_atoms?: Record<string, string>;
    active_selection_count?: number;
    structure_index?: number;
    system_loaded?: boolean;
};

export type MeasurementSeriesMessage = {
    op: "measurement_series";
    tag: string;
    request_id?: number | null;
    unit?: string;
    n_frames?: number;
    sparkline?: number[];
    sparkline_indices?: number[];
    series_index?: number | null;
};

export type SetShapeSummariesMessage = {
    op: "set_shape_summaries";
    shapes?: Array<{
        op?: string;
        kind?: string;
        tag: string;
        owner?: string | null;
        layer_tag?: string | null;
        title?: string;
        subtitle?: string | null;
        atom_indices?: number[];
        hidden?: boolean;
        color?: string | null;
        n_colors?: number | null;
        radius?: { magnitude?: number; unit?: string } | null;
        n_radii?: number | null;
        alpha?: number | null;
        radius_scale?: number | null;
        length_scale?: number | null;
        broken?: boolean;
        broken_reason?: string | null;
    }>;
};

export type SetDynamicRegionAtomsMessage = {
    op: "set_dynamic_region_atoms";
    frame?: number;
    regions?: Array<{
        tag?: string;
        atom_indices?: number[];
    }>;
};

export type BatchRegionOperationsMessage = {
    op: "batch_region_operations";
    operations?: Array<Record<string, unknown>>;
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
    kind: string;
};

export type HideLayerMessage = {
    op: "hide_layer";
    tag?: string;
    kind: string;
};

export type DeleteLayerMessage = {
    op: "delete_layer";
    tag?: string;
    kind: string;
};

export type SetLayerTagMessage = {
    op: "set_layer_tag";
    tag?: string;
    kind: string;
    new_tag: string;
};

export type SetWholeRepresentationMessage = {
    op: "set_whole_representation";
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

export type ShowWholeMessage = {
    op: "show_whole";
    target?: "whole" | "all";
};

export type HideWholeMessage = {
    op: "hide_whole";
    target?: "whole" | "all";
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
    panel?: "navigate" | "addons" | null;
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
    addon_sections?: Array<{
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
    discovery_failures?: Array<{
        kind?: string;
        source?: string;
        reason?: string;
        traceback?: string;
    }>;
    lifecycle_failures?: Array<{
        kind?: string;
        source?: string;
        reason?: string;
        traceback?: string;
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
    /** Optional model-level atom indices to clear. Absent clears every per-atom colour. */
    atom_indices?: number[];
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
    start_time_ms?: number;
};

export type StopMovieMessage = {
    op: "stop_movie";
};

export type PartialCoordinatesUpdateMessage = {
    op: "partial_coordinates_update";
    coordinates: number[][];
    atom_indices: number[];
    transaction_id?: string | number;
};

export type KnownViewerMessage =
    PartialCoordinatesUpdateMessage |
    SetAtomColorsMessage |
    ClearAtomColorsMessage |
    SetSectionsMessage |
    SetSectionSummariesMessage |
    SetSectionDragMessage |
    AddSphereMessage |
    UpdateSphereMessage |
    AddAlphaSphereSetMessage |
    AddPocketSurfaceMessage |
    AddPocketBlobMessage |
    AddScalarIsosurfaceMessage |
    AddChannelTubeMessage |
    AddRingsMessage |
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
    LoadMolSysPayloadRefMessage |
    LoadStructureFromUrlMessage |
    LoadPdbIdMessage |
    UpdateVisibilityMessage |
    UpdateVisibilityDeltaMessage |
    SetFocusFadeMessage |
    SetTrajectoryPlotMessage |
    ClearSceneMessage |
    SetCanvasVisibilityMessage |
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
    SetRegionsVisibilityMessage |
    SetRegionSummariesMessage |
    SetLayerSummariesMessage |
    SetWholeSummaryMessage |
    SetAnnotationSummariesMessage |
    SetMeasurementSummariesMessage |
    MeasurementSeriesMessage |
    SetShapeSummariesMessage |
    SetDynamicRegionAtomsMessage |
    SetRegionOrderMessage |
    BatchRegionOperationsMessage |
    DeleteRegionMessage |
    RenameRegionMessage |
    CreateLayerMessage |
    ShowLayerMessage |
    HideLayerMessage |
    DeleteLayerMessage |
    SetLayerTagMessage |
    SetWholeRepresentationMessage |
    SetFigureSpecMessage |
    ShowWholeMessage |
    HideWholeMessage |
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
    StopMovieMessage;

// The runtime bridge also tolerates arbitrary/forward-compatible messages, but
// that permissiveness must not poison `KnownViewerMessage["op"]` (the literal
// union that types the dispatch), so the catch-all lives only here.
export type ViewerMessage = KnownViewerMessage | Record<string, unknown>;
