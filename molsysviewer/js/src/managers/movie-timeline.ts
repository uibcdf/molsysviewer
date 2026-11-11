import { Mat3, Quat, Vec3 } from "molstar/lib/mol-math/linear-algebra";

const halfTurnTolerance = 1e-12;

const collections = {
    annotation: "annotations",
    interaction: "interactions",
    layer: "layers",
    measurement: "measurements",
    region: "regions",
    shape: "shapes",
} as const;

type VisibilityDomain = keyof typeof collections | "whole";
type Visibility = { domain: VisibilityDomain; tag: string | null; visible: boolean };
type CameraPose = { position: Vec3; target: Vec3; up: Vec3 };
type CameraKey = { pose: CameraPose; distance: number; orientation: Quat };
type Easing = "linear" | "ease-in" | "ease-out" | "ease-in-out";
type Key<T> = { time: number; value: T; easing: Easing };
type MovieSample = {
    time_ms: number;
    camera: CameraPose;
    structure_index: number;
    visibility: Visibility[];
};

function record(value: unknown, label: string, fields?: readonly string[]): Record<string, unknown> {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
        throw new Error(`${label} must be an object.`);
    }
    if (fields && (Object.keys(value).length !== fields.length || fields.some(field => !owns(value, field)))) {
        throw new Error(`${label} must contain ${fields.join(", ")}.`);
    }
    return value as Record<string, unknown>;
}

function owns(value: object, field: string): boolean {
    return Object.prototype.hasOwnProperty.call(value, field);
}

function tag(value: unknown): string {
    if (typeof value !== "string" || !value.trim()) throw new Error("Movie tags must be nonempty.");
    return value;
}

function time(value: unknown, maximum = Number.MAX_SAFE_INTEGER): number {
    if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > maximum) {
        throw new Error(`Movie time must be between 0 and ${maximum} ms.`);
    }
    return value;
}

function frame(value: unknown, count: number): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0 || value >= count) {
        throw new Error(`Movie structure index must be an integer in [0, ${count}).`);
    }
    return value;
}

function visibility(value: unknown): boolean {
    if (typeof value !== "boolean") throw new Error("Movie visibility must be boolean.");
    return value;
}

function vector(value: unknown): Vec3 {
    if (!Array.isArray(value) || value.length !== 3
        || !Array.from(value).every(component => typeof component === "number" && Number.isFinite(component))) {
        throw new Error("Movie camera vectors must have three finite components.");
    }
    return Vec3.create(value[0], value[1], value[2]);
}

function camera(value: unknown): CameraKey {
    const pose = record(value, "Movie camera pose");
    const position = vector(pose.position);
    const target = vector(pose.target);
    const up = vector(pose.up);
    const backward = Vec3.sub(Vec3(), position, target);
    const distance = Math.hypot(...backward);
    const upLength = Math.hypot(...up);
    if (!(distance > 0) || !(upLength > 0) || !Number.isFinite(distance) || !Number.isFinite(upLength)) {
        throw new Error("Movie camera requires a positive finite distance and a nonzero up vector.");
    }
    // Divide component-wise, including for representable subnormal lengths.
    Vec3.set(backward, backward[0] / distance, backward[1] / distance, backward[2] / distance);
    Vec3.set(up, up[0] / upLength, up[1] / upLength, up[2] / upLength);
    const right = Vec3.cross(Vec3(), up, backward);
    const rightLength = Math.hypot(...right);
    if (rightLength < 1e-12) throw new Error("Movie camera up must not be parallel to its viewing direction.");
    Vec3.scale(right, right, 1 / rightLength);
    Vec3.cross(up, backward, right);
    const orientation = Quat.fromMat3(Quat(), Mat3.fromColumns(Mat3(), right, up, backward));
    return { pose: { position, target, up }, distance, orientation };
}

function ease(fraction: number, easing: Easing): number {
    switch (easing) {
        case "ease-in": return fraction ** 2;
        case "ease-out": return 1 - (1 - fraction) ** 2;
        case "ease-in-out": return fraction < 0.5 ? 2 * fraction ** 2 : 1 - 2 * (1 - fraction) ** 2;
        default: return fraction;
    }
}

function interpolateCamera(left: CameraKey, right: CameraKey, fraction: number): CameraPose {
    const a = left.orientation;
    const b = right.orientation;
    const dot = Quat.dot(a, b);
    const orientation = Quat();
    const startWeight = 1 - fraction;
    if (Math.abs(dot) <= halfTurnTolerance) {
        // The two equally short arcs need the same sign convention as Python.
        const sign = (value: Quat) => Math.sign(value.find(component => Math.abs(component) > halfTurnTolerance)!);
        const leftWeight = Math.sin(startWeight * Math.PI / 2) * sign(a);
        const rightWeight = Math.sin(fraction * Math.PI / 2) * sign(b);
        for (let i = 0; i < 4; i++) orientation[i] = leftWeight * a[i] + rightWeight * b[i];
    } else if (Math.abs(dot) > 0.9995) {
        // This threshold is part of the version-2 evaluator, including Python.
        const endWeight = dot < 0 ? -fraction : fraction;
        for (let i = 0; i < 4; i++) orientation[i] = startWeight * a[i] + endWeight * b[i];
    } else {
        Quat.slerp(orientation, a, b, fraction);
    }
    Quat.normalize(orientation, orientation);
    const target = Vec3();
    for (let i = 0; i < 3; i++) target[i] = startWeight * left.pose.target[i] + fraction * right.pose.target[i];
    const distance = startWeight * left.distance + fraction * right.distance;
    const offset = Vec3.transformQuat(Vec3(), Vec3.unitZ, orientation);
    const position = Vec3.scaleAndAdd(Vec3(), target, offset, distance);
    const up = Vec3.transformQuat(Vec3(), Vec3.unitY, orientation);
    // Match Python's final basis check, including loss of distance to rounding.
    return camera({ position, target, up }).pose;
}

function keys<T>(value: unknown, duration: number, read: (value: unknown) => T, cameraTrack = false): Key<T>[] {
    if (!Array.isArray(value) || !value.length) throw new Error("A Movie track requires at least one key.");
    const result: Key<T>[] = [];
    for (const item of value) {
        const key = record(item, "Movie key");
        if (Object.keys(key).some(field => field !== "time_ms" && field !== "value" && field !== "easing")) {
            throw new Error("Movie keys accept time_ms, value and optional easing.");
        }
        const at = time(key.time_ms, duration);
        if (result.length && at <= result[result.length - 1].time) {
            throw new Error("Movie keys in one track must be strictly increasing.");
        }
        const easing = owns(key, "easing") ? key.easing : "linear";
        if (easing !== "linear" && (!cameraTrack || (easing !== "ease-in" && easing !== "ease-out" && easing !== "ease-in-out"))) {
            throw new Error("Only camera pose keys admit a non-linear easing.");
        }
        result.push({ time: at, value: read(key.value), easing });
    }
    return result;
}

function upperBound<T>(keys: readonly Key<T>[], at: number): number {
    let low = 0;
    let high = keys.length;
    while (low < high) {
        const middle = low + Math.floor((high - low) / 2);
        if (keys[middle].time <= at) low = middle + 1;
        else high = middle;
    }
    return low;
}

function visibilityId(domain: string, name: string | null): string {
    return JSON.stringify([domain, name]);
}

function sceneVisibility(scene: Record<string, unknown>): Map<string, Visibility> {
    const whole = { domain: "whole", tag: null, visible: visibility(record(scene.whole, "Movie whole").visible) } as const;
    const rows = new Map<string, Visibility>([[visibilityId("whole", null), whole]]);
    for (const domain of Object.keys(collections) as (keyof typeof collections)[]) {
        const name = collections[domain];
        const items = owns(scene, name) ? scene[name] : [];
        if (!Array.isArray(items)) throw new Error(`Movie scene ${name} must be a list.`);
        for (const value of items) {
            const item = record(value, `Movie ${domain}`);
            const name = tag(item.tag);
            const id = visibilityId(domain, name);
            if (rows.has(id)) throw new Error(`Ambiguous Movie target ${id}.`);
            rows.set(id, { domain, tag: name, visible: !visibility(owns(item, "hidden") ? item.hidden : false) });
        }
    }
    return rows;
}

/**
 * Compile a detached version-2 recipe for arbitrary-time evaluation in JavaScript.
 * The caller owns binding to a molecular system and application to a live scene.
 */
export function compileMovieTimeline(value: unknown): { duration_ms: number; evaluate(time_ms: number): MovieSample } {
    const recipe = record(value, "Movie recipe", ["molsysmovie_version", "duration_ms", "units", "baseline", "tracks"]);
    if (recipe.molsysmovie_version !== 2) throw new Error("Unsupported Movie recipe version.");
    const duration = time(recipe.duration_ms);
    if (duration === 0) throw new Error("Movie duration must be positive.");
    const units = record(recipe.units, "Movie units", ["time", "camera_length"]);
    if (units.time !== "ms" || units.camera_length !== "angstrom") {
        throw new Error("Movie recipes use milliseconds and angstroms.");
    }
    const baseline = record(recipe.baseline, "Movie baseline", ["scene", "camera", "binding"]);
    const binding = record(baseline.binding, "Movie molecular binding", ["n_atoms", "n_structures", "fingerprint"]);
    const count = binding.n_structures;
    if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 1
        || typeof binding.n_atoms !== "number" || !Number.isSafeInteger(binding.n_atoms) || binding.n_atoms < 1
        || typeof binding.fingerprint !== "string" || !/^sha256:[0-9a-f]{64}$/.test(binding.fingerprint)) {
        throw new Error("Movie molecular binding requires positive counts and a SHA-256 fingerprint.");
    }
    const scene = record(baseline.scene, "Movie scene");
    if (scene.version !== 2 || owns(scene, "movie")) {
        throw new Error("Movie baseline requires a version-2 overlay scene without a nested Movie.");
    }
    if (scene.sources != null) {
        const source = record(record(scene.sources, "Movie scene sources").binding, "Movie source binding",
            ["n_atoms", "n_structures", "fingerprint"]);
        if (Object.keys(binding).some(key => binding[key] !== source[key])) {
            throw new Error("Movie baseline source records do not match its molecular binding.");
        }
    }
    const baseCamera = { time: 0, value: camera(baseline.camera), easing: "linear" } as const;
    const baseFrame = frame(record(scene.view, "Movie view").structure_index, count);
    const rows = sceneVisibility(scene);
    const trackTags = new Set<string>();
    const visTracks = new Map<string, Key<boolean>[]>();
    let poseTrack: Key<CameraKey>[] = [];
    let frameTrack: Key<number>[] = [];
    if (!Array.isArray(recipe.tracks)) throw new Error("Movie tracks must be an ordered list.");
    for (const value of recipe.tracks) {
        const track = record(value, "Movie track", ["tag", "target", "property", "keys"]);
        const name = tag(track.tag);
        if (trackTags.has(name)) throw new Error("Movie track tags must be unique.");
        trackTags.add(name);
        const target = record(track.target, "Movie target");
        const domain = target.domain;
        if (typeof domain !== "string" || Object.keys(target).some(field => field !== "domain" && field !== "tag")) {
            throw new Error("Movie targets require a domain and optionally a tag.");
        }
        const untagged = domain === "camera" || domain === "structure" || domain === "whole";
        if (untagged && target.tag != null) throw new Error(`Movie target ${domain} has no tag.`);
        if (domain === "camera" && track.property === "pose") {
            if (poseTrack.length) throw new Error("Movie permits only one track per target property.");
            poseTrack = keys(track.keys, duration, camera, true);
        } else if (domain === "structure" && track.property === "index") {
            if (frameTrack.length) throw new Error("Movie permits only one track per target property.");
            frameTrack = keys(track.keys, duration, value => frame(value, count));
        } else if (track.property === "visible" && domain !== "camera" && domain !== "structure") {
            const id = visibilityId(domain, untagged ? null : tag(target.tag));
            if (!rows.has(id)) throw new Error(`Unknown Movie visibility target ${id}.`);
            if (visTracks.has(id)) throw new Error("Movie permits only one track per target property.");
            visTracks.set(id, keys(track.keys, duration, visibility));
        } else {
            throw new Error(`Unsupported Movie property for ${domain}.`);
        }
    }

    return {
        duration_ms: duration,
        evaluate(time_ms) {
            const at = time(time_ms, duration);
            const right = upperBound(poseTrack, at);
            const start = poseTrack[right - 1] ?? baseCamera;
            const end = poseTrack[right];
            const pose = !end || start.time === at
                ? { position: Vec3.clone(start.value.pose.position), target: Vec3.clone(start.value.pose.target),
                    up: Vec3.clone(start.value.pose.up) }
                : interpolateCamera(start.value, end.value, ease((at - start.time) / (end.time - start.time), start.easing));
            return {
                time_ms: at,
                camera: pose,
                structure_index: frameTrack[upperBound(frameTrack, at) - 1]?.value ?? baseFrame,
                visibility: Array.from(rows, ([id, row]) => {
                    const track = visTracks.get(id);
                    return { ...row, visible: (track && track[upperBound(track, at) - 1]?.value) ?? row.visible };
                }),
            };
        },
    };
}
