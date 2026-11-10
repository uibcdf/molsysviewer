/** Conventional median for finite benchmark observations; empty is not zero. */
export function median(values: readonly number[]): number {
    if (!values.length || values.some(value => !Number.isFinite(value))) {
        throw new RangeError("A benchmark median needs nonempty finite observations");
    }
    const sorted = [...values].sort((left, right) => left - right);
    const middle = Math.floor(sorted.length / 2);
    if (sorted.length % 2) return sorted[middle];
    const lower = sorted[middle - 1], upper = sorted[middle];
    const sum = lower + upper;
    return Number.isFinite(sum) ? sum / 2 : lower / 2 + upper / 2;
}

export function medianOrNull(values: readonly number[]): number | null {
    return values.length ? median(values) : null;
}
