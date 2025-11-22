// src/structure.ts
import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Column } from "molstar/lib/mol-data/db/column";
import { Table } from "molstar/lib/mol-data/db/table";
import { BasicSchema, createBasic } from "molstar/lib/mol-model-formats/structure/basic/schema";
import { Topology } from "molstar/lib/mol-model/structure/topology";
import { Coordinates } from "molstar/lib/mol-model/structure/coordinates";
import { Model } from "molstar/lib/mol-model/structure/model";
import { Cell } from "molstar/lib/mol-math/geometry/spacegroup/cell";

export interface LoadStructureOptions {
    /** Referencia al nodo anterior que se debe eliminar antes de cargar. */
    previous?: StateObjectRef;
}

export interface LoadedStructure {
    /** Referencia al nodo raíz de los datos brutos (puede no existir en cargas nativas). */
    data?: StateObjectRef;
    /** Referencia al nodo de la trayectoria (parseado). */
    trajectory: StateObjectRef<SO.Molecule.Trajectory>;
    /** Referencia opcional a la estructura creada por el preset. */
    structure?: StateObjectRef<SO.Molecule.Structure>;
}

export interface MolSysAtomPayload {
    atom_id: number[];
    atom_name?: string[];
    element_symbol?: string[];
    residue_id?: number[];
    residue_name?: string[];
    chain_id?: string[];
    entity_id?: string[];
    formal_charge?: number[];
}

export interface MolSysFramePayload {
    /** Lista de coordenadas [[x,y,z], ...] en Å. */
    positions: number[][];
    /** Parámetros de celda opcionales. */
    cell?: { a: number; b: number; c: number; alpha: number; beta: number; gamma: number };
    /** Tiempo opcional del frame. */
    time?: number;
}

export interface MolSysPayload {
    atoms: MolSysAtomPayload;
    coordinates: MolSysFramePayload[];
    bonds?: {
        indexA: number[];
        indexB: number[];
        order?: number[];
    };
    meta?: Record<string, unknown>;
    time?: {
        delta?: number;
        offset?: number;
        unit?: "ps" | "step";
    };
}

async function recyclePreviousNode(plugin: PluginContext, previous?: StateObjectRef) {
    if (!previous) return;
    const builder = plugin.build();
    builder.delete(previous);
    await builder.commit();
}

export async function loadStructureFromString(
    plugin: PluginContext,
    data: string,
    format: string = "pdb",
    label?: string,
    options?: LoadStructureOptions
): Promise<LoadedStructure> {
    await recyclePreviousNode(plugin, options?.previous);

    const raw = await plugin.builders.data.rawData({
        data,
        label: label ?? "Structure from string",
        // extension opcional; ayuda a algunos parsers
        ext: format,
    });

    // parseTrajectory necesita el nombre del formato: 'pdb', 'mmcif', etc.
    const trajectory = await plugin.builders.structure.parseTrajectory(raw, format as any);

    // Aplica el preset por defecto (representación bonita estándar)
    const preset = await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");

    return {
        data: raw.ref,
        trajectory: trajectory.ref,
        structure: preset?.structure?.ref,
    };
}

export async function loadStructureFromUrl(
    plugin: PluginContext,
    url: string,
    format?: string,
    label?: string,
    options?: LoadStructureOptions
): Promise<LoadedStructure> {
    await recyclePreviousNode(plugin, options?.previous);

    // Descarga la estructura (texto) desde la URL
    const dataNode = await plugin.builders.data.download(
        { url, isBinary: false, label },
        { state: { isGhost: true } }
    );

    // Si no se especifica formato, intenta deducirlo de la extensión
    const guessedFormat =
        format ??
        (url.split(".").pop() ?? "pdb"); // "pdb", "cif", "mmcif", etc.

    const trajectory = await plugin.builders.structure.parseTrajectory(
        dataNode,
        guessedFormat as any
    );

    const preset = await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");

    return {
        data: dataNode.ref,
        trajectory: trajectory.ref,
        structure: preset?.structure?.ref,
    };
}

export async function loadStructureFromMolSysPayload(
    plugin: PluginContext,
    payload: MolSysPayload,
    label?: string,
    options?: LoadStructureOptions
): Promise<LoadedStructure> {
    await recyclePreviousNode(plugin, options?.previous);

    if (!payload?.atoms || !payload.coordinates || payload.coordinates.length === 0) {
        throw new Error("MolSys payload requires atoms and at least one coordinate frame");
    }

    const atomCount = payload.atoms.atom_id.length;
    if (atomCount === 0) {
        throw new Error("MolSys payload did not include atom identifiers");
    }

    const firstFrame = payload.coordinates[0];
    const atomSite = createAtomSiteTable(payload, atomCount, firstFrame);
    const basic = createBasic({ atom_site: atomSite }, true);
    const topology = Topology.create(
        label ?? "MolSysMT",
        basic,
        createBondColumns(payload.bonds),
        {
            kind: "mol-viewer:molsysmt",
            name: label ?? "MolSysMT",
            data: payload.meta ?? {},
        }
    );

    const frames = payload.coordinates.map((frame, index) => createFrame(frame, atomCount, index));
    const delta = payload.time?.delta ?? 1;
    const unit = payload.time?.unit ?? "ps";
    const offset = payload.time?.offset ?? 0;
    const coordinates = Coordinates.create(
        frames,
        { value: delta, unit },
        { value: offset, unit }
    );

    const trajectory = await plugin.runTask(
        Model.trajectoryFromTopologyAndCoordinates(topology, coordinates),
        { useOverlay: false }
    );

    const builder = plugin.build();
    const trajectoryNode = builder
        .toRoot()
        .insert(
            new SO.Molecule.Trajectory(trajectory, {
                label: label ?? "MolSysMT Trajectory",
                description: `${trajectory.frameCount} model${trajectory.frameCount === 1 ? "" : "s"}`,
            })
        );
    await builder.commit();

    const preset = await plugin.builders.structure.hierarchy.applyPreset(trajectoryNode.ref, "default");

    return {
        trajectory: trajectoryNode.ref,
        structure: preset?.structure?.ref,
    };
}

function createAtomSiteTable(payload: MolSysPayload, atomCount: number, frame: MolSysFramePayload) {
    const atoms = payload.atoms;
    const ids = ensureNumericArray(atoms.atom_id, atomCount, i => i + 1);
    const names = ensureStringArray(atoms.atom_name, atomCount, i => `A${i + 1}`);
    const elements = ensureStringArray(atoms.element_symbol, atomCount, () => "C");
    const residueIds = ensureNumericArray(atoms.residue_id, atomCount, () => 1);
    const residueNames = ensureStringArray(atoms.residue_name, atomCount, () => "RES");
    const chainIds = ensureStringArray(atoms.chain_id, atomCount, () => "A");
    const entityIds = ensureStringArray(atoms.entity_id, atomCount, () => "1");
    const charges = ensureNumericArray(atoms.formal_charge, atomCount, () => 0);

    const { x, y, z } = splitPositions(frame, atomCount);

    return Table.ofPartialColumns(BasicSchema.atom_site, {
        id: Column.ofIntArray(ids),
        label_atom_id: Column.ofStringArray(names),
        auth_atom_id: Column.ofStringArray(names),
        type_symbol: Column.ofStringArray(elements),
        label_alt_id: Column.ofConst("", atomCount, Column.Schema.str),
        label_comp_id: Column.ofStringArray(residueNames),
        auth_comp_id: Column.ofStringArray(residueNames),
        label_asym_id: Column.ofStringArray(chainIds),
        auth_asym_id: Column.ofStringArray(chainIds),
        label_entity_id: Column.ofStringArray(entityIds),
        label_seq_id: Column.ofIntArray(residueIds),
        auth_seq_id: Column.ofIntArray(residueIds),
        pdbx_PDB_model_num: Column.ofConst(1, atomCount, Column.Schema.int),
        pdbx_PDB_ins_code: Column.ofConst("", atomCount, Column.Schema.str),
        pdbx_formal_charge: Column.ofIntArray(charges),
        occupancy: Column.ofConst(1, atomCount, Column.Schema.float),
        B_iso_or_equiv: Column.ofConst(0, atomCount, Column.Schema.float),
        Cartn_x: Column.ofFloatArray(x),
        Cartn_y: Column.ofFloatArray(y),
        Cartn_z: Column.ofFloatArray(z),
        group_PDB: Column.ofConst("HETATM", atomCount, Column.Schema.str),
    }, atomCount);
}

function splitPositions(frame: MolSysFramePayload, atomCount: number) {
    if (!Array.isArray(frame.positions) || frame.positions.length !== atomCount) {
        throw new Error("MolSys payload coordinates do not match atom count");
    }
    const x = new Float32Array(atomCount);
    const y = new Float32Array(atomCount);
    const z = new Float32Array(atomCount);
    for (let i = 0; i < atomCount; i++) {
        const coords = frame.positions[i];
        x[i] = coords?.[0] ?? 0;
        y[i] = coords?.[1] ?? 0;
        z[i] = coords?.[2] ?? 0;
    }
    return { x, y, z };
}

function ensureStringArray(values: string[] | undefined, length: number, fallback: (index: number) => string) {
    if (Array.isArray(values) && values.length === length) return values;
    const output = new Array<string>(length);
    for (let i = 0; i < length; i++) output[i] = fallback(i);
    return output;
}

function ensureNumericArray(values: number[] | undefined, length: number, fallback: (index: number) => number) {
    if (Array.isArray(values) && values.length === length) return values;
    const output = new Array<number>(length);
    for (let i = 0; i < length; i++) output[i] = fallback(i);
    return output;
}

function createFrame(frame: MolSysFramePayload, atomCount: number, index: number): Coordinates.Frame {
    const { x, y, z } = splitPositions(frame, atomCount);
    const cell = frame.cell
        ? Cell.create(frame.cell.a, frame.cell.b, frame.cell.c, frame.cell.alpha, frame.cell.beta, frame.cell.gamma)
        : void 0;
    return {
        elementCount: atomCount,
        time: { value: frame.time ?? index, unit: "ps" },
        x,
        y,
        z,
        cell,
        xyzOrdering: { isIdentity: true },
    };
}

function createBondColumns(bonds: MolSysPayload["bonds"]): Topology["bonds"] {
    if (!bonds || bonds.indexA.length === 0) {
        return {
            indexA: Column.ofConst(0, 0, Column.Schema.int),
            indexB: Column.ofConst(0, 0, Column.Schema.int),
            order: Column.ofConst(1, 0, Column.Schema.int),
        };
    }
    if (bonds.indexA.length !== bonds.indexB.length) {
        throw new Error("MolSys payload bonds must have matching index arrays");
    }
    const orderValues = bonds.order && bonds.order.length === bonds.indexA.length
        ? bonds.order
        : new Array<number>(bonds.indexA.length).fill(1);
    return {
        indexA: Column.ofIntArray(bonds.indexA),
        indexB: Column.ofIntArray(bonds.indexB),
        order: Column.ofIntArray(orderValues),
    };
}
