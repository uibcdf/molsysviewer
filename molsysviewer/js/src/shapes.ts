// shapes.ts — placeholder utilities for future custom shapes
// ----------------------------------------------------------
// This file contains ONLY minimal helpers used for debugging and
// for logging placeholder "shape" requests coming from Python.
//
// No Mol* geometry is created here. This keeps MolSysViewer stable
// while we prepare a correct shape pipeline for Mol* 5.x in another branch.

export interface TransparentSphereOptions {
    center: [number, number, number];
    radius: number;
    color: number;
    alpha: number;
}

/**
 * Used only for logging. This function does not create any Mol* geometry.
 */
export function describeTransparentSphere(opts: TransparentSphereOptions): string {
    return `Transparent sphere placeholder:
    center = [${opts.center.join(", ")}]
    radius = ${opts.radius}
    color  = 0x${opts.color.toString(16)}
    alpha  = ${opts.alpha}`;
}

