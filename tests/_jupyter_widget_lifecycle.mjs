/** Actual notebook disposal, weak native owners and an independent live witness. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {dirname} from 'node:path';

const config=JSON.parse(await readFile(process.env.MOLSYSVIEWER_JUPYTER_CAPTURE_SETTINGS,'utf8'));
const output=dirname(process.env.MOLSYSVIEWER_JUPYTER_CAPTURE_SETTINGS);
const {chromium}=createRequire(config.viewer_root+'/molsysviewer/js/package.json')('playwright');
let browser,page,stage='bootstrap';
const cell=index=>page.locator('.jp-NotebookPanel:visible .jp-Cell').nth(index);
async function execute(index){
    await page.getByText(/MolSysViewer capture receiving\s*\|\s*Idle/).waitFor();
    await cell(index).locator('.cm-content').click();
    await page.getByRole('button',{name:/Run this cell and advance/}).click();
}
async function marker(text){
    await page.waitForFunction(text=>document.querySelector('.jp-OutputArea-error')
        || [...document.querySelectorAll('.jp-OutputArea-output')].some(node=>node.textContent.trim()===text),text);
    assert.equal(await page.locator('.jp-OutputArea-error').count(),0,'Notebook cell reported a Python exception');
    await page.getByText(text,{exact:true}).waitFor();
}
try {
    browser=await chromium.launch({headless:true,executablePath:process.env.PW_CHROMIUM_BIN||undefined,
        args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--js-flags=--expose-gc']});
    page=await browser.newPage({viewport:{width:1500,height:1200}});
    page.setDefaultTimeout(30000);
    await page.addInitScript(()=>{
        window.__lifecycleControllers=[];window.__lifecycleElements=[];
        let runtime;
        Object.defineProperty(window,'__molsysviewer_anywidget_runtime__',{configurable:true,get:()=>runtime,set(value){
            runtime=value;
            const C=value?.module?.MolSysViewerController;
            if(!C||C.create.__lifecycleWrapped)return;
            const create=C.create;
            const wrapped=async function(...args){
                const controller=await create.apply(this,args);
                window.__lifecycleControllers.push(new WeakRef(controller));
                return controller;
            };
            wrapped.__lifecycleWrapped=true;C.create=wrapped;
            const entry=value.module.default;
            value.module={...value.module,default:{...entry,async render(context){
                window.__lifecycleElements.push(new WeakRef(context.el));
                return entry.render(context);
            }}};
        }});
    });
    await page.goto(`http://127.0.0.1:${config.port}/lab/workspaces/lifecycle-${Date.now()}/tree/capture.ipynb?token=${config.token}`,{waitUntil:'domcontentloaded'});
    await cell(0).filter({hasText:'import molsysviewer as msv'}).waitFor();
    const no=page.getByRole('button',{name:'No',exact:true});
    if(await no.isVisible())await no.click();
    const cdp=await page.context().newCDPSession(page);
    await cdp.send('HeapProfiler.enable');
    async function sample(){
        // WeakRef.deref protects its target until the current job ends.
        await page.evaluate(()=>new Promise(resolve=>setTimeout(resolve,0)));
        await cdp.send('HeapProfiler.collectGarbage');
        return page.evaluate(()=>window.__lifecycleControllers.map(ref=>ref.deref()).filter(Boolean)
            .map(controller=>({disposed:controller.disposed,connected:controller.canvasHost.isConnected,
                atoms:controller.getStructureData()?.elementCount??null})));
    }
    async function ready(index,count){
        await cell(index).locator('[data-molsysviewer-canvas-output]').first().scrollIntoViewIfNeeded();
        const handle=await page.waitForFunction(count=>window.__lifecycleControllers.some(ref=>{
            const controller=ref.deref();
            return controller?.canvasHost.isConnected&&controller.getStructureData()?.elementCount===count;
        }),count);
        await handle.dispose();
    }
    stage='lifecycle open';
    await execute(0);await marker('LIFETIME_WITNESS');await ready(0,22);
    await execute(1);await marker('LIFETIME_VICTIM');await ready(1,62);
    assert.equal((await sample()).filter(item=>item.connected).length,2);
    const initial=await page.evaluate(()=>{
        const controllers=window.__lifecycleControllers.map(ref=>ref.deref());
        const retired=controllers.find(controller=>controller.getStructureData()?.elementCount===62);
        const structure=retired.getStructureData(),model=structure.model,x=model.atomicConformation.x;
        window.__lifecycleNative={structure:new WeakRef(structure),model:new WeakRef(model),axis:new WeakRef(x),buffer:new WeakRef(x.buffer)};
        const witness=controllers.find(controller=>controller.getStructureData()?.elementCount===22);
        return {witness:Array.from(witness.getStructureData().model.atomicConformation.x),retired_buffer_bytes:x.buffer.byteLength};
    });
    stage='lifecycle close';
    await execute(2);await marker('LIFETIME_CLOSED');
    const detached=await page.waitForFunction(()=>window.__lifecycleControllers.filter(ref=>ref.deref()?.canvasHost.isConnected).length===1);
    await detached.dispose();
    await execute(1);await marker('LIFETIME_CLEARED');
    await cell(1).locator('[data-molsysviewer-canvas-output]').waitFor({state:'detached'});
    stage='lifecycle collection';
    const samples=[await sample(),await sample()];
    const observed=await page.evaluate(async()=>{
        const retired=window.__lifecycleElements[1].deref();
        const witness=window.__lifecycleControllers.map(ref=>ref.deref()).find(controller=>controller?.canvasHost.isConnected);
        const canvas=witness.plugin.canvas3d;
        await new Promise((resolve,reject)=>{
            let replay=true;
            const subscription=canvas.didDraw.subscribe(()=>{if(replay)return;subscription.unsubscribe();clearTimeout(timer);resolve();});
            replay=false;
            const timer=setTimeout(()=>{subscription.unsubscribe();reject(new Error('Independent witness needs a fresh native draw'));},5000);
            canvas.requestDraw();
        });
        return {retired_callbacks:retired?['molsysviewerOpenPopup','molsysviewerClosePopup'].filter(name=>typeof retired[name]==='function'):[],
            native_collected:Object.fromEntries(Object.entries(window.__lifecycleNative).map(([name,ref])=>[name,!ref.deref()])),
            witness:Array.from(witness.getStructureData().model.atomicConformation.x)};
    });
    // Preserve the buffer observation separately; #356's residual owner stays open.
    const evidence={outcome:'in_progress',initial,samples,...observed};
    await writeFile(output+'/lifecycle-observations.json',JSON.stringify(evidence,null,2));
    assert.deepEqual(observed.retired_callbacks,[],'Closed output must not retain live popup methods');
    for(const observedSample of samples)assert.deepEqual(observedSample,[{disposed:false,connected:true,atoms:22}]);
    for(const name of ['structure','model','axis'])assert.equal(observed.native_collected[name],true,`${name} must actually be collected`);
    assert.deepEqual(observed.witness,initial.witness,'Independent molecular data must survive disposal');
    await cdp.detach();
    await execute(3);await marker('LIFETIME_DONE');
    evidence.outcome='passed';
    await writeFile(output+'/lifecycle-observations.json',JSON.stringify(evidence,null,2));
    await writeFile(output+'/observations.json',JSON.stringify({outcome:'passed'}));
    console.log('Actual Jupyter controller/native model release and independent witness passed; buffer observation retained separately.');
}catch(error){
    await writeFile(output+'/observations.json',JSON.stringify({outcome:'failed',stage,error_type:error.name,error:String(error),stack:error.stack},null,2));
    console.error(error);process.exitCode=1;
}finally{
    await browser?.close();
}
