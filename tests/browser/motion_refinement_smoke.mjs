// Motion is tested through actual browser-computed styles and live scenario requests.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

export async function checkMotionRefinement({evaluate,send,waitFor,click,viewport}){
  const root=path.resolve('.artifacts/motion-refinement'),after=path.join(root,'after');
  const frames=path.join(root,'recording-frames');mkdirSync(after,{recursive:true});mkdirSync(frames,{recursive:true});
  const metrics=[];
  async function capture(name){await pause(160);const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(path.join(after,`${name}.png`),Buffer.from(result.data,'base64'));}
  async function reloadReady(){const old=await evaluate('performance.timeOrigin');await send('Page.reload');await waitFor(`performance.timeOrigin!==${old}`);await waitFor("document.getElementById('workspace-status')?.textContent!=='Loading saved events…'&&document.getElementById('submit-btn')?.disabled===false");await evaluate("scrollTo({top:0,behavior:'instant'})");}
  const style=()=>evaluate("JSON.stringify([...document.querySelectorAll('.scene-depth')].map(el=>({name:el.className,translate:getComputedStyle(el).translate,rotate:getComputedStyle(el).rotate,state:getComputedStyle(el).animationPlayState})))");
  await viewport(1440);await send('Emulation.setEmulatedMedia',{features:[]});
  await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'});document.getElementById('toast').hidden=true");
  await waitFor("['active','gentle'].includes(document.getElementById('cinematic-hero').dataset.motion)");
  await pause(1500);const idleBefore=await style();await pause(450);assert.notEqual(await style(),idleBefore,'Idle scene must move without pointer input');
  assert.equal(await evaluate("document.querySelectorAll('.scene-depth').length"),6);
  await click('#scene-motion-toggle');await waitFor("document.getElementById('cinematic-hero').dataset.motion==='paused'");await pause(150);
  const frozen=await style();await pause(300);assert.equal(await style(),frozen,'Pause must freeze all independent scene layers');
  assert(await evaluate("[...document.querySelectorAll('.scene-depth')].every(el=>getComputedStyle(el).animationPlayState==='paused')"));
  await reloadReady();await waitFor("document.getElementById('scene-motion-toggle')?.textContent==='Resume motion'");
  await click('#scene-motion-toggle');await waitFor("['active','gentle'].includes(document.getElementById('cinematic-hero').dataset.motion)");
  await evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))");
  assert.equal(await evaluate("document.getElementById('cinematic-hero').dataset.motion"),'paused');
  assert(await evaluate("[...document.querySelectorAll('.scene-depth')].every(el=>getComputedStyle(el).animationPlayState==='paused')"));
  await evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))");
  await evaluate("document.getElementById('experience').scrollIntoView({behavior:'instant'})");await waitFor("document.getElementById('cinematic-hero').dataset.motion==='paused'");
  await evaluate("scrollTo({top:0,behavior:'instant'})");await waitFor("['active','gentle'].includes(document.getElementById('cinematic-hero').dataset.motion)");
  const point=await evaluate("(()=>{const r=document.getElementById('scene-viewport').getBoundingClientRect();return{x:r.left+r.width*.75,y:r.top+r.height*.3};})()");
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});await pause(200);
  if(await evaluate("matchMedia('(hover:hover) and (pointer:fine)').matches")){
    assert(await evaluate("Math.abs(parseFloat(document.getElementById('scene-camera').style.getPropertyValue('--invitation-tilt-y')))<=2.2"));
    assert.notEqual(await evaluate("document.getElementById('scene-camera').style.getPropertyValue('--invitation-tilt-y')"),'');
  }
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:1,y:1});await pause(100);
  await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});
  await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...point,radiusX:2,radiusY:2}]});
  await send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:point.x+8,y:point.y+2,radiusX:2,radiusY:2}]});
  await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.equal(await evaluate("document.getElementById('scene-camera').style.getPropertyValue('--invitation-tilt-y')"),'');
  await send('Emulation.setTouchEmulationEnabled',{enabled:false});
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await waitFor("document.getElementById('cinematic-hero').dataset.motion==='static'");
  assert(await evaluate("document.getElementById('scene-motion-toggle').disabled"));
  assert(await evaluate("[...document.querySelectorAll('.scene-depth')].every(el=>getComputedStyle(el).animationName==='none')"));
  await capture('reduced-motion');await send('Emulation.setEmulatedMedia',{features:[]});
  // Buffered layout-shift observations on fresh local document loads, not an FPS benchmark.
  const observer=await send('Page.addScriptToEvaluateOnNewDocument',{source:"window.motionLayoutShifts=[];if(PerformanceObserver.supportedEntryTypes.includes('layout-shift')){new PerformanceObserver(list=>{for(const item of list.getEntries())if(!item.hadRecentInput)window.motionLayoutShifts.push(item.value)}).observe({type:'layout-shift',buffered:true})}"});
  for(const width of [1440,1024,768,390,320]){
    await viewport(width,900);await reloadReady();await waitFor("document.getElementById('scene-budget-value').textContent.includes('20,000')");await pause(700);
    const dimensions=await evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,shifts:window.motionLayoutShifts||[]})');
    assert(dimensions.scroll<=dimensions.width+1,`Overflow at ${width}: ${JSON.stringify(dimensions)}`);
    const cls=dimensions.shifts.reduce((total,value)=>total+value,0);metrics.push({width,cls,layoutShiftEntries:dimensions.shifts.length});
    assert(cls<.1,`Unexpected initial layout instability at ${width}: ${cls}`);
    await capture(`homepage-${width}`);await evaluate("document.getElementById('cinematic-hero').scrollIntoView({block:'center',behavior:'instant'})");await capture(`scene-${width}`);
  }
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:observer.identifier});
  writeFileSync(path.join(root,'layout-observations.json'),JSON.stringify(metrics,null,2));
  await viewport(1440);await evaluate("scrollTo({top:0,behavior:'instant'});document.getElementById('toast').hidden=true");await pause(700);
  const recording=[],start=Date.now();
  for(let i=0;i<12;i++){
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const name=`frame-${String(i).padStart(2,'0')}.png`;
    writeFileSync(path.join(frames,name),Buffer.from(shot.data,'base64'));recording.push({file:`recording-frames/${name}`,at:Date.now()-start});await pause(100);
  }
  writeFileSync(path.join(root,'recording.json'),JSON.stringify(recording,null,2));
  writeFileSync(path.join(root,'recording.html'),`<!doctype html><html lang="en"><meta charset="utf-8"><title>Planora AI actual browser recording</title><style>body{background:#fbf8f2;color:#18243c;font:16px system-ui;margin:24px}img{width:100%;max-width:1440px;border:1px solid #ddd}button{padding:12px;margin:12px 8px 12px 0}input{width:220px}</style><h1>Planora AI motion refinement</h1><p>12 actual browser captures. A short frame sequence, not a synthetic scene or an FPS benchmark.</p><button id="play">Pause playback</button><label>Frame <input id="frame" type="range" min="0" max="11" value="0"></label><img id="image" alt="Recorded Planora AI homepage frame"><script>const frames=${JSON.stringify(recording)};let index=0,playing=true,timer;const image=document.getElementById('image'),slider=document.getElementById('frame'),button=document.getElementById('play');function render(){image.src=frames[index].file;slider.value=index}function tick(){if(playing){const next=(index+1)%frames.length,delay=next===0?250:Math.max(70,frames[next].at-frames[index].at);index=next;render();timer=setTimeout(tick,delay)}}button.onclick=()=>{playing=!playing;button.textContent=playing?'Pause playback':'Play';clearTimeout(timer);if(playing)tick()};slider.oninput=()=>{index=Number(slider.value);render()};render();timer=setTimeout(tick,150);</script></html>`);
  const events=await evaluate("fetch('/api/events').then(r=>r.json())");
  await click('a[href="#experience"]');await click('#demo-budget-tab');
  await waitFor("document.querySelectorAll('.ring-segment').length>0");
  const shares=await evaluate("[...document.querySelectorAll('.ring-segment')].map(el=>Number(el.getAttribute('stroke-dasharray').split(' ')[0]))");
  const expected=await evaluate("fetch('/api/demo').then(r=>r.json()).then(d=>d.workspace.plan.budget_lines.map(line=>line.percent))");assert.deepEqual(shares,expected);
  await capture('budget-allocation');await click('#demo-rescue-tab');await waitFor("document.getElementById('demo-content').dataset.stage==='disruption'");
  await click('#demo-content .demo-option');await waitFor("document.getElementById('demo-content').dataset.stage==='review'");
  assert(await evaluate("document.querySelector('#demo-content .primary').disabled"));await capture('recovery-review');
  await click('#demo-discard-btn');assert(await evaluate("document.getElementById('demo-content').textContent.includes('Demo preview discarded')"));
  assert.deepEqual(await evaluate("fetch('/api/events').then(r=>r.json())"),events);
  await click('#demo-budget-tab');await evaluate("scrollTo({top:0,behavior:'instant'})");
  console.log('PASS independent idle layers, pause/persistence, hidden/offscreen shutdown, bounded tilt/touch, reduced motion, 1440/1024/768/390/320 overflow/CLS observations, true allocation shares and demo discard nonmutation; motion screenshots/recording saved');
}

export async function checkRescueFailureFeedback({evaluate,send,waitFor,click,savedEvent,id}){
  const before=await savedEvent(id);
  await send('Network.setBlockedURLs',{urls:[`*/api/events/${id}/scenarios/*/apply`]});
  await click('#scenario-approval');await click('#scenario-apply');
  await waitFor("!document.getElementById('scenario-error').hidden&&!document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('rescue-action-status').dataset.tone"),'error');
  assert.deepEqual(await savedEvent(id),before);
  assert.equal(await evaluate("document.querySelectorAll('#rescue-options .recovery-option').length"),2);
  await send('Network.setBlockedURLs',{urls:[]});await click('#scenario-approval');
  console.log('PASS failed real Rescue application preserves saved state/options and shows no success feedback before server confirmation');
}
