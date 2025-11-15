/**
 * Copyright (c) 2018 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author David Sehnal <david.sehnal@gmail.com>
 */
import * as Data from './transforms/data.js';
import * as Misc from './transforms/misc.js';
import * as Model from './transforms/model.js';
import * as Volume from './transforms/volume.js';
import * as Representation from './transforms/representation.js';
import * as Shape from './transforms/shape.js';
export declare const StateTransforms: {
    Data: typeof Data;
    Misc: typeof Misc;
    Model: typeof Model;
    Volume: typeof Volume;
    Representation: typeof Representation;
    Shape: typeof Shape;
};
export type StateTransforms = typeof StateTransforms;
