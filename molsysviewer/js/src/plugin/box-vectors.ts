/** Fixed-unit graphic data: three box vectors as rows, in angstroms. */
export type BoxVectorTable = Float32Array | Float64Array;

export function copyJsonBoxVectors(structures: readonly { box?: number[][] }[]): BoxVectorTable | undefined {
    if (!structures.some(frame => frame.box !== undefined)) return undefined;
    const values = new Float64Array(structures.length * 9).fill(NaN);
    structures.forEach((frame, index) => {
        const rows = frame.box;
        if (!Array.isArray(rows) || rows.length !== 3 || rows.some(row =>
            !Array.isArray(row) || row.length !== 3 || row.some(value => typeof value !== "number" || !Number.isFinite(value)))) return;
        rows.forEach((row, axis) => values.set(row, index * 9 + axis * 3));
    });
    return values;
}

export function readBoxVectors(table: BoxVectorTable | undefined, frame: number): number[][] | undefined {
    if (!table || !Number.isSafeInteger(frame) || frame < 0 || (frame + 1) * 9 > table.length) return undefined;
    const values = table.subarray(frame * 9, frame * 9 + 9);
    if (!values.every(Number.isFinite)) return undefined;
    return [Array.from(values.subarray(0, 3)), Array.from(values.subarray(3, 6)), Array.from(values.subarray(6, 9))];
}
