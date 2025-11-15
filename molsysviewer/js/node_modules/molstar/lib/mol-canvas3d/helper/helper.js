/**
 * Copyright (c) 2020-2025 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Alexander Rose <alexander.rose@weirdbyte.de>
 */
import { ParamDefinition as PD } from '../../mol-util/param-definition.js';
import { BoundingSphereHelper, DebugHelperParams } from './bounding-sphere-helper.js';
import { CameraHelper, CameraHelperParams } from './camera-helper.js';
import { HandleHelper, HandleHelperParams } from './handle-helper.js';
import { PointerHelper, PointerHelperParams } from './pointer-helper.js';
export const HelperParams = {
    debug: PD.Group(DebugHelperParams),
    camera: PD.Group({
        helper: PD.Group(CameraHelperParams)
    }),
    handle: PD.Group(HandleHelperParams),
    pointer: PD.Group(PointerHelperParams),
};
export const DefaultHelperProps = PD.getDefaultValues(HelperParams);
export class Helper {
    constructor(webgl, scene, props = {}) {
        const p = { ...DefaultHelperProps, ...props };
        this.debug = new BoundingSphereHelper(webgl, scene, p.debug);
        this.camera = new CameraHelper(webgl, p.camera.helper);
        this.handle = new HandleHelper(webgl, p.handle);
        this.pointer = new PointerHelper(webgl, p.pointer);
    }
}
