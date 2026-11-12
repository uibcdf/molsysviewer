/** Import history is descriptive, never authentication or an instruction. */
const domains = new Set(["annotation", "interaction", "layer", "measurement", "region", "shape"]);

function record(value: unknown, fields: readonly string[]): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)
        || Object.keys(value).length !== fields.length || fields.some(key => !Object.hasOwn(value, key))) {
        throw new Error("Invalid Movie import provenance record.");
    }
    return value as Record<string, unknown>;
}

function text(value: unknown): string {
    if (typeof value !== "string" || !value.trim()) throw new Error("Movie import references require nonempty tags.");
    return value;
}

function reference(value: unknown, legacy = false): { domain: string; tag: string } {
    const row = record(value, ["domain", "tag"]);
    if (typeof row.domain !== "string" || (legacy ? row.domain !== "legacy" : !domains.has(row.domain))) {
        throw new Error("Invalid Movie import domain.");
    }
    return { domain: row.domain, tag: text(row.tag) };
}

function digest(value: unknown): void {
    if (typeof value !== "string" || !/^sha256:[0-9a-f]{64}$/.test(value)) throw new Error("Invalid Movie import SHA-256.");
}

function count(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 1) throw new Error("Invalid Movie import count.");
    return value;
}

export function validateMovieImportProvenance(value: unknown, destinationCount: number): void {
    const row = record(value, ["schema", "source_sha256", "source_version", "source_binding", "target_map",
        "structure_index_map", "warnings", "targets"]);
    const legacy = row.schema === "molsysviewer.movie_import@2";
    if (legacy ? row.source_version !== 1 || row.source_binding !== null
        : row.schema !== "molsysviewer.movie_import@1" || row.source_version !== 2) {
        throw new Error("Unsupported Movie import provenance.");
    }
    digest(row.source_sha256);
    // Legacy recipes have no source binding. This is only an index bound.
    let structures = Number.MAX_SAFE_INTEGER + 1;
    if (!legacy) {
        const binding = record(row.source_binding, ["n_atoms", "n_structures", "fingerprint"]);
        count(binding.n_atoms);
        structures = count(binding.n_structures);
        digest(binding.fingerprint);
    }
    if (!Array.isArray(row.target_map)) throw new Error("Movie target maps require a list.");
    const sources = new Set<string>(), targets = new Set<string>(), associations = new Set<string>();
    for (const entry of row.target_map) {
        const pair = record(entry, ["source", "target"]);
        const source = reference(pair.source, legacy), target = reference(pair.target);
        const a = JSON.stringify(source), b = JSON.stringify(target);
        if ((!legacy && source.domain !== target.domain) || sources.has(a) || targets.has(b)) throw new Error("Invalid Movie target map.");
        sources.add(a); targets.add(b);
        associations.add(JSON.stringify([source, target]));
    }
    if (row.structure_index_map !== null && (!Array.isArray(row.structure_index_map)
        || row.structure_index_map.length !== destinationCount || row.structure_index_map.some(value => value !== null
            && (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0 || value >= structures)))) {
        throw new Error("Invalid Movie structure correspondence.");
    }
    if (!Array.isArray(row.warnings) || row.warnings.some(code => typeof code !== "string" || !code)) {
        throw new Error("Invalid Movie import warning codes.");
    }
    if (!Array.isArray(row.targets)) throw new Error("Invalid Movie import associations.");
    const tracks = new Set<string>();
    for (const entry of row.targets) {
        const target = record(entry, ["track", "source", "target", "source_identity", "target_identity"]);
        const track = text(target.track);
        const sourceRef = reference(target.source, legacy), targetRef = reference(target.target);
        if (tracks.has(track) || (!legacy && sourceRef.domain !== targetRef.domain)) {
            throw new Error("Invalid Movie import association.");
        }
        tracks.add(track);
        if (legacy && (!associations.has(JSON.stringify([sourceRef, targetRef]))
            || !target.source_identity || typeof target.source_identity !== "object"
            || Array.isArray(target.source_identity) || Object.keys(target.source_identity).length !== 0)) {
            throw new Error("Legacy Movie association requires a declared target and unknown source identity.");
        }
        for (const key of ["source_identity", "target_identity"]) {
            const identity = target[key];
            if (!identity || typeof identity !== "object" || Array.isArray(identity)
                || Object.entries(identity).some(([field, value]) => !["uid", "definition_sha256", "analysis_name", "analysis_revision", "op"].includes(field)
                    || value !== null && typeof value !== "string")) throw new Error("Invalid Movie import identity.");
            const definition = (identity as Record<string, unknown>).definition_sha256;
            if (definition != null) digest(definition);
        }
    }
}
