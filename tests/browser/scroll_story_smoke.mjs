import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

export async function checkScrollStory({evaluate,send,waitFor,click,viewport}){
  const folder=path.resolve('.artifacts/scroll-experience/after');mkdirSync(folder,{recursive:true});
  async function capture(name){await pause(650);const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(path.join(folder,`${name}.png`),Buffer.from(shot.data,'base64'));}
  async function position(p){
    await evaluate(`(()=>{const root=document.getElementById('scroll-journey'),r=root.getBoundingClientRect();scrollTo({top:scrollY+r.top+(r.height-innerHeight)*${p},behavior:'instant'})})()`);
    await pause(120);
  }
  await viewport(1440,960);await send('Emulation.setEmulatedMedia',{features:[]});
  await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'});document.getElementById('toast').hidden=true");
  await waitFor("document.getElementById('scroll-journey').dataset.enhanced==='true'");
  const events=await evaluate("fetch('/api/events').then(r=>r.json())");
  const transforms=[];
  for(const [i,p] of [.04,.32,.59,.88].entries()){
    await position(p);await waitFor(`document.getElementById('scroll-journey').dataset.chapter==='${i}'`);
    assert.equal(await evaluate("document.querySelectorAll('.journey-chapter:not([hidden])').length"),1);
    assert.equal(await evaluate("Math.round(document.querySelector('.journey-sticky').getBoundingClientRect().top)"),0);
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));
    transforms.push(await evaluate("getComputedStyle(document.querySelector('.journey-world')).transform"));
    await capture(`chapter-${i+1}-1440`);
  }
  assert.equal(new Set(transforms).size,4,'Real scrolling must scrub different 3D transforms');
  await click('[data-journey-go="1"]');await waitFor("document.getElementById('scroll-journey').dataset.chapter==='1'");
  assert.equal(await evaluate("document.querySelector('[data-journey-go=\"1\"]').getAttribute('aria-current')"),'step');
  await evaluate("document.querySelector('[data-journey-go=\"2\"]').focus()");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  await waitFor("document.getElementById('scroll-journey').dataset.chapter==='2'");
  await click('#journey-motion');assert.equal(await evaluate("document.getElementById('scroll-journey').dataset.paused"),'true');
  const frozen=await evaluate("getComputedStyle(document.querySelector('.journey-world')).transform");
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.editorial-row .feature-visual')).animationName"),'none');
  await position(.67);assert.equal(await evaluate("getComputedStyle(document.querySelector('.journey-world')).transform"),frozen);
  await click('#journey-motion');
  for(const width of [1024,768,390,320]){
    await viewport(width,900);await position(.6);
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),`Scroll scene overflow ${width}`);
    const button=await evaluate("document.getElementById('journey-motion').getBoundingClientRect().toJSON()");
    assert(button.top>=0&&button.bottom<=900,`Pause must stay reachable at ${width}`);
    await capture(`chapter-adapt-${width}`);
  }
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await waitFor("document.getElementById('scroll-journey').dataset.enhanced==='false'");
  assert.equal(await evaluate("document.getElementById('scroll-journey').dataset.enhanced"),'false');
  assert.equal(await evaluate("document.querySelectorAll('.journey-chapter:not([hidden])').length"),4);
  assert.notEqual(await evaluate("getComputedStyle(document.querySelector('.journey-sticky')).position"),'sticky');
  assert(await evaluate("document.getElementById('journey-motion').disabled"));
  await evaluate("document.getElementById('scroll-journey').scrollIntoView({block:'start',behavior:'instant'})");await capture('reduced-motion-320');
  await send('Emulation.setEmulatedMedia',{features:[]});await viewport(1024,600);
  assert.equal(await evaluate("document.getElementById('scroll-journey').dataset.enhanced"),'false');
  assert.equal(await evaluate("document.querySelectorAll('.journey-chapter:not([hidden])').length"),4);
  assert.deepEqual(await evaluate("fetch('/api/events').then(r=>r.json())"),events);
  await viewport(1440,960);await evaluate("scrollTo({top:0,behavior:'instant'})");
  console.log('PASS native sticky scroll chapters, real scrubbed 3D transforms, chapter controls, shared pause, five widths, short-screen/static reduced motion and saved-event nonmutation; screenshots: .artifacts/scroll-experience');
}
