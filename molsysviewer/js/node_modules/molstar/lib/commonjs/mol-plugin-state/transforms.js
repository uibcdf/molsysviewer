"use strict";
/**
 * Copyright (c) 2018 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author David Sehnal <david.sehnal@gmail.com>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.StateTransforms = void 0;
const tslib_1 = require("tslib");
const Data = tslib_1.__importStar(require("./transforms/data.js"));
const Misc = tslib_1.__importStar(require("./transforms/misc.js"));
const Model = tslib_1.__importStar(require("./transforms/model.js"));
const Volume = tslib_1.__importStar(require("./transforms/volume.js"));
const Representation = tslib_1.__importStar(require("./transforms/representation.js"));
const Shape = tslib_1.__importStar(require("./transforms/shape.js"));
exports.StateTransforms = {
    Data,
    Misc,
    Model,
    Volume,
    Representation,
    Shape
};
