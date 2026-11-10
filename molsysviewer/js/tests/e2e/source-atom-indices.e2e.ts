import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace, fixtureEnvironment } from "./fixture-workspace";

const dir=dirname(fileURLToPath(import.meta.url));
const close=(a: number[],b: number[])=>{assert.equal(a.length,b.length);a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-4,`${v} != ${b[i]}`));};
async function main(){
 await withFixtureWorkspace("source-atom-indices",async workspace=>{
  const native=spawnSync(process.env.PYTHON||"python",[resolve(dir,"source-atom-indices-bridge.py")],{env:fixtureEnvironment(workspace),encoding:"utf8",maxBuffer:16*1024*1024});
  assert.equal(native.status,0,native.stderr);const cases=JSON.parse(native.stdout),browser=await chromium.launch();
  try{const page=await browser.newPage({viewport:{width:1100,height:800}});const errors:string[]=[];page.on("pageerror",e=>errors.push(String(e)));
   for(const [caseIndex,item] of [...cases.entries()].reverse())for(const kind of ["initial","restored"]){
    await page.goto("about:blank");await page.setContent('<div id="root" style="width:1000px;height:750px"></div>');await page.addScriptTag({path:resolve(dir,"harness.bundle.js")});
    await page.evaluate(async messages=>{const w=window as any;w.c=await w.Harness.createController("root");for(const m of messages)await w.c.handleMessage(m);},item[kind]);
    for(const frame of [0,2,1]){
     await page.evaluate(async frame=>(window as any).c.trajectory.setTrajectoryFrame(frame),frame);
     const actual=await page.evaluate(()=>(window as any).Harness.inspectSourceAtomCorrespondence((window as any).c,[1]));
     assert.deepEqual(actual.selected,[1]);assert.equal(actual.context.atom_index,1);
     assert.deepEqual([...actual.context.atom_indices].sort(),item.expected.groups.flatMap((g:number,i:number)=>g===item.expected.groups[1]?[i]:[]).sort(),"Context retains the complete picked source group");assert.equal(actual.context.metadata.group_index,item.expected.groups[1]);
     assert.deepEqual([...actual.regionAtoms].sort(),[1,4]);
     if(caseIndex===1)assert.notDeepEqual(actual.permutation,[0,1,2,3,4,5],"The noncontiguous fixture must retain a nonidentity permutation");
     assert.deepEqual(actual.colors,item.expected.colors);
     const xyz=item.expected.coordinates[frame];actual.positions.forEach((p:number[],i:number)=>close(p,xyz[i]));
     const center=xyz[1].map((v:number,i:number)=>(v+xyz[4][i])/2);
     assert.ok(actual.measurement.geometry.length);for(const g of actual.measurement.geometry){close(g.points[0],center);close(g.points[1],xyz[0]);}
     assert.ok(actual.annotations.length);for(const a of actual.annotations)close(a.anchor,center);assert.deepEqual([...new Set(actual.labelAtoms)].sort(),[1,4],JSON.stringify({caseIndex,kind,frame,labelTrace:actual.labelTrace,labelAtoms:actual.labelAtoms}));assert.ok(actual.labelCenters.length);actual.labelCenters.forEach((p:number[],i:number)=>close(p,actual.labelBounds[i]));
     assert.ok(actual.sphereCenters.length);for(const p of actual.sphereCenters)close(p,center);const first=item.expected.coordinates[0],staticCenter=first[1].map((v:number,i:number)=>(v+first[4][i])/2);assert.ok(actual.staticSphereCenters.length);for(const p of actual.staticSphereCenters)close(p,staticCenter);
    }
    await page.evaluate(()=>(window as any).c.dispose());
   }
   assert.deepEqual(errors,[]);console.log("SOURCE_ATOM_INDICES_OK: contiguous/noncontiguous real pentalanine, three structures, selection/context, region, colors, measures, annotations, spheres and recovered session");
  }finally{await browser.close();}
 });
}
main().catch(error=>{console.error(error);process.exitCode=1;});
