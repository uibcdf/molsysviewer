export const BOX_TAG = "__msv_box";
export type BoxDisplayMetadata = { definition_revision: number; structure_index: number; frame_update: boolean };
export type BoxDisplayProjection = Pick<BoxDisplayMetadata, "definition_revision" | "structure_index">;

export function isBoxDisplayProjection(value: any): value is BoxDisplayProjection {
    return !!value && Number.isSafeInteger(value.definition_revision) && value.definition_revision >= 0
        && Number.isSafeInteger(value.structure_index) && value.structure_index >= 0;
}

export function isAutomaticBoxClear(message: any): boolean {
    return message?.op === "clear_shapes_by_tag" && message.tag === BOX_TAG
        && Number.isSafeInteger(message.box_frame_update) && message.box_frame_update >= 0;
}
