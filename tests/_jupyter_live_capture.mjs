import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile, writeFile} from 'node:fs/promises';
import {receiveJupyterMoving} from './_jupyter_moving_capture.mjs';

const config=JSON.parse(await readFile(process.env.MOLSYSVIEWER_JUPYTER_CAPTURE_SETTINGS,'utf8'));
const {chromium}=createRequire(config.viewer_root+'/molsysviewer/js/package.json')('playwright');
const report={scope:'Actual kernel, anywidget, Mol* and normal browser input; no installed/native-host qualification.',capture_restore_cases:0,strong_restore_cases:0,studio_cases:0,records:[],page_errors:[],runtime_console:[]};
let browser,page,stage='bootstrap';
const distance=(a,b)=>Math.max(...['position','target','up'].flatMap(key=>a[key].map((value,i)=>Math.abs(value-b[key][i]))));
const camera=target=>target.evaluate(()=>window.__captureControllers[0].getCameraSnapshot());

async function observeDraws(target){
 await target.evaluate(()=>{
  const c=window.__captureControllers[0];window.__captureDraws={count:0,snapshot:null};let replay=true;
  const trace=window.__captureCameraTrace={requests:[],poses:[],requestCount:0};
  const request=c.plugin.canvas3d.requestCameraReset;
  c.plugin.canvas3d.requestCameraReset=function(options){
   trace.requestCount++;
   trace.requests.push({time:performance.now(),frameToken:c.frameRequestToken,
    provider:typeof options?.snapshot,camera:c.getCameraSnapshot()});
   if(trace.requests.length>64)trace.requests.shift();
   return request.call(this,options);
  };
  c.plugin.canvas3d.didDraw.subscribe(()=>{
   if(replay){replay=false;return;}
   window.__captureDraws.count++;window.__captureDraws.snapshot=c.getCameraSnapshot();
   const snapshot=window.__captureDraws.snapshot,previous=trace.poses.at(-1)?.snapshot;
   if(!previous||['position','target','up'].some(key=>snapshot[key].some((value,i)=>Math.abs(value-previous[key][i])>1e-5))){
    trace.poses.push({time:performance.now(),frameToken:c.frameRequestToken,snapshot});
    if(trace.poses.length>64)trace.poses.shift();
   }
  });
 });
}

async function drawnCamera(target,mark,saved){
 await target.waitForFunction(({mark,saved})=>{
  const drawn=window.__captureDraws,now=drawn.snapshot;
  return drawn.count>mark&&now&&Math.max(...['position','target','up'].flatMap(key=>now[key].map((value,i)=>Math.abs(value-saved[key][i]))))<1e-4;
 },{mark,saved});
}

async function observeControllers(target){
 await target.addInitScript(()=>{
  // Retain real controllers without replacing any command or its result.
  let runtime;window.__captureControllers=[];
  Object.defineProperty(window,'__molsysviewer_anywidget_runtime__',{configurable:true,get:()=>runtime,set(value){
   runtime=value;const C=value?.module?.MolSysViewerController;if(!C)return;
   const create=C.create;C.create=async function(...args){
    const c=await create.apply(this,args);window.__captureControllers.push(c);
    const trace=window.__captureOperationTrace=[];
    const handle=c.handleMessage;
    c.handleMessage=function(message,...rest){
     const item={op:message?.op,started:performance.now()};trace.push(item);if(trace.length>256)trace.shift();
     const finish=error=>{item.finished=performance.now();if(error)item.error=error.name;};
     try{const result=handle.call(this,message,...rest);if(result?.then)result.then(()=>finish(),finish);else finish();return result;}
     catch(error){finish(error);throw error;}
    };
    return c;
   };
  }});
  const open=window.open.bind(window);window.__capturePopups=[];
  window.open=(...args)=>{
   const popup=open(...args);if(!popup)return popup;
   window.__capturePopups.push(popup);
   const append=popup.Node.prototype.appendChild;
   popup.Node.prototype.appendChild=function(node){
    if(node.tagName==='SCRIPT'&&node.textContent.includes('await boot(module)'))node.textContent=node.textContent.replace('await boot(module)',`const create=module.MolSysViewerController.create;module.MolSysViewerController.create=async function(...args){const c=await create.apply(this,args);window.__captureControllers=[...(window.__captureControllers||[]),c];return c;};await boot(module)`);
    return append.call(this,node);
   };
   return popup;
  };
 });
}

async function kernel(code){
 return page.evaluate(async code=>{
  const kernel=window.jupyterapp.shell.currentWidget.sessionContext.session.kernel;
  const future=kernel.requestExecute({code,stop_on_error:true});let output='',error;
  future.onIOPub=message=>{
   if(message.header.msg_type==='stream')output+=message.content.text;
   if(message.header.msg_type==='error')error={name:message.content.ename,value:message.content.evalue,traceback:message.content.traceback};
  };
  const reply=await future.done;
  if(reply.content.status!=='ok'||error)throw new Error(JSON.stringify({reply:reply.content,error}));
  const values=output.split('\n').filter(line=>line.startsWith('MSV_CAPTURE_JSON '));
  if(!values.length)throw new Error('The live kernel produced no explicit observation.');
  return JSON.parse(values.at(-1).slice('MSV_CAPTURE_JSON '.length));
 },code);
}

async function rotate(target){
 await target.evaluate(()=>window.__captureControllers[0].setPanelMode('navigate',false));
 const before=await camera(target),rect=await target.locator('canvas').first().boundingBox();assert.ok(rect);
 const start={x:rect.x+rect.width*.55,y:rect.y+rect.height*.65};
 assert.equal(await target.evaluate(point=>document.elementFromPoint(point.x,point.y)?.tagName,start),'CANVAS','Rotation must hit the exposed molecular canvas.');
 await target.mouse.move(start.x,start.y);
 await target.mouse.down();await target.mouse.move(start.x+65,start.y+35,{steps:8});await target.mouse.up();
 await target.waitForFunction(before=>{
  const now=window.__captureControllers[0].getCameraSnapshot();return Math.max(...now.position.map((value,i)=>Math.abs(value-before.position[i])))>0.05;
 },before);
 return before;
}

async function openWork(target){
 // Establish the existing Studio navigation through its normal controller;
 // all file actions below use real visible controls and authenticated transport.
 await target.evaluate(()=>{const c=window.__captureControllers[0];c.setPanelMode('navigate',true);c.groupPanel.setExpanded(true);c.groupPanel.openSection('export');});
 const work=target.locator('[data-molsysviewer-work-files="true"]');await work.waitFor({state:'visible'});return work;
}

async function openCanvas(){
 await page.evaluate(()=>window.__captureControllers[0].groupPanel.setExpanded(false));
 const source=page.locator('[data-molsysviewer-canvas-output]').first();
 await source.getByRole('button',{name:'Show canvas controls',exact:true}).focus();await page.keyboard.press('Enter');
 const opened=page.waitForEvent('popup');await source.getByTitle('Open popup',{exact:true}).click();const popup=await opened;
 popup.on('pageerror',error=>report.page_errors.push({stage,message:error.message,stack:error.stack}));
 await popup.locator('#molsysviewer-loading').waitFor({state:'hidden'});
 await popup.waitForFunction(()=>window.__captureControllers?.[0]?.getStructureData()?.elementCount===62);
 return popup;
}

async function repliesSince(mark){
 return page.evaluate(mark=>window.__captureTraffic.slice(mark).filter(event=>event.event==='visual_state_snapshot'),mark);
}

async function restored(target,saved,kind,name,work){
 const before=await camera(target);await rotate(target);
 const perturbed=await camera(target);assert.ok(distance(perturbed,saved)>0.05,'Restore must start from another observed camera.');
 const drawMark=await target.evaluate(()=>window.__captureDraws.count);
 if(work){
  await work.getByRole('button',{name:'Restore file…',exact:true}).click();
  await work.getByRole('button',{name:'Confirm restore',exact:true}).click();
  await work.getByLabel('Path in Python session',{exact:true}).waitFor({state:'visible'});
  await target.waitForFunction(()=>{const input=document.querySelector('[data-molsysviewer-work-file-path]');return input&&!input.disabled;});
  assert.match(await work.locator('[data-molsysviewer-work-file-status]').innerText(),/Restored/);
 }else{
  await kernel(kind==='state'?`view.load_state(_output / ${JSON.stringify(name)}); print('MSV_CAPTURE_JSON '+json.dumps(True))`:`msv.load_session(_output / ${JSON.stringify(name)}, view=view); print('MSV_CAPTURE_JSON '+json.dumps(True))`);
 }
 await target.waitForFunction(expected=>{
  const now=window.__captureControllers[0].getCameraSnapshot();return Math.max(...['position','target','up'].flatMap(key=>now[key].map((value,i)=>Math.abs(value-expected[key][i]))))<1e-4;
 },saved).catch(async error=>{
  // Private bounded observations retain the failed predicate's actual state;
  // they never replace a camera request, result, assertion or deadline.
  report.restore_failure={expected:saved,observed:await target.evaluate(()=>{
   const c=window.__captureControllers[0];return {camera:c.getCameraSnapshot(),
    frame:c.trajectory.getTrajectoryState().currentFrame,frameToken:c.frameRequestToken,
    intentional:c.state.hasIntentionalViewpoint(),drawn:window.__captureDraws,
    cameraTrace:window.__captureCameraTrace};
  })};
  throw error;
 });
 await drawnCamera(target,drawMark,saved);
 report.strong_restore_cases++;
 return {before,perturbed};
}

async function receivePython(target,kind,origin){
 stage=`Python ${origin} ${kind}`;await rotate(target);
 const mark=await page.evaluate(()=>window.__captureTraffic.length);
 const name=`python-${origin}.${kind==='state'?'json':'msv'}`;
 const observation=await kernel(`print('MSV_CAPTURE_JSON '+json.dumps(await save_live(${JSON.stringify(name)},${JSON.stringify(kind)})))`);
 const replies=await repliesSince(mark);assert.equal(replies.length,1);assert.equal(replies[0].ok,true);
 assert.deepEqual(observation.state.view.camera,replies[0].snapshot);assert.equal(observation.state.view.structure_index,replies[0].structure_index);
 await restored(target,observation.state.view.camera,kind,name);
 report.records.push({origin,method:'Python',kind,request_id:replies[0].request_id,restore_perturbed:true});report.capture_restore_cases++;
}

async function receiveStudio(target,kind,origin){
 stage=`Studio ${origin} ${kind}`;await rotate(target);const work=await openWork(target);
 const name=`studio-${origin}.${kind==='state'?'json':'msv'}`,path=config.output+'/notebooks/'+name;
 await work.getByLabel('Work file format',{exact:true}).selectOption(kind);
 await work.getByLabel('Path in Python session',{exact:true}).fill(path);
 const mark=await page.evaluate(()=>window.__captureTraffic.length);
 await work.getByRole('button',{name:'Save file',exact:true}).click();
 await target.waitForFunction(()=>{const input=document.querySelector('[data-molsysviewer-work-file-path]');return input&&!input.disabled;});
 const status=await work.locator('[data-molsysviewer-work-file-status]').innerText();assert.match(status,/Saved/);
 const observation=await kernel(`print('MSV_CAPTURE_JSON '+json.dumps(inspect_file(${JSON.stringify(name)},${JSON.stringify(kind)})))`);
 const replies=await repliesSince(mark);assert.equal(replies.length,1);assert.equal(replies[0].ok,true);
 assert.deepEqual(observation.state.view.camera,replies[0].snapshot);assert.equal(observation.state.view.structure_index,replies[0].structure_index);
 await target.evaluate(()=>{window.__captureControllers[0].groupPanel.setExpanded(false);});
 await rotate(target);const other=await camera(target);assert.ok(distance(other,observation.state.view.camera)>0.05);
 await openWork(target);
 const drawMark=await target.evaluate(()=>window.__captureDraws.count);
 await work.getByRole('button',{name:'Restore file…',exact:true}).click();
 await work.getByRole('button',{name:'Confirm restore',exact:true}).click();
 await target.waitForFunction(()=>{const input=document.querySelector('[data-molsysviewer-work-file-path]');return input&&!input.disabled;});
 assert.match(await work.locator('[data-molsysviewer-work-file-status]').innerText(),/Restored/);
 await target.waitForFunction(expected=>{const now=window.__captureControllers[0].getCameraSnapshot();return Math.max(...['position','target','up'].flatMap(key=>now[key].map((value,i)=>Math.abs(value-expected[key][i]))))<1e-4;},observation.state.view.camera);
 await drawnCamera(target,drawMark,observation.state.view.camera);
 assert.equal(await work.getByLabel('Path in Python session',{exact:true}).inputValue(),path);
 report.records.push({origin,method:'Studio',kind,request_id:replies[0].request_id,restore_perturbed:true});report.capture_restore_cases++;report.strong_restore_cases++;report.studio_cases++;
}

async function delayedReply(work,kind){
 stage=kind==='cancel'?'cancel late reply':'autonomous capture deadline';
 const name=kind==='cancel'?'cancelled.json':'timed-out.json';
 await work.getByLabel('Work file format',{exact:true}).selectOption('state');
 await work.getByLabel('Path in Python session',{exact:true}).fill(config.output+'/notebooks/'+name);
 await page.evaluate(()=>{
  const model=window.__captureControllers[0].model,send=model.send.bind(model);
  window.__heldCapture=[];
  window.__releaseCapture=()=>{model.send=send;for(const event of window.__heldCapture.splice(0))send(event);};
  model.send=(event,...rest)=>{
   const body=event?.payload??event;
   if(body?.event==='visual_state_snapshot'){window.__heldCapture.push(event);return;}
   return send(event,...rest);
  };
 });
 await work.getByRole('button',{name:'Save file',exact:true}).click();
 await page.waitForFunction(()=>window.__heldCapture.length===1);
 assert.equal(await work.getByLabel('Path in Python session',{exact:true}).isDisabled(),true);
 if(kind==='cancel')await work.getByRole('button',{name:'Cancel save',exact:true}).click();
 // In the timeout case there is no kernel request or transport poll between
 // the pending Save and this UI verdict. The bound host timer must fire alone.
 await page.waitForFunction(()=>{const input=document.querySelector('[data-molsysviewer-work-file-path]');return input&&!input.disabled;});
 const status=await work.locator('[data-molsysviewer-work-file-status]').innerText();
 assert.match(status,kind==='cancel'?/cancelled/i:/timed?\s*out|request_timeout/i);
 await page.evaluate(()=>window.__releaseCapture());
 const late=await kernel(`print('MSV_CAPTURE_JSON '+json.dumps({'exists':(_output/${JSON.stringify(name)}).exists(),'pending':len(view._work_file_saves._pending),'captures':len(view._frontend_requests._pending),'timers':len(view.widget._scheduled_callbacks)}))`);
 assert.deepEqual(late,{exists:false,pending:0,captures:0,timers:0});
 report[kind==='cancel'?'no_late_write_after_cancel':'no_late_write_after_timeout']=true;
}

try{
 const options={headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']};
 if(process.env.PW_CHROMIUM_BIN)options.executablePath=process.env.PW_CHROMIUM_BIN;
 browser=await chromium.launch(options);
 page=await browser.newPage({viewport:{width:1440,height:1100}});page.setDefaultTimeout(30000);
 page.on('console',message=>{if(['error','warning'].includes(message.type())&&report.runtime_console.length<64)report.runtime_console.push({stage,type:message.type(),text:message.text().slice(0,2048)});});
 page.on('pageerror',error=>report.page_errors.push({stage,message:error.message,stack:error.stack}));await observeControllers(page);
 await page.goto(`http://127.0.0.1:${config.port}/lab/workspaces/capture-${Date.now()}/tree/capture.ipynb?token=${config.token}`,{waitUntil:'domcontentloaded'});
 const cell=page.locator('.jp-NotebookPanel:visible .jp-Cell').first();await cell.locator('.cm-content').waitFor();
 const no=page.getByRole('button',{name:'No',exact:true});if(await no.isVisible())await no.click();
 await page.waitForFunction(()=>window.jupyterapp?.shell.currentWidget?.sessionContext.session?.kernel);
 stage='plain-kernel baseline';await kernel("import json; print('MSV_CAPTURE_JSON '+json.dumps(True))");
 report.plain_kernel_page_errors=report.page_errors.length;
 await cell.locator('.cm-content').click();await page.getByRole('button',{name:/Run this cell and advance/}).click();
 await page.waitForFunction(()=>window.__captureControllers?.[0]?.getStructureData()?.elementCount===62);
 await observeDraws(page);
 await page.evaluate(()=>{
  window.__captureTraffic=[];window.__captureProtocolTraffic=[];window.__captureKernelErrors=[];
  const kernel=window.jupyterapp.shell.currentWidget.sessionContext.session.kernel;
  kernel.anyMessage.connect((_sender,args)=>{
   const content=args.msg?.content?.data?.content,data=content?.payload??content;
   if(args.msg?.header?.msg_type==='error'&&window.__captureKernelErrors.length<12)window.__captureKernelErrors.push({ename:args.msg.content.ename,evalue:args.msg.content.evalue});
   if(data?.event==='visual_state_snapshot')window.__captureTraffic.push(JSON.parse(JSON.stringify(data)));
   if(data?.event||data?.op){window.__captureProtocolTraffic.push({direction:args.direction,event:data.event,op:data.op,generation:data.generation,
    target:data.target_endpoint_id,viewer:data.viewer_id,session:data.session_id,stream:data.stream_id});if(window.__captureProtocolTraffic.length>512)window.__captureProtocolTraffic.shift();}
  });
 });
 await receivePython(page,'state','notebook');await receivePython(page,'session','notebook');
 await receiveStudio(page,'state','notebook');await receiveStudio(page,'session','notebook');
 stage='canvas popup';const popup=await openCanvas();
 await observeDraws(popup);
 await receiveStudio(popup,'state','popup');await receiveStudio(popup,'session','popup');await popup.close();
 await page.bringToFront();
 await receiveJupyterMoving({page,kernel,config,report,openWork,openCanvas,setStage:value=>{stage=value;}});
 // Delay actual rendered replies, never supply fake camera/scientific data.
 await page.bringToFront();const work=await openWork(page);
 await delayedReply(work,'cancel');await delayedReply(work,'timeout');
 report.known_host_diagnostics=report.page_errors.filter(error=>error.message==='No active debugger session');
 report.unexpected_page_errors=report.page_errors.filter(error=>error.message!=='No active debugger session');
 assert.deepEqual(report.unexpected_page_errors,[]);report.outcome='passed';
}catch(error){report.outcome='failed';report.stage=stage;report.error_type=error?.name;report.error=String(error);report.stack=error?.stack;process.exitCode=1;await page?.screenshot({path:config.output+'/failure.png'}).catch(()=>{});}
finally{await writeFile(config.output+'/observations.json',JSON.stringify(report,null,2));await browser?.close();console.log(JSON.stringify({outcome:report.outcome,stage,save_restore:report.capture_restore_cases,studio:report.studio_cases}));}
