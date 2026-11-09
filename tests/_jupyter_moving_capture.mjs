import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

/** Actual anywidget traffic only: hold/release real requests, never supply science. */
export async function receiveJupyterMoving({page,kernel,config,report,openWork,openCanvas,setStage}) {
 const json=expression=>`print('MSV_CAPTURE_JSON '+json.dumps(${expression}))`;
 const harness=await readFile(config.viewer_root+'/molsysviewer/js/tests/e2e/harness.bundle.js','utf8');
 let popup;
 report.moving_cases=[];
 setStage('moving setup');
 await page.evaluate(()=>{
  const model=window.__captureControllers[0].model;
  const trace=window.__jupMovingPreparation=[];
  model.on('msg:custom',(event,buffers)=>{
   const body=event?.payload??event;
   trace.push({op:body?.op,event:body?.event,action:body?.action,generation:body?.generation,
    target:body?.target_endpoint_id,buffers:buffers?.length??0});
   if(trace.length>128)trace.shift();
  });
 });
 await kernel(`import runpy\n_moving=runpy.run_path(${JSON.stringify(config.viewer_root+'/tests/_jupyter_moving_capture.py')})['configure'](view,_output,${JSON.stringify(config.viewer_root)})\n${json('True')}`);
 await page.addScriptTag({content:harness});
 await page.evaluate(()=>{
  const c=window.__captureControllers[0],model=c.model,send=model.send;
  const wire=window.__jupMovingWire={holding:false,held:[],queries:[],requests:[],replies:[],target:null};
  wire.release=()=>{wire.holding=false;for(const [event,rest] of wire.held.splice(0))send.call(model,event,...rest);};
  wire.releaseObserved=target=>{
   const active=target.__jupMoving?.active;
   if(!wire.holding||wire.target!==target||!active||active.changes.length<2)return;
   active.released={held_real_queries:wire.held.length,
    held_owners:[...new Set(wire.held.map(([event])=>(event?.payload??event)._query_endpoint_id))],
    requests:wire.requests.slice(wire.mark.requests),early_reply:wire.replies.length!==wire.mark.replies,
    frame_changes_after_request:[...active.changes]};
   wire.release();
  };
  model.send=function(event,...rest){
   const body=event?.payload??event;
   if(['request_dynamic_region_evaluation','request_interaction_frame'].includes(body?.event)){
    wire.queries.push(JSON.parse(JSON.stringify(body)));
    if(wire.queries.length>256)wire.queries.shift();
    if(wire.holding&&body._query_endpoint_id===wire.holdingOwner&&body.event==='request_dynamic_region_evaluation'){
     wire.held.push([event,rest]);return;
    }
   }
   if(body?.event==='visual_state_snapshot')wire.replies.push(JSON.parse(JSON.stringify(body)));
   return send.call(this,event,...rest);
  };
  const incoming=event=>{
   const body=event?.payload??event;
   if(body?.op!=='request_visual_state'||body.capture_version!==2)return;
   wire.requests.push(JSON.parse(JSON.stringify(body)));
   const target=wire.target?.__jupMoving;
   if(target)target.active={request_id:body.request_id,lastFrame:wire.target.__captureControllers[0].trajectory.getTrajectoryState().currentFrame,changes:[]};
  };
  model.on('msg:custom',incoming);
  wire.dispose=()=>{wire.release();model.send=send;model.off('msg:custom',incoming);};
 });
 async function observe(target){
  if(target!==page)await target.addScriptTag({content:harness});
  await target.evaluate(()=>{
   const c=window.__captureControllers[0],p=window.__jupMoving={draws:[],frames:[],active:null,readiness:[],captureStarts:[]};
   const prepare=c.prepareMovingVisualCapture;
   c.prepareMovingVisualCapture=function(...args){p.captureStarts.push({ms:performance.now(),frame:c.trajectory.getTrajectoryState().currentFrame});return prepare.apply(this,args);};
   p.releaseFrames=c.onTrajectoryState(state=>{
    if(p.frames.at(-1)!==state.currentFrame)p.frames.push(state.currentFrame);
    if(p.frames.length>64)p.frames.shift();
    if(p.active&&p.active.lastFrame!==state.currentFrame){
     p.active.lastFrame=state.currentFrame;p.active.changes.push(state.currentFrame);
     const authority=window.__jupMovingWire?window:window.opener;
     authority.__jupMovingWire.releaseObserved(window);
    }
   });
   let replay=true;
   p.subscription=c.plugin.canvas3d.didDraw.subscribe(()=>{
    if(replay)return;
    const frame=c.trajectory.getTrajectoryState().currentFrame;
    p.readiness.push({ms:performance.now(),frame,updating:c.plugin.state.data.behaviors.isUpdating.value,
     trajectory:c.trajectory.isCaptureFrameReady(frame),box:c.boxDisplay.isFrameReady(frame),shapes:c.shapes.isFrameReady(frame),
     interactions:c.interactions.isFrameReady(frame),annotations:c.annotations.isGeometryCurrent(),movie:c.movie.isCaptureSafe,
     dynamic:{applied:c.dynamicRegionEvaluationAppliedFrame,inflight:c.dynamicRegionEvaluationInFlight,pending:c.dynamicRegionEvaluationPendingFrame}});
    if(p.readiness.length>96)p.readiness.shift();
    const draw=window.Harness.inspectMovingCaptureDraw(c);
    if(draw)p.draws.push(draw);
    if(p.draws.length>128)p.draws.shift();
   });replay=false;
   p.dispose=()=>{p.releaseFrames();p.subscription.unsubscribe();c.prepareMovingVisualCapture=prepare;};
  });
 }
 async function capture(target,kind,origin,method){
  setStage(`Moving ${method} ${origin} ${kind}`);
  const name=`moving-${method.toLowerCase()}-${origin}.${kind==='state'?'json':'msv'}`;
  const work=await openWork(target);
  await work.getByLabel('Work file format',{exact:true}).selectOption(kind);
  await work.getByLabel('Path in Python session',{exact:true}).fill(config.output+'/notebooks/'+name);
  const before=await kernel(json("_moving['status']()"));assert.equal(before.playing,true);
  const owner=await target.evaluate(()=>window.molsysviewer_popup_channel?.popupEndpointId??`widget-host:${window.__captureControllers[0].model.get('runtime_session_id')}`);
  const mark=await page.evaluate(({origin,owner})=>{
   const wire=window.__jupMovingWire;
   wire.target=origin==='notebook'?window:window.__capturePopups.at(-1);
   wire.target.__jupMoving.active=null;
   wire.holding=true;
   wire.holdingOwner=owner;
   wire.mark={replies:wire.replies.length,requests:wire.requests.length};return wire.mark;
  },{origin,owner});
  await page.waitForFunction(()=>window.__jupMovingWire.held.length>0);
  let pending;
  if(method==='Studio')await work.getByRole('button',{name:'Save file',exact:true}).click();
  else{
   pending=kernel(json(`await _moving['save'](${JSON.stringify(name)},${JSON.stringify(kind)})`));
   void pending.catch(()=>{}); // Observe early rejection; the original is awaited below.
  }
  // Do not submit another kernel execute while the real async save is awaiting
  // comm traffic. The live browser observes/replays the actual scientific events.
  try{
   if(pending)await pending;
   else{
    await target.waitForFunction(()=>{const input=document.querySelector('[data-molsysviewer-work-file-path]');return input&&!input.disabled;});
    assert.match(await work.locator('[data-molsysviewer-work-file-status]').innerText(),/Saved/);
   }
   const held=await target.evaluate(()=>window.__jupMoving.active?.released);
   assert.ok(held&&held.held_real_queries>0);assert.equal(held.early_reply,false);
   assert.equal(held.requests.length,1);assert.equal(held.frame_changes_after_request.length,2);
   assert.deepEqual(held.held_owners,[owner]);
   assert.equal(held.requests[0].target_endpoint_id,origin==='notebook'?undefined:owner);
   const replies=await page.evaluate(mark=>window.__jupMovingWire.replies.slice(mark.replies),mark);
   assert.equal(replies.length,1);const reply=replies[0];assert.equal(reply.ok,true);assert.equal(reply.capture_version,2);
   assert.equal(reply.request_id,held.requests[0].request_id);
   const actual=await target.evaluate(reply=>{
    const p=window.__jupMoving;
    const draw=p.draws.findLast(d=>JSON.stringify(d.snapshot)===JSON.stringify(reply.snapshot)&&d.structure_index===reply.structure_index);
    return {draw,changes:p.active.changes};
   },reply);
   assert.ok(actual.draw,'The saved snapshot must match a real completed native draw.');
   const verified=await kernel(json(`_moving['inspect'](${JSON.stringify(name)},${JSON.stringify(kind)},json.loads(${JSON.stringify(JSON.stringify(actual.draw))}))`));
   assert.ok(verified.heartbeat>before.heartbeat);assert.equal(verified.pending_saves,0);assert.equal(verified.pending_captures,0);
   report.moving_cases.push({origin,method,kind,request_id:reply.request_id,...verified,
    held_real_queries:held.held_real_queries,held_query_owners:held.held_owners,frame_changes_after_request:held.frame_changes_after_request,native_draw:actual.draw});
   report.moving_capture_cases=report.moving_cases.length;
  }finally{
   await page.evaluate(()=>window.__jupMovingWire.release());
   if(pending)await pending.catch(()=>{});
  }
 }
 try{
  await observe(page);
  await kernel(json("_moving['start']()"));
  await page.waitForFunction(()=>window.__jupMoving.frames.length>=3);
  for(const kind of ['state','session'])for(const method of ['Studio','Python'])await capture(page,kind,'notebook',method);
  setStage('moving popup');popup=await openCanvas();await observe(popup);
  await popup.waitForFunction(()=>window.__jupMoving.frames.length>=3);
  for(const kind of ['state','session'])await capture(popup,kind,'popup','Studio');
  report.moving_transport=await page.evaluate(()=>({queries:window.__jupMovingWire.queries,requests:window.__jupMovingWire.requests,replies:window.__jupMovingWire.replies}));
 }catch(error){
  report.moving_failure=await page.evaluate(()=>{
   const c=window.__captureControllers[0],p=window.__jupMoving,wire=window.__jupMovingWire;
   const canvas=c.plugin.canvas3dContext?.canvas;
   return {frames:p?.frames,active:p?.active,draws:p?.draws.slice(-2),readiness:p?.readiness,captureStarts:p?.captureStarts,preparation:window.__jupMovingPreparation,operations:window.__captureOperationTrace,protocol:window.__captureProtocolTraffic,kernel_errors:window.__captureKernelErrors,
    playback:c.trajectory.getTrajectoryState(),sync:c.systemSyncState,
    canvas:{connected:canvas?.isConnected,visibility:canvas&&getComputedStyle(canvas).visibility,rect:canvas?.getBoundingClientRect().toJSON()},
    queries:wire.queries.slice(-12),requests:wire.requests.slice(-4),replies:wire.replies.slice(-4)};
  }).catch(failure=>({diagnostic_error:failure.name}));
  report.moving_failure.authority=await kernel(json("_moving['status']()")).catch(failure=>({diagnostic_error:failure.name}));
  if(popup)report.moving_failure.popup=await popup.evaluate(()=>({
   active:window.__jupMoving?.active,frames:window.__jupMoving?.frames,readiness:window.__jupMoving?.readiness,
   captureStarts:window.__jupMoving?.captureStarts,playback:window.__captureControllers[0].trajectory.getTrajectoryState(),
   capture_target_matches:window.opener.__jupMovingWire.target===window,
  })).catch(failure=>({diagnostic_error:failure.name}));
  throw error;
 }finally{
  await kernel(json("await _moving['stop']()"));
  await page.evaluate(()=>{window.__jupMovingWire.dispose();window.__jupMoving?.dispose();});
  if(popup){await popup.evaluate(()=>window.__jupMoving?.dispose()).catch(()=>{});await popup.close();}
 }
}
