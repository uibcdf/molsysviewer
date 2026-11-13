/** Actual notebook/kernel Movie authoring, native draws and endpoint lifetime. */
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';

export async function receiveJupyterMovie({page,kernel,config,report,openCanvas,rotate,observePopupChildren,setStage}){
 const status=()=>kernel("print('MSV_CAPTURE_JSON '+json.dumps(movie_status()))");
 const idle=target=>target.waitForFunction(()=>{
  const p=window.__captureControllers[0].groupPanel.moviePanel;
  return p?.state&&!p.state.busy&&p.pending===null;
 });
 async function openMovie(target){
  await target.evaluate(()=>{const c=window.__captureControllers[0];c.setPanelMode('navigate',true);c.groupPanel.setExpanded(true);c.groupPanel.openSection('movie');});
  await target.getByRole('tab',{name:'Timeline',exact:true}).waitFor();await idle(target);
 }
 async function fresh(target,index=0){
  return target.evaluate(index=>new Promise((resolve,reject)=>{
   const c=window.__captureControllers[index],canvas=c.plugin.canvas3d;let replay=true;
   const sub=canvas.didDraw.subscribe(()=>{
    if(replay)return;
    const frame=c.trajectory.getTrajectoryState().currentFrame,region=c.state.regionIndex.get('site');
    const observations={frame,trajectory:c.trajectory.isCaptureFrameReady(frame),annotations:c.annotations.isGeometryCurrent(),
     region_hidden:region?.hidden,representations:region?.representations.map(ref=>c.plugin.state.data.cells.get(ref)?.state.isHidden),camera:c.getCameraSnapshot()};
    clearTimeout(timer);sub.unsubscribe();resolve(observations);
   });replay=false;
   const timer=setTimeout(()=>{sub.unsubscribe();reject(new Error('Movie needs a fresh native draw'));},5000);
   canvas.requestDraw();
  }),index);
 }
 async function nextTrack(target,name,domain,prop){
  await target.getByRole('button',{name:'New track',exact:true}).click();
  await target.getByLabel('Track name',{exact:true}).fill(name);
  await target.getByLabel('Target',{exact:true}).selectOption(domain);
  if(prop)await target.getByLabel('Property',{exact:true}).selectOption(prop);
 }
 let popup,panel;
 const phase=value=>{setStage(value);console.log(value);};
 report.movie_authoring_cases=0;
 try{
  phase('Movie notebook authoring');await openMovie(page);
  await page.getByLabel('Duration (seconds)',{exact:true}).fill('0.75');
  await page.getByRole('button',{name:'Capture initial scene',exact:true}).click();await idle(page);
  let observed=await status();assert.equal(observed.recipe.molsysmovie_version,2);assert.equal(observed.recipe.duration_ms,750);
  await page.getByLabel('Track name',{exact:true}).fill('camera');
  await page.getByRole('button',{name:'Capture this camera as key',exact:true}).click();await idle(page);
  await nextTrack(page,'frames','structure');
  await page.getByLabel('Key time (seconds)',{exact:true}).fill('0.25');
  await page.getByLabel('Structure',{exact:true}).fill('2');
  await page.getByRole('button',{name:'Save key',exact:true}).click();await idle(page);
  await nextTrack(page,'hide-site','region');
  await page.getByLabel('Object name in the initial scene',{exact:true}).fill('site');
  await page.getByLabel('Key time (seconds)',{exact:true}).fill('0.25');
  await page.getByLabel('Visible',{exact:true}).uncheck();
  await page.getByRole('button',{name:'Save key',exact:true}).click();await idle(page);
  assert.equal((await status()).recipe.tracks.length,3);report.movie_authoring_cases++;

  phase('Movie Python edit');
  await page.getByLabel('Track name',{exact:true}).fill('kept notebook draft');
  await kernel("view.movie.set_duration(1000)\nprint('MSV_CAPTURE_JSON '+json.dumps(True))");
  await page.getByRole('button',{name:'Use kept draft',exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Save key',exact:true}).isDisabled(),true);
  await page.getByRole('button',{name:'Use kept draft',exact:true}).click();await idle(page);
  assert.equal(await page.getByLabel('Track name',{exact:true}).inputValue(),'kept notebook draft');
  report.movie_authoring_cases++;

  phase('Movie notebook seek');
  await page.getByRole('tab',{name:'Preview',exact:true}).click();
  await page.getByLabel('Movie time (seconds)',{exact:true}).fill('0.4');
  await page.getByRole('button',{name:'Go to time',exact:true}).click();await idle(page);
  observed=await fresh(page);assert.equal(observed.frame,2);assert.equal(observed.trajectory,true);assert.equal(observed.annotations,true);
  assert.equal(observed.region_hidden,true);assert.ok(observed.representations.length>0&&observed.representations.every(Boolean));
  assert.equal((await status()).frame,2);report.movie_authoring_cases++;

  phase('Movie popup camera');popup=await openCanvas();
  popup.on('pageerror',error=>report.page_errors.push({stage:'Movie popup camera',message:error.message}));
  await rotate(popup);const rotated=await fresh(popup);
  await openMovie(popup);
  await popup.getByRole('button',{name:/^camera · Camera pose ·/}).click();await idle(popup);
  await popup.getByLabel('Key time (seconds)',{exact:true}).fill('0.5');
  const mark=await page.evaluate(()=>window.__captureProtocolTraffic.length);
  await popup.getByRole('button',{name:'Capture this camera as key',exact:true}).click();await idle(popup);
  observed=await status();const cameraTrack=observed.recipe.tracks.find(t=>t.tag==='camera');assert.equal(cameraTrack.keys.length,2);
  for(const key of ['position','target','up'])assert.ok(cameraTrack.keys[1].value[key].every((v,i)=>Math.abs(v-rotated.camera[key][i])<1e-4));
  const endpoint=await popup.evaluate(()=>window.molsysviewer_popup_channel.popupEndpointId);
  const requests=await page.evaluate(mark=>window.__captureProtocolTraffic.slice(mark).filter(row=>row.op==='request_visual_state'),mark);
  assert.ok(requests.length>0&&requests.every(row=>row.target===endpoint),'Camera capture must address its actual popup');
  report.movie_authoring_cases++;

  phase('Movie detached preview');await observePopupChildren(popup);
  const opened=popup.waitForEvent('popup');await popup.getByTitle('Popout panel to external window',{exact:true}).click();panel=await opened;
  panel.on('pageerror',error=>report.page_errors.push({stage:'Movie detached preview',message:error.message}));
  await panel.waitForFunction(()=>!!window.__captureControllers?.[0]);await openMovie(panel);
  await panel.getByRole('tab',{name:'Preview',exact:true}).click();
  await panel.getByLabel('Loop preview',{exact:true}).check();
  await panel.getByRole('button',{name:'Play',exact:true}).click();
  await panel.waitForFunction(()=>window.__captureControllers[0].groupPanel.moviePanel.state.busy==='movie_play');
  const pythonPause=await kernel("await view.movie.pause_async()\nprint('MSV_CAPTURE_JSON '+json.dumps({'paused':view.movie._playback is None,'pending':len(view._frontend_requests._pending)}))");
  assert.deepEqual(pythonPause,{paused:true,pending:0});await idle(panel);
  await kernel("_python_preview=asyncio.create_task(view.movie.play_async(loop=True))\nprint('MSV_CAPTURE_JSON '+json.dumps(True))");
  await panel.waitForFunction(()=>window.__captureControllers[0].groupPanel.moviePanel.state.busy==='movie_play');
  assert.equal(await panel.getByRole('button',{name:'Cancel operation',exact:true}).count(),0);
  await panel.getByRole('button',{name:'Pause',exact:true}).click();await idle(panel);
  const guiPause=await kernel("await _python_preview\nprint('MSV_CAPTURE_JSON '+json.dumps({'paused':view.movie._playback is None,'pending':len(view._frontend_requests._pending)}))");
  assert.deepEqual(guiPause,{paused:true,pending:0});
  report.movie_python_studio_pause=true;
  await panel.getByRole('button',{name:'Play',exact:true}).click();
  await panel.waitForFunction(()=>window.__captureControllers[0].groupPanel.moviePanel.state.busy==='movie_play');
  await panel.getByRole('button',{name:'Pause',exact:true}).click();await idle(panel);
  observed=await status();assert.equal(observed.job,false);assert.equal(observed.pending,0);report.movie_authoring_cases++;

  phase('Movie detached export');const path=config.output+'/notebooks/studio.zip';
  await panel.getByRole('tab',{name:'Export',exact:true}).click();
  await panel.getByLabel('Output path in Python session (.mp4, .webm, .zip or .html)',{exact:true}).fill(path);
  await panel.getByLabel('Frames per second',{exact:true}).fill('2');
  await panel.getByLabel('Width (pixels)',{exact:true}).fill('320');
  await panel.getByLabel('Height (pixels)',{exact:true}).fill('180');
  await panel.getByRole('button',{name:'Export Movie',exact:true}).click();await idle(panel);
  const archive=await kernel("with zipfile.ZipFile(_output/'studio.zip') as _zip:\n    _manifest=json.loads(_zip.read('manifest.json'))\n    _pngs=[name for name in _zip.namelist() if name.endswith('.png')]\nassert _manifest['recipe']==view.movie.to_dict()\nprint('MSV_CAPTURE_JSON '+json.dumps({'frames':len(_pngs),'resolution':_manifest['resolution'],'bytes':(_output/'studio.zip').stat().st_size}))");
  assert.equal(archive.frames,2);assert.deepEqual(archive.resolution,{width:320,height:180});assert.ok(archive.bytes>1000);
  await panel.screenshot({path:config.output+'/movie-export.png'});report.movie_archive=archive;report.movie_authoring_cases++;

  phase('Movie session recovery');await page.bringToFront();
  const restored=await kernel("await view.save_session_async(_output/'studio.msv')\nrestored=msv.load_session(_output/'studio.msv')\nassert restored.molsys is not view.molsys\nnp.testing.assert_array_equal(msv.pyunitwizard.get_value(restored.get_coordinates(),to_unit='angstrom'),_coordinates)\nassert restored.movie.to_dict()==view.movie.to_dict()\nassert restored.movie.evaluate(400)==view.movie.evaluate(400)\nprint('MSV_CAPTURE_JSON '+json.dumps({'independent':True,'recipe_preserved':True,'source_unchanged':movie_status()['source_unchanged']}))");
  assert.deepEqual(restored,{independent:true,recipe_preserved:true,source_unchanged:true});report.movie_authoring_cases++;

  phase('Movie close cancellation');await panel.bringToFront();
  await panel.getByRole('tab',{name:'Timeline',exact:true}).click();
  await panel.getByRole('button',{name:/^camera · Camera pose ·/}).click();await idle(panel);
  await panel.getByLabel('Key time (seconds)',{exact:true}).fill('0.75');
  const before=(await status()).recipe;
  await page.evaluate(()=>{
   const model=window.__captureControllers[0].model,send=model.send.bind(model);window.__movieHeld=[];
   window.__releaseMovieHeld=()=>{model.send=send;for(const event of window.__movieHeld.splice(0))send(event);};
   model.send=(event,...rest)=>{if((event?.payload??event)?.event==='visual_state_snapshot'){window.__movieHeld.push(event);return;}return send(event,...rest);};
  });
  await panel.getByRole('button',{name:'Capture this camera as key',exact:true}).click();
  await page.waitForFunction(()=>window.__movieHeld.length===1);
  await panel.close();panel=undefined;
  await page.waitForFunction(()=>!window.__captureControllers[0].groupPanel.moviePanel.state.busy);
  await page.evaluate(()=>window.__releaseMovieHeld());
  observed=await status();assert.equal(observed.job,false);assert.equal(observed.pending,0);assert.deepEqual(observed.recipe,before);
  report.movie_authoring_cases++;report.movie_source_unchanged=observed.source_unchanged;
  report.movie_cancel_late_reply_preserved=true;
  await kernel("restored.close()\nview.close()\nprint('MSV_CAPTURE_JSON '+json.dumps({'closed':view.closed and restored.closed}))");
  await writeFile(config.output+'/movie-observations.json',JSON.stringify({cases:report.movie_authoring_cases,archive,cancel_late_reply:true,source_unchanged:true,python_studio_pause:true},null,2));
 }catch(error){
  const inspect=target=>target?.evaluate(()=>{
   const c=window.__captureControllers?.[0],p=c?.groupPanel.moviePanel,frame=c?.trajectory.getTrajectoryState().currentFrame;
   return {hidden:document.hidden,frame,editor:p&&{state:p.state,pending:p.pending,message:p.message},
    native:c&&{trajectory:c.trajectory.isCaptureFrameReady(frame),annotations:c.annotations.isGeometryCurrent(),movie:c.movie.isCaptureSafe},
    traffic:window.__captureProtocolTraffic?.slice(-40),replies:window.__captureTraffic?.slice(-4)};
  }).catch(e=>({diagnostic_error:e.name}));
  report.movie_failure={pages:await Promise.all([inspect(page),inspect(popup),inspect(panel)])};
  await writeFile(config.output+'/movie-failure-before-kernel.json',JSON.stringify(report.movie_failure,null,2));
  let diagnosticTimer;
  try{
   report.movie_failure.kernel=await Promise.race([status(),new Promise((_,reject)=>{diagnosticTimer=setTimeout(()=>reject(new Error('Kernel diagnostic deadline')),5000);})]);
  }catch(e){report.movie_failure.kernel={diagnostic_error:e.name};}
  finally{clearTimeout(diagnosticTimer);}
  await panel?.screenshot({path:config.output+'/movie-failure.png'}).catch(()=>{});
  throw error;
 }finally{await panel?.close();await popup?.close();}
}
