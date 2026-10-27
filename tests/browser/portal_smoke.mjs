import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

export async function checkPortal({evaluate,send,waitFor,click,viewport}){
  const folder=path.resolve('.artifacts/portal-experience/after');mkdirSync(folder,{recursive:true});
  async function capture(name){await pause(180);const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(path.join(folder,`${name}.png`),Buffer.from(shot.data,'base64'));}
  await viewport(1440);await send('Emulation.setEmulatedMedia',{features:[]});
  await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'});document.getElementById('toast').hidden=true");
  await waitFor("document.getElementById('portal-people')?.textContent==='60 guests'");
  const events=await evaluate("fetch('/api/events').then(r=>r.json())");
  assert.equal(await evaluate("document.getElementById('portal-toggle').getAttribute('aria-expanded')"),'false');
  assert(await evaluate("document.getElementById('portal-facts').inert"));
  await capture('invitation-closed-1440');
  const closed=await evaluate("getComputedStyle(document.querySelector('.scene-invitation')).transform");
  await click('#portal-toggle');
  const frames=path.resolve('.artifacts/portal-experience/opening-frames');mkdirSync(frames,{recursive:true});
  const recording=[],start=Date.now();
  for(let i=0;i<8;i++){
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}),file=`frame-${String(i).padStart(2,'0')}.png`;
    writeFileSync(path.join(frames,file),Buffer.from(shot.data,'base64'));recording.push({file:`opening-frames/${file}`,at:Date.now()-start});await pause(90);
  }
  writeFileSync(path.resolve('.artifacts/portal-experience/opening.json'),JSON.stringify(recording,null,2));
  await pause(1250);
  assert.equal(await evaluate("document.getElementById('portal-toggle').getAttribute('aria-expanded')"),'true');
  assert(!(await evaluate("document.getElementById('portal-facts').inert")));
  assert.notEqual(await evaluate("getComputedStyle(document.querySelector('.scene-invitation')).transform"),closed);
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.portal-date')).visibility"),'visible');
  await capture('invitation-open-1440');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape'});
  assert.equal(await evaluate("document.getElementById('portal-toggle').getAttribute('aria-expanded')"),'false');
  assert.equal(await evaluate('document.activeElement.id'),'portal-toggle');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  assert.equal(await evaluate("document.getElementById('portal-toggle').getAttribute('aria-expanded')"),'true');
  for(const width of [1024,768,390,320]){
    await viewport(width,900);await evaluate("document.getElementById('cinematic-hero').scrollIntoView({block:'center',behavior:'instant'})");await pause(400);
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),`Open portal overflow at ${width}`);
    await capture(`invitation-open-${width}`);
  }
  await viewport(1440);await evaluate("scrollTo({top:0,behavior:'instant'})");
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await click('#portal-toggle');await click('#portal-toggle');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.envelope-flap')).transitionDuration"),'0s');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.portal-arrival-stage')).animationName"),'none');
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.portal-arrival-stage')).opacity"),'1');
  await capture('invitation-reduced-motion');
  assert.deepEqual(await evaluate("fetch('/api/events').then(r=>r.json())"),events);
  await click('#portal-toggle');await send('Emulation.setEmulatedMedia',{features:[]});
  assert.equal(await evaluate("document.getElementById('portal-facts').getAttribute('aria-hidden')"),'true');
  await evaluate("scrollTo({top:0,behavior:'instant'})");
  console.log('PASS reversible 3D invitation, actual fictional facts, keyboard Enter/Escape, five-width open-scene overflow, static reduced motion and event-list nonmutation; portal screenshots saved');
}
