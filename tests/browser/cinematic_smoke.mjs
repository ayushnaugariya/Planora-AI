// Actual DOM/CSS/interaction checks; no browser library or mocked renderer.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

export async function checkCinematic({evaluate,send,waitFor,click,viewport}){
  const folder=path.resolve('.artifacts/cinematic');mkdirSync(folder,{recursive:true});
  async function capture(name){
    await pause(400);
    const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    writeFileSync(path.join(folder,`${name}.png`),Buffer.from(result.data,'base64'));
  }
  const ready=()=>waitFor("document.getElementById('workspace-status')?.textContent!=='Loading saved events…'&&!document.getElementById('submit-btn').disabled");
  async function reloadReady(){
    const old=await evaluate('performance.timeOrigin');
    await send('Page.reload');await waitFor(`performance.timeOrigin!==${old}`);await ready();
    await evaluate("scrollTo({top:0,behavior:'instant'})");
  }
  await viewport(1440);await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'});document.getElementById('toast').hidden=true");
  await waitFor("document.getElementById('scene-budget-value').textContent.includes('20,000')");
  assert(await evaluate("getComputedStyle(document.getElementById('scene-camera')).transform.startsWith('matrix3d')"));
  await click('[data-scene-view="timeline"]');
  assert(await evaluate("document.getElementById('scene-insight-detail').textContent.includes('Fictional example:')"));
  await click('[data-scene-view="rescue"]');
  assert(await evaluate("document.getElementById('cinematic-hero').classList.contains('scene-recovery')"));
  assert.equal(await evaluate("document.getElementById('demo-rescue-tab').getAttribute('aria-selected')"),'true');
  await click('[data-scene-view="budget"]');
  assert(await evaluate("document.getElementById('scene-insight-detail').textContent.includes('recorded estimates')"));
  await click('[data-scene-view="occasion"]');
  await evaluate("scrollTo({top:0,behavior:'instant'})");await capture('hero-desktop-1440');
  const point=await evaluate("(()=>{const r=document.getElementById('scene-viewport').getBoundingClientRect();return{x:r.left+r.width*.8,y:r.top+r.height*.3};})()");
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});await pause(100);
  if(await evaluate("matchMedia('(hover:hover) and (pointer:fine)').matches")){
    assert.notEqual(await evaluate("document.getElementById('scene-camera').style.getPropertyValue('--scene-y')"),'');
  }
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:point.x+10,y:point.y});await pause(100);
  assert.equal(await evaluate("document.getElementById('scene-camera').style.getPropertyValue('--scene-y')"),'');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.scene-invitation')).animationName"),'none');
  await capture('hero-reduced-motion');
  await send('Emulation.setEmulatedMedia',{features:[]});
  await evaluate("document.getElementById('experience').scrollIntoView({behavior:'instant'})");await pause(150);
  assert.equal(await evaluate("document.getElementById('scene-camera').style.getPropertyValue('--scene-y')"),'');
  for(const width of [768,390]){
    await viewport(width,900);await evaluate("scrollTo({top:0,behavior:'instant'})");await pause(150);
    await capture(`hero-${width}`);
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),await evaluate("JSON.stringify({width:innerWidth,scroll:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('#landing-view *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(el=>el.className)})"));
    await evaluate("document.getElementById('cinematic-hero').scrollIntoView({block:'center',behavior:'instant'})");await capture(`scene-${width}`);
  }
  await viewport(1440);await evaluate("scrollTo({top:0,behavior:'instant'})");
  await send('Network.setBlockedURLs',{urls:['*/static/assets/botanical.svg','*/api/demo']});
  await reloadReady();await waitFor("document.querySelector('#demo-content button')?.textContent==='Retry example'");
  await click('[data-scene-view="rescue"]');assert(await evaluate("document.getElementById('scene-insight-detail').textContent.includes('Unknown costs')"));
  assert.equal(await evaluate("document.getElementById('scene-budget-value').textContent"),'Room for the details.');
  await evaluate("scrollTo({top:0,behavior:'instant'})");await capture('hero-assets-unavailable');
  await send('Network.setBlockedURLs',{urls:[]});
  await send('Emulation.setScriptExecutionDisabled',{value:true});await send('Page.reload');await pause(700);
  const dom=await send('DOM.getDocument');
  const node=await send('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'.scene-viewport'});
  const box=await send('DOM.getBoxModel',{nodeId:node.nodeId});assert(box.model.width>200&&box.model.height>200);
  await capture('hero-no-javascript');
  await send('Emulation.setScriptExecutionDisabled',{value:false});await reloadReady();
  await waitFor("document.getElementById('scene-budget-value').textContent.includes('20,000')");
  console.log('PASS CSS 3D scene/hotspots, real demo linkage, desktop pointer/reduced/offscreen behavior, 1440/768/390 screenshots, unavailable artwork/demo and static no-JavaScript fallback');
}

export async function checkLanguageAndQuotes({evaluate,send,waitFor,click,values,savedEvent,id}){
  await evaluate(`location.hash='#/event/${id}/scenarios'`);await waitFor("!document.getElementById('panel-scenarios').hidden");
  const before=await savedEvent(id);
  await evaluate("document.getElementById('scenario-interpret-form').closest('details').open=true");
  await values({'scenario-question':'What if we increase the guest count by 30?'});
  await click('#scenario-interpret-form button');await waitFor("document.getElementById('scenario-status').textContent.includes('Built-in saved-state suggestion')&&!document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('scenario-guests').value"),'90');assert.deepEqual(await savedEvent(id),before);
  // Cancel the newly suggested draft, keeping every stored preview.
  await evaluate("(()=>{const previous=confirm;try{window.confirm=()=>true;document.querySelector('#scenario-form button.ghost').click();}finally{window.confirm=previous;}})()");
  await values({'scenario-question':'What happens if the event date changes?'});await click('#scenario-interpret-form button');
  await waitFor("document.getElementById('scenario-status').textContent.includes('Which exact date')&&!document.getElementById('submit-btn').disabled");
  await click('#quote-comparison summary');await values({'quote-category':'catering','quote-a':'120.15','quote-b':'140.25'});
  const countBefore=await evaluate(`fetch('/api/events/${id}/scenarios').then(r=>r.json()).then(a=>a.length)`);
  await evaluate("window.cinematicOriginalFetch=window.fetch;window.cinematicQuotePosts=0;window.fetch=(url,options)=>{if(String(url).endsWith('/scenarios')&&options?.method==='POST'&&++window.cinematicQuotePosts===2)return Promise.reject(new TypeError('Test network failure'));return window.cinematicOriginalFetch(url,options);}");
  await click('#quote-compare-button');await waitFor("document.getElementById('quote-comparison-status').textContent.startsWith('1 preview(s) saved; comparison did not complete.')&&!document.getElementById('quote-compare-button').disabled");
  await evaluate("window.fetch=window.cinematicOriginalFetch;delete window.cinematicOriginalFetch;delete window.cinematicQuotePosts");
  assert.equal(await evaluate(`fetch('/api/events/${id}/scenarios').then(r=>r.json()).then(a=>a.length)`),countBefore+1);
  assert.equal(await evaluate("document.getElementById('quote-b').value"),'140.25');
  assert.deepEqual(await savedEvent(id),before);
  await evaluate("(()=>{const previous=confirm;try{window.confirm=()=>false;document.getElementById('new-event-btn').click();}finally{window.confirm=previous;}})()");
  assert.equal(await evaluate("JSON.parse(localStorage.getItem('eventra:selected-event'))"),id);
  assert.equal(await evaluate("document.getElementById('quote-a').value"),'120.15');
  await click('#quote-compare-button');await waitFor("document.querySelectorAll('#quote-comparison-options article').length===2&&!document.getElementById('quote-compare-button').disabled");
  assert.deepEqual(await savedEvent(id),before);
  await click('#quote-comparison-options button');await waitFor("!document.getElementById('scenario-preview').hidden");
  assert(await evaluate("document.getElementById('scenario-apply').disabled"));
  await evaluate("document.getElementById('quote-comparison').scrollIntoView({behavior:'instant'});document.getElementById('toast').hidden=true");
  const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  writeFileSync(path.resolve('.artifacts/cinematic/quote-comparison.png'),Buffer.from(result.data,'base64'));
  console.log('PASS relative-language suggestion, missing-date clarification, honest partial quote-comparison failure, retained inputs, two real isolated quote previews and disabled application before approval');
}
