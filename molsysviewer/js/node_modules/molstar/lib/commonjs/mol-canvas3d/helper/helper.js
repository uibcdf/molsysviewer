"use strict";
/**
 * Copyright (c) 2020-2025 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Alexander Rose <alexander.rose@weirdbyte.de>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.Helper = exports.DefaultHelperProps = exports.HelperParams = void 0;
const param_definition_1 = require("../../mol-util/param-definition.js");
const bounding_sphere_helper_1 = require("./bounding-sphere-helper.js");
const camera_helper_1 = require("./camera-helper.js");
const handle_helper_1 = require("./handle-helper.js");
const pointer_helper_1 = require("./pointer-helper.js");
exports.HelperParams = {
    debug: param_definition_1.ParamDefinition.Group(bounding_sphere_helper_1.DebugHelperParams),
    camera: param_definition_1.ParamDefinition.Group({
        helper: param_definition_1.ParamDefinition.Group(camera_helper_1.CameraHelperParams)
    }),
    handle: param_definition_1.ParamDefinition.Group(handle_helper_1.HandleHelperParams),
    pointer: param_definition_1.ParamDefinition.Group(pointer_helper_1.PointerHelperParams),
};
exports.DefaultHelperProps = param_definition_1.ParamDefinition.getDefaultValues(exports.HelperParams);
class Helper {
    constructor(webgl, scene, props = {}) {
        const p = { ...exports.DefaultHelperProps, ...props };
        this.debug = new bounding_sphere_helper_1.BoundingSphereHelper(webgl, scene, p.debug);
        this.camera = new camera_helper_1.CameraHelper(webgl, p.camera.helper);
        this.handle = new handle_helper_1.HandleHelper(webgl, p.handle);
        this.pointer = new pointer_helper_1.PointerHelper(webgl, p.pointer);
    }
}
exports.Helper = Helper;
