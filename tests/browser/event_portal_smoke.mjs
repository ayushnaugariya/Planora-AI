import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';


async function reload({evaluate,send,waitFor}){
  const prior=await evaluate('performance.timeOrigin');await send('Page.reload');
  await waitFor(`performance.timeOrigin!==${prior}&&document.readyState==='complete'&&Boolean(document.getElementById('event-portal'))`);
}

export async function checkEventPortal({evaluate,send,waitFor,click,viewport,requireWebGL=false}){
  const artifacts=path.resolve('.artifacts/event-portal');mkdirSync(artifacts,{recursive:true});
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});
  await viewport(1440,960);await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'})");
  await waitFor("!document.getElementById('landing-view').hidden&&!document.getElementById('event-portal').hidden");
  const saved=await evaluate("fetch('/api/events').then(r=>r.json()).then(async rows=>Promise.all(rows.map(e=>fetch('/api/events/'+e.id).then(r=>r.json()))))");
  async function at(progress){
    await evaluate(`(()=>{const root=document.getElementById('event-portal'),r=root.getBoundingClientRect();scrollTo({top:scrollY+r.top+Math.max(0,r.height-innerHeight)*${progress},behavior:'instant'});})()`);
    await sleep(220);
    if(await evaluate("document.getElementById('event-portal').dataset.mode==='webgl'"))await waitFor(`Math.abs(Number(document.getElementById('event-portal').dataset.progress)-${progress})<.035`);
  }
  async function capture(name){const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(path.join(artifacts,name+'.png'),Buffer.from(shot.data,'base64'));}
  function pixels(){return evaluate(`(()=>{const canvas=document.getElementById('event-portal-canvas'),gl=canvas.getContext('webgl2'),p=new Uint8Array(canvas.width*canvas.height*4);gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,p);let hash=0,bright=0;for(let i=0;i<p.length;i+=16){hash=(hash*31+p[i]+p[i+1]*3+p[i+2]*7)|0;if(p[i]+p[i+1]+p[i+2]>330)bright++;}return{hash,bright,width:canvas.width,height:canvas.height}})()`);}
  await at(.08);await waitFor("['webgl','fallback'].includes(document.getElementById('event-portal').dataset.mode)");
  const mode=await evaluate("document.getElementById('event-portal').dataset.mode");
  const desktopTriangles=Number(await evaluate("document.getElementById('event-portal').dataset.triangles||0"));
  if(requireWebGL)assert.equal(mode,'webgl','The software-rendered test must create a real WebGL2 context');
  if(mode==='webgl'){
    const hashes=[],cameras=[];
    for(const [progress,name] of [[.08,'approach'],[.36,'separation'],[.59,'passage'],[.98,'universe']]){
      await at(progress);const sample=await pixels();hashes.push(sample.hash);cameras.push(await evaluate("Number(document.getElementById('event-portal').dataset.cameraZ)"));
      assert(sample.bright>200,'Real lit geometry must appear beyond the dark background');await capture('portal-'+name);
    }
    assert.equal(new Set(hashes).size,4);assert(cameras[0]>5&&cameras.at(-1)<=-3.9);assert(cameras.every((z,i)=>!i||z<cameras[i-1]));
    await at(.22);await sleep(600);const before=await pixels();
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:1160,y:390});await sleep(650);const after=await pixels();assert.notEqual(before.hash,after.hash,'Pointer must affect the rendered lighting/camera');
    await sleep(700);const idle=await evaluate("document.getElementById('event-portal').dataset.paints");await sleep(350);assert.equal(await evaluate("document.getElementById('event-portal').dataset.paints"),idle,'No perpetual idle WebGL rendering');
    await evaluate("document.getElementById('event-portal-pause').focus()");
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
    assert.equal(await evaluate("document.getElementById('event-portal-pause').getAttribute('aria-pressed')"),'true');await sleep(150);
    const pausedZ=await evaluate("document.getElementById('event-portal').dataset.cameraZ");
    await evaluate("scrollBy({top:300,behavior:'instant'})");await sleep(200);assert.equal(await evaluate("document.getElementById('event-portal').dataset.cameraZ"),pausedZ);
    await click('#event-portal-pause');await sleep(200);await at(.1);
    await evaluate("document.querySelector('[data-event-portal-go=\"0.98\"]').focus()");await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
    await waitFor("Number(document.getElementById('event-portal').dataset.progress)>.94");
    await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await waitFor("document.getElementById('event-portal').dataset.mode==='static'");
    await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});await waitFor("['pending','webgl'].includes(document.getElementById('event-portal').dataset.mode)");await at(.08);try{await waitFor("document.getElementById('event-portal').dataset.mode==='webgl'");}catch(error){throw new Error(error.message+' / portal state: '+JSON.stringify(await evaluate("(()=>{const r=document.getElementById('event-portal');return{dataset:{...r.dataset},bounds:r.getBoundingClientRect().toJSON(),scrollY,height:innerHeight,reduced:matchMedia('(prefers-reduced-motion:reduce)').matches,css:getComputedStyle(r).height,status:document.getElementById('event-portal-status').textContent}})()")));}
    const reserveHeight=await evaluate("document.getElementById('event-portal').offsetHeight");
    await evaluate("document.getElementById('event-portal-canvas').getContext('webgl2').getExtension('WEBGL_lose_context').loseContext()");
    await waitFor("document.getElementById('event-portal').dataset.mode==='fallback'");
    assert.equal(await evaluate("document.getElementById('event-portal').offsetHeight"),reserveHeight,'Context loss must preserve the active section layout');
  }
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await waitFor("document.getElementById('event-portal').dataset.mode==='static'");
  for(const width of [1440,1024,768,390,320]){
    await viewport(width,960);await evaluate("document.getElementById('event-portal').scrollIntoView({block:'start',behavior:'instant'})");await sleep(150);
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),`Portal overflow at ${width}`);
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.event-portal-stage')).position"),'relative');
    await capture('portal-static-'+width);
  }
  assert.equal(await evaluate("document.querySelector('.event-portal-actions a').getAttribute('href')"),'#/create');
  assert.deepEqual(await evaluate("fetch('/api/events').then(r=>r.json()).then(async rows=>Promise.all(rows.map(e=>fetch('/api/events/'+e.id).then(r=>r.json()))))"),saved);
  if(requireWebGL){
    await viewport(390,900);await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});await reload({evaluate,send,waitFor});
    await waitFor("document.getElementById('event-portal')?.hidden===false");await at(.15);await waitFor("document.getElementById('event-portal').dataset.mode==='webgl'");
    assert(Number(await evaluate("document.getElementById('event-portal').dataset.triangles"))<desktopTriangles);
    assert(await evaluate("(()=>{const c=document.getElementById('event-portal-canvas');return c.width*c.height<510000})()"));
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));await capture('portal-mobile-webgl');
  }
  console.log(`PASS Event Portal ${mode}: real camera/geometry/pointer when WebGL available, keyboard/pause, no idle loop, context fallback, five-width reduced motion and saved-event nonmutation`);
}

export async function checkEventPortalPolicies({evaluate,send,waitFor,viewport}){
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  await viewport(1440,960);await send('Page.enable');
  const injected=await send('Page.addScriptToEvaluateOnNewDocument',{source:"window.__portalWebGLRequests=0;const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){if(type==='webgl2'){window.__portalWebGLRequests++;return null}return original.call(this,type,...args)}"});
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await reload({evaluate,send,waitFor});
  await waitFor("document.getElementById('event-portal')?.dataset.mode==='static'");await evaluate("document.getElementById('event-portal').scrollIntoView({block:'start',behavior:'instant'})");await sleep(200);
  assert.equal(await evaluate('window.__portalWebGLRequests'),0);
  assert.equal(await evaluate("performance.getEntriesByType('resource').some(r=>r.name.includes('event-portal-renderer.js'))"),false);
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});await reload({evaluate,send,waitFor});
  await waitFor("document.getElementById('event-portal')?.hidden===false");await evaluate("document.getElementById('event-portal').scrollIntoView({block:'start',behavior:'instant'})");await waitFor("document.getElementById('event-portal').dataset.mode==='fallback'");
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.event-portal-art img')).opacity"),'1');
  const saveData=await send('Page.addScriptToEvaluateOnNewDocument',{source:"Object.defineProperty(navigator,'connection',{configurable:true,value:{saveData:true,addEventListener(){},removeEventListener(){}}})"});await reload({evaluate,send,waitFor});
  await waitFor("document.getElementById('event-portal')?.dataset.mode==='static'");assert.equal(await evaluate('window.__portalWebGLRequests'),0);
  assert.equal(await evaluate("performance.getEntriesByType('resource').some(r=>r.name.includes('event-portal-renderer.js'))"),false);
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:saveData.identifier});await viewport(900,500);await reload({evaluate,send,waitFor});await waitFor("document.getElementById('event-portal')?.dataset.mode==='static'");assert.equal(await evaluate('window.__portalWebGLRequests'),0);assert.equal(await evaluate("getComputedStyle(document.querySelector('.event-portal-stage')).position"),'relative');await viewport(1440,960);await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.identifier});
  await send('Network.setBlockedURLs',{urls:['*event-portal.css*']});await reload({evaluate,send,waitFor});
  await waitFor("document.getElementById('event-portal')&&document.readyState==='complete'");
  assert(await evaluate("document.getElementById('event-portal').hidden"));
  assert(await evaluate("document.querySelector('.hero-actions [data-new-event]').getClientRects().length>0"));
  await send('Network.setBlockedURLs',{urls:[]});
  console.log('PASS initial WebGL refusal, reduced-motion/Save-Data skip renderer import/context, and real missing-stylesheet safe hiding');
}
