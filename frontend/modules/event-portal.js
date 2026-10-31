// A separate lazy WebGL experience; no event data, API access or changes to the existing floral scene.
import {store} from './helpers.js';

export function mountEventPortal(){
  const root=document.getElementById('event-portal');if(!root)return;
  if(getComputedStyle(root).getPropertyValue('--event-portal-ready').trim()!=='1'){
    addEventListener('load',()=>{if(getComputedStyle(root).getPropertyValue('--event-portal-ready').trim()==='1')mountEventPortal();},{once:true});return;
  }
  if(root.dataset.mounted)return;root.dataset.mounted='true';root.hidden=false;
  const canvas=document.getElementById('event-portal-canvas'),stage=root.querySelector('.event-portal-stage'),pause=document.getElementById('event-portal-pause'),status=document.getElementById('event-portal-status'),caption=document.getElementById('event-portal-caption'),title=document.getElementById('event-portal-title'),description=document.getElementById('event-portal-description');
  const reduced=matchMedia('(prefers-reduced-motion:reduce)'),compact=matchMedia('(max-width:650px)'),fine=matchMedia('(hover:hover) and (pointer:fine)'),short=matchMedia('(max-height:640px)');
  let renderer=null,loading=false,failed=false,near=false,visible=false,frame=0,dead=false,paused=store.get('planora:event-portal-paused',false)===true;
  let target={x:0,y:0},point={x:0,y:0},progress=0,paintCount=0;
  const clamp=n=>Math.max(0,Math.min(1,n));
  const constrained=()=>reduced.matches||short.matches||navigator.connection?.saveData===true;
  function cancel(){if(frame)cancelAnimationFrame(frame);frame=0;}
  function release(){cancel();renderer?.dispose();renderer=null;}
  function sync(){
    pause.disabled=constrained()||failed||!renderer;
    pause.setAttribute('aria-pressed',String(paused||constrained()));
    pause.textContent=constrained()||failed?'Static portal':paused?'Resume portal motion':'Pause portal motion';
    if(constrained()){release();root.dataset.mode='static';status.textContent=short.matches?'Short-screen view: a static portal illustration with normal page scrolling.':reduced.matches?'Reduced motion: a static portal illustration. Planning stays available.':'Data-saving mode: a static portal illustration. Planning stays available.';return;}
    if(failed){root.dataset.mode='fallback';status.textContent='Static portal illustration. Continue to your planning studio below.';return;}
    if(renderer){root.dataset.mode='webgl';status.textContent=paused?'Portal motion paused. Use the planning link or continue scrolling.':'SCROLL TO TRAVEL / MOVE YOUR POINTER TO SHIFT THE LIGHT';request();}
    else{root.dataset.mode='pending';status.textContent='An abstract planning universe. Scroll to explore.';if(near)load();}
  }
  async function load(){
    if(loading||renderer||failed||constrained()||dead)return;loading=true;
    try{
      const {createEventPortalRenderer}=await import('./event-portal-renderer.js');
      if(dead||constrained())return;
      renderer=createEventPortalRenderer(canvas,{compact:compact.matches||!fine.matches||(navigator.hardwareConcurrency||8)<=4});
      root.dataset.mode='webgl';sync();request();
    }catch{root.dataset.reserved=String(visible);failed=true;release();root.dataset.mode='fallback';sync();}
    finally{loading=false;}
  }
  function paint(){
    frame=0;if(dead||!renderer||!visible||document.hidden||constrained())return;
    const bounds=root.getBoundingClientRect(),size=stage.getBoundingClientRect();
    if(size.width<1||size.height<1)return;
    if(!paused){
      progress=clamp(-bounds.top/Math.max(1,bounds.height-innerHeight));
      point={...target};
    }
    try{
      const result=renderer.render(progress,point,size.width,size.height);if(!result)return;
      root.style.setProperty('--portal-progress',String(progress));root.dataset.progress=progress.toFixed(3);root.dataset.cameraZ=result.cameraZ.toFixed(3);root.dataset.triangles=String(result.triangles);root.dataset.paints=String(++paintCount);
      const chapter=progress<.34?0:progress<.73?1:2;
      caption.textContent=['01 / A WORLD OF POSSIBILITIES','02 / BEYOND THE EXPECTED','03 / EVERYTHING, IN ITS PLACE'][chapter];
      if(root.dataset.chapter!==String(chapter)){root.dataset.chapter=String(chapter);title.firstChild.textContent=['A little chaos.','Go beyond.','One occasion.'][chapter];title.querySelector('em').textContent=['Infinite possibility.','See what could be.','In perfect harmony.'][chapter];description.textContent=['Step into a world where every moving part finds its place.','Move through the noise. Discover the shape of what comes next.','Distinct pieces. A shared rhythm. Room for every detail.'][chapter];}
      root.querySelectorAll('[data-event-portal-go]').forEach((button,i)=>button.setAttribute('aria-pressed',String(i===chapter)));
      // One coalesced frame per input: no self-scheduling pointer animation or idle renderer.
    }catch{root.dataset.reserved=String(visible);failed=true;release();sync();}
  }
  function request(){if(!frame&&renderer&&visible&&!document.hidden&&!dead&&!constrained())frame=requestAnimationFrame(paint);}
  const observer=new IntersectionObserver(entries=>{for(const entry of entries){near=entry.isIntersecting;if(near&&!constrained())load();}},{rootMargin:'550px'});
  const visibility=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible){sync();request();}else{target={x:0,y:0};cancel();}},{threshold:0});
  observer.observe(root);visibility.observe(root);
  const resize=new ResizeObserver(()=>{if(!paused)request();});resize.observe(stage);
  function move(event){if(paused||!fine.matches||compact.matches||!visible)return;const r=stage.getBoundingClientRect();target={x:Math.max(-1,Math.min(1,(event.clientX-r.left)/r.width*2-1)),y:Math.max(-1,Math.min(1,(event.clientY-r.top)/r.height*2-1))};request();}
  function leave(){target={x:0,y:0};if(!paused)request();}
  function scroll(){if(!paused)request();}
  function pageVisibility(){if(document.hidden)cancel();else{sync();request();}}
  function lost(event){event.preventDefault();root.dataset.reserved=String(visible);failed=true;release();sync();}
  function policy(){target={x:0,y:0};point={x:0,y:0};sync();}
  function toggle(){paused=!paused;store.set('planora:event-portal-paused',paused);sync();}
  function chapter(event){const button=event.target.closest('[data-event-portal-go]');if(!button||root.dataset.mode!=='webgl')return;const bounds=root.getBoundingClientRect(),to=scrollY+bounds.top+Number(button.dataset.eventPortalGo)*Math.max(1,bounds.height-innerHeight);scrollTo({top:to,behavior:reduced.matches?'instant':'smooth'});}
  addEventListener('scroll',scroll,{passive:true});document.addEventListener('visibilitychange',pageVisibility);stage.addEventListener('pointermove',move,{passive:true});stage.addEventListener('pointerleave',leave,{passive:true});canvas.addEventListener('webglcontextlost',lost);pause.addEventListener('click',toggle);root.addEventListener('click',chapter);reduced.addEventListener('change',policy);compact.addEventListener('change',policy);fine.addEventListener('change',policy);short.addEventListener('change',policy);navigator.connection?.addEventListener('change',policy);
  function cleanup(){if(dead)return;dead=true;release();observer.disconnect();visibility.disconnect();resize.disconnect();removeEventListener('scroll',scroll);document.removeEventListener('visibilitychange',pageVisibility);stage.removeEventListener('pointermove',move);stage.removeEventListener('pointerleave',leave);canvas.removeEventListener('webglcontextlost',lost);pause.removeEventListener('click',toggle);root.removeEventListener('click',chapter);reduced.removeEventListener('change',policy);compact.removeEventListener('change',policy);fine.removeEventListener('change',policy);short.removeEventListener('change',policy);navigator.connection?.removeEventListener('change',policy);}
  addEventListener('pagehide',event=>{if(event.persisted){cancel();return;}cleanup();});addEventListener('pageshow',event=>{if(event.persisted){sync();request();}});
  sync();
}
