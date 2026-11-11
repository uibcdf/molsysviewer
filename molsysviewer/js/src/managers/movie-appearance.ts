/** Bounded Movie appearance values; received against the Python catalogue/oracle. */
export const movieRepresentationTypes = [
    "backbone", "ball-and-stick", "carbohydrate", "cartoon", "ellipsoid", "gaussian-surface",
    "gaussian-volume", "line", "molecular-surface", "point", "putty", "spacefill",
] as const;

export type AppearanceValue = number | string | { ambient: number; diffuse: number };
export type Appearance = { domain: string; tag: string | null; property: string; value: AppearanceValue };
export const continuousAppearance = new Set(["color", "alpha", "background", "lighting"]);
export const colorInterpolation = "linear-light-srgb-half-up@1";
const properties: Record<string, readonly string[]> = {
    whole: ["representation", "color", "alpha"], region: ["representation", "color", "alpha"],
    shape: ["color", "alpha"], interaction: ["color", "alpha"], annotation: ["text"], scene: ["background", "lighting"],
};

function record(value: any): Record<string, any> {
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid Movie appearance record.");
    return value;
}

export function validateMovieEnvironment(value: unknown): void {
    const environment = record(value);
    if (Object.keys(environment).some(key => key !== "background" && key !== "lighting")) throw new Error("Unsupported scene environment.");
    if ("background" in environment) {
        const background = record(environment.background);
        if (Object.keys(background).length !== 1) throw new Error("Invalid scene background.");
        if ("color" in background) appearanceValue(background.color, "background");
        else if (background.mode !== "light" && background.mode !== "dark") throw new Error("Invalid background mode.");
    }
    if ("lighting" in environment) {
        const lighting = record(environment.lighting);
        if (!Object.keys(lighting).length || Object.keys(lighting).some(key => key !== "ambient" && key !== "diffuse")) {
            throw new Error("Invalid scene lighting.");
        }
        for (const value of Object.values(lighting)) appearanceValue(value, "alpha");
    }
}

export function appearanceValue(value: unknown, property: string): AppearanceValue {
    if (property === "color" || property === "background") {
        if (typeof value !== "number" || !Number.isInteger(value) || value < 0 || value > 0xFFFFFF) {
            throw new Error("Movie colours must be 24-bit RGB integers.");
        }
        return value;
    }
    if (property === "alpha") {
        if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
            throw new Error("Movie alpha must be finite and in [0, 1].");
        }
        return value;
    }
    if (property === "lighting") {
        const lighting = record(value);
        if (Object.keys(lighting).length !== 2 || !("ambient" in lighting) || !("diffuse" in lighting)) {
            throw new Error("Movie lighting requires ambient and diffuse.");
        }
        return { ambient: appearanceValue(lighting.ambient, "alpha") as number,
            diffuse: appearanceValue(lighting.diffuse, "alpha") as number };
    }
    if (property === "text" && typeof value === "string") return value;
    if (property === "representation" && movieRepresentationTypes.includes(value as any)) return value as string;
    throw new Error(`Unsupported Movie appearance value for ${property}.`);
}

export function appearanceBaseline(scene: Record<string, any>, domain: string, tag: string | null,
    property: string): AppearanceValue | undefined {
    if (!properties[domain]?.includes(property)) throw new Error(`Unsupported Movie property for ${domain}.`);
    if (domain === "scene") {
        const environment = scene.environment == null ? {} : record(scene.environment);
        let value = property === "background" ? environment.background?.color : environment.lighting;
        if (property === "lighting" && (!value || Object.keys(value).length !== 2
            || !("ambient" in value) || !("diffuse" in value))) value = undefined;
        return value == null ? undefined : appearanceValue(value, property);
    }
    const collection: Record<string, string> = { region: "regions", shape: "shapes", interaction: "interactions", annotation: "annotations" };
    const target = record(domain === "whole" ? scene.whole : scene[collection[domain]]?.find((row: any) => row.tag === tag));
    let value: any;
    if (domain === "whole" || domain === "region") {
        if (target.preset != null || !movieRepresentationTypes.includes(target.representation)) {
            throw new Error("Movie structural appearance requires an explicit simple baseline representation.");
        }
        if (property === "color" && target.color_layer) {
            throw new Error("Movie uniform colour requires no per-atom colour layer on its target.");
        }
        const params = record(target.params ?? {});
        value = property === "representation" ? target.representation : property === "alpha" ? params.alpha ?? 1
            : params.molstar_color_theme?.name === "uniform" ? params.molstar_color_theme.params?.value : undefined;
    } else if (domain === "shape") {
        if (target.op !== "add_sphere") throw new Error("Movie shape colour/alpha currently requires a sphere.");
        value = target.options?.[property];
    } else if (domain === "interaction") value = target.style?.[property];
    else value = target.options?.text;
    return value == null ? undefined : appearanceValue(value, property);
}

export function interpolateAppearance(a: AppearanceValue, b: AppearanceValue, fraction: number, property: string): AppearanceValue {
    if (property === "color" || property === "background") {
        const linear = (byte: number) => { const value = byte / 255;
            return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4; };
        let result = 0;
        for (const shift of [16, 8, 0]) {
            const left = linear(((a as number) >> shift) & 255), right = linear(((b as number) >> shift) & 255);
            const value = (1 - fraction) * left + fraction * right;
            const encoded = value <= 0.0031308 ? 12.92 * value : 1.055 * value ** (1 / 2.4) - 0.055;
            result |= Math.min(255, Math.max(0, Math.floor(encoded * 255 + 0.5))) << shift;
        }
        return result;
    }
    if (property === "lighting") {
        const left = a as { ambient: number; diffuse: number }, right = b as typeof left;
        return { ambient: (1 - fraction) * left.ambient + fraction * right.ambient,
            diffuse: (1 - fraction) * left.diffuse + fraction * right.diffuse };
    }
    return (1 - fraction) * (a as number) + fraction * (b as number);
}
