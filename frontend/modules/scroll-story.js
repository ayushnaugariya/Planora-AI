import {$,h,financialMoney,store} from './helpers.js';

// Native scrolling, one scheduled frame per event burst, no perpetual render loop.
export function mountScrollStory(){
  const root=$('scroll-journey');if(!root)return;
  // A stale/missing stylesheet must never expose the raw storyboard as a page.
  if(getComputedStyle(root).getPropertyValue('--scroll-story-ready').trim()!=='1')return;
  root.hidden=false;
  const reduced=matchMedia('(prefers-reduced-motion:reduce)'),short=matchMedia('(max-height:650px)');
  const chapters=[...root.querySelectorAll('.journey-chapter')],
  buttons=[...root.querySelectorAll('[data-journey-go]')];
  const scene=$('journey-scene'),pause=$('journey-motion'),hero=$('cinematic-hero');
  const progress=h('div',{class:'home-read-progress','aria-hidden':'true'},h('span'));
  document.body.append(progress);
  const arrival=document.querySelector('.portal-arrival-stage');
  const heroDepth=h('div',{class:'home-scroll-depth'});
  if(arrival){arrival.before(heroDepth);heroDepth.append(arrival);}
  let frame=0,active=-1,enhanced=false,paused=false;
  const clamp=(v,min=0,max=1)=>Math.max(min,Math.min(max,v));
  function chapter(index){
    if(index===active)return;active=index;root.dataset.chapter=String(index);
    chapters.forEach((article,i)=>{article.hidden=enhanced&&i!==index;});
    buttons.forEach(
      (button,i)=>{
        if(i===index)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');
      }
    );
    $('journey-position').textContent=`0${index+1} / 04`;
  }
  function draw(){
    frame=0;if(document.hidden||document.body.dataset.view!=='landing-view')return;
    const bounds=root.getBoundingClientRect(),height=innerHeight;
    const p=clamp(-bounds.top/Math.max(1,bounds.height-height));
    const heroBounds=hero.getBoundingClientRect(),landing=$('landing-view').getBoundingClientRect();
    progress.firstChild.style.transform=`scaleX(${clamp(-landing.top/Math.max(1,landing.height-height))})`;
    if(!enhanced)return;
    chapter(Math.min(3,Math.floor(p*4)));
    root.style.setProperty('--journey-progress',String(p));
    if(paused)return;
    if(bounds.bottom>0&&bounds.top<height){
      scene.style.setProperty('--journey-turn',`${-24+p*48}deg`);
      scene.style.setProperty('--journey-rise',`${35-p*70}px`);
      scene.style.setProperty('--journey-spread',String(Math.sin(p*Math.PI)));
      scene.style.setProperty('--journey-orbit',`${p*100}deg`);
      scene.style.setProperty('--journey-card-turn',`${12-p*24}deg`);
    }
    const heroP=clamp(-heroBounds.top/Math.max(1,heroBounds.height));
    heroDepth.style.setProperty('--home-scroll-y',`${-heroP*24}px`);
    heroDepth.style.setProperty('--home-scroll-turn',`${heroP*4}deg`);
  }
  function schedule(){if(!frame&&!document.hidden)frame=requestAnimationFrame(draw);}
  function policy(){
    const saveData=navigator.connection?.saveData===true;
    enhanced=!reduced.matches&&!saveData&&!short.matches;
    paused=store.get('planora:scene-paused',false)===true;
    $('landing-view').dataset.scrollPaused=String(paused);
    $('landing-view').dataset.scrollStatic=String(!enhanced);
    root.dataset.enhanced=String(enhanced);root.dataset.paused=String(paused);
    pause.disabled=reduced.matches||saveData;
    pause.textContent=reduced.matches||saveData?'Motion reduced':paused?'Resume motion':'Pause motion';
    pause.setAttribute('aria-pressed',String(paused||reduced.matches||saveData));
    chapters.forEach((article,i)=>{article.hidden=enhanced&&i!==Math.max(0,active);});
    if(!enhanced){scene.removeAttribute('style');heroDepth.removeAttribute('style');}
    schedule();
  }
  buttons.forEach((button,index)=>button.addEventListener('click',()=>{
    if(!enhanced){chapters[index].scrollIntoView({block:'center',behavior:'instant'});chapter(index);return;}
    const rect=root.getBoundingClientRect(),distance=Math.max(1,rect.height-innerHeight);
    scrollTo({top:scrollY+rect.top+distance*((index+.35)/4),behavior:'instant'});schedule();
  }));
  pause.addEventListener('click',()=>{$('scene-motion-toggle').click();});
  $('scene-motion-toggle').addEventListener('click',policy);
  addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule,{passive:true});
  reduced.addEventListener('change',policy);short.addEventListener('change',policy);
  document.addEventListener(
    'visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;}else schedule();}
  );
  document.addEventListener('planora:workspace',schedule);addEventListener('hashchange',schedule);
  document.addEventListener('planora:demo-data',event=>{
    const example=event.detail.workspace;
    $('journey-budget-value').textContent=financialMoney(
      example.budget_summary.total_budget,example.details.currency
    );
    $('journey-guest-value').textContent=`${example.details.guest_count} guests`;
    $('journey-task-value').textContent=`${example.plan.timeline.length} dated milestones`;
  });
  policy();chapter(0);
}
