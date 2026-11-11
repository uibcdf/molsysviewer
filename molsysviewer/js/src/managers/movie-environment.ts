import type { Canvas3D } from "molstar/lib/mol-canvas3d/canvas3d";
import { resolvedMovieEnvironment } from "./movie-appearance";

/** Observe the supported channels synchronously in the completed-draw reader.
 * Diffuse is the primary directional light, matching the existing scene setter.
 * Other renderer channels are deliberately outside this bounded catalogue.
 */
export function readMovieEnvironment(canvas: Pick<Canvas3D, "props">) {
    const renderer = canvas.props.renderer;
    return resolvedMovieEnvironment({ background: { color: renderer.backgroundColor },
        lighting: { ambient: renderer.ambientIntensity, diffuse: renderer.light[0]?.intensity } });
}
