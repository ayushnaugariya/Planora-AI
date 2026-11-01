import {$,h,store,financialMoney,fmtDate} from './helpers.js';

// Enhancement only: the dimensional composition and its copy are static HTML/CSS.
export function mountCinematic(){
  const hero=$('cinematic-hero'),viewport=$('scene-viewport'),camera=$('scene-camera');
  if(!hero||!viewport||!camera)return;
  const reduced=matchMedia('(prefers-reduced-motion:reduce)');
  const fine=matchMedia('(hover:hover) and (pointer:fine)');
  const compact=matchMedia('(max-width:760px)');
  let visible=false,frame=0,data=null,chapter='occasion',loaded=false,rect=null;
  let paused=store.get('planora:scene-paused',false)===true,point={x:0,y:0};
  // Keep every original position/material transform inside its own motion layer.
  for(
    const [selector,name] of [
      ['.scene-invitation','invitation'],
      ['.botanical-main','floral'],
      ['.botanical-echo','echo'],
      ['.scene-glass','glass'],
      ['.petal-one','petal-a'],
      ['.petal-two','petal-b']
    ]
  ){
    const object=camera.querySelector(selector),layer=h('div',{class:`scene-depth depth-${name}`});
    object.before(layer);layer.append(object);
  }
  const toggle=$('scene-motion-toggle')||h(
    'button',
    {
      type:'button',
      id:'scene-motion-toggle',
      class:'scene-motion-toggle',
      'aria-pressed':'false',
      text:'Pause motion'
    }
  );
  if(!toggle.parentNode)document.querySelector('.scene-story-control .scene-fictional').after(toggle);
  function policy(){
    const saveData=navigator.connection?.saveData===true;
    const constrained=compact.matches||!fine.matches||(navigator.hardwareConcurrency||8)<=4;
    hero.dataset.motion=reduced.matches||saveData?'static':paused||!visible||document.hidden?'paused':constrained?'gentle':'active';
    toggle.disabled=reduced.matches||saveData;
    toggle.setAttribute('aria-pressed',String(paused||reduced.matches||saveData));
    toggle.textContent=reduced.matches||saveData?'Motion reduced':paused?'Resume motion':'Pause motion';
    toggle.setAttribute(
      'aria-label',
      reduced.matches||saveData?'Decorative motion reduced by your preferences':paused?'Resume decorative scene motion':'Pause decorative scene motion'
    );
    if(hero.dataset.motion==='paused'||hero.dataset.motion==='static'||!fine.matches)reset();
  }
  toggle.addEventListener('click',()=>{paused=!paused;store.set('planora:scene-paused',paused);policy();});
  const views={
    occasion:[
      '01 / IMAGINE',
      '01 / THE INSPIRATION',
      'Beautifully imagined. Thoughtfully brought together.',
      'One occasion, with a place for every detail. Explore an explicitly fictional example.'
    ],
    timeline:[
      '02 / PLAN',
      '02 / THE PLAN',
      'The right detail. At the right moment.',
      'Your event date becomes dated milestones and persistent planning checklists.'
    ],
    budget:[
      '03 / CONSIDER',
      '03 / THE INTELLIGENCE',
      'Dream generously. Spend thoughtfully.',
      'Estimates, commitments and payments stay distinct. The server calculates the financial picture.'
    ],
    rescue:[
      '04 / RECOVER',
      '04 / THE RESILIENCE',
      'A change of plans. A considered way forward.',
      'Compare supplied alternatives, review the impact, then explicitly approve. Unknown costs stay unknown.'
    ]
  };
  function render(){
    const [counter,label,title,explanation]=views[chapter];
    $('scene-chapter').textContent=counter;$('scene-insight-label').textContent=label;
    $('scene-insight-title').textContent=title;
    let detail=explanation;
    if(data){
      const event=data.workspace;
      $('scene-budget-value').textContent=financialMoney(
        event.budget_summary.total_budget,event.details.currency
      );
      $('scene-event-date').textContent=fmtDate(event.details.event_date).toUpperCase();
      if(chapter==='timeline'){
        const task=event.plan.timeline.find(item=>item.category!=='event');
        detail=task?`Fictional example: ${task.title} · ${fmtDate(task.due)}. Your own timeline is calculated around your date.`:explanation;
      }
      if(chapter==='budget')detail=`Fictional example: ${financialMoney(event.budget_summary.projected_cost,event.details.currency)} in recorded estimates. Prices are illustrative, never live quotes.`;
      if(chapter==='rescue')detail=`Fictional disruption: an entertainment supplier cancels. Compare ${data.rescue.options.length} supplied alternatives in the recovery demo; no saved event changes.`;
    }
    $('scene-insight-detail').textContent=detail;
    hero.classList.toggle('scene-recovery',chapter==='rescue');
    hero.querySelectorAll('[data-scene-view]').forEach(
      button=>button.setAttribute('aria-pressed',String(button.dataset.sceneView===chapter))
    );
  }
  $('scene-insight').setAttribute('aria-live','polite');$('scene-insight').setAttribute('aria-atomic','true');
  for(const button of hero.querySelectorAll('[data-scene-view]'))button.addEventListener('click',()=>{
    chapter=button.dataset.sceneView;render();
    const note=$('scene-insight');
    note.classList.remove('is-updating');
    requestAnimationFrame(()=>note.classList.add('is-updating'));
    document.dispatchEvent(new CustomEvent('planora:demo-mode',{detail:chapter==='rescue'?'rescue':'budget'}));
  });
  document.addEventListener('planora:demo-data',event=>{data=event.detail;render();});
  function reset(){
    cancelAnimationFrame(frame);frame=0;rect=null;
    for(
      const name of [
        '--scene-x','--scene-y','--scene-px','--scene-py','--invitation-tilt-x','--invitation-tilt-y'
      ]
    )camera.style.removeProperty(name);
    viewport.style.removeProperty('--light-x');viewport.style.removeProperty('--light-y');
  }
  viewport.addEventListener('pointermove',event=>{
    if(
      event.pointerType==='touch'||!visible||document.hidden||reduced.matches||paused||!fine.matches||hero.dataset.motion==='static'
    )return;
    rect=rect||viewport.getBoundingClientRect();
    point={
      x:Math.max(-1,Math.min(1,(event.clientX-rect.left)/rect.width*2-1)),
      y:Math.max(-1,Math.min(1,(event.clientY-rect.top)/rect.height*2-1))
    };
    if(frame)return;
    frame=requestAnimationFrame(()=>{
      frame=0;if(!visible||document.hidden||reduced.matches||paused||!fine.matches)return;
      const {x,y}=point;
      camera.style.setProperty('--scene-x',`${5-y*2}deg`);
      camera.style.setProperty('--scene-y',`${-13+x*3}deg`);
      camera.style.setProperty('--scene-px',`${x*4}px`);camera.style.setProperty('--scene-py',`${y*3}px`);
      camera.style.setProperty('--invitation-tilt-x',`${-y*1.8}deg`);
      camera.style.setProperty('--invitation-tilt-y',`${x*2.2}deg`);
      viewport.style.setProperty('--light-x',`${50+x*10}%`);
      viewport.style.setProperty('--light-y',`${45+y*8}%`);
    });
  },{passive:true});
  viewport.addEventListener('pointerleave',reset);
  reduced.addEventListener('change',policy);
  fine.addEventListener('change',policy);
  compact.addEventListener('change',policy);
  addEventListener('resize',()=>{rect=null;},{passive:true});
  addEventListener('scroll',()=>{rect=null;},{passive:true});
  document.addEventListener('visibilitychange',policy);
  if('IntersectionObserver'in window){
    const observer=new IntersectionObserver(entries=>{
      visible=entries.some(entry=>entry.isIntersecting);
      policy();
      if(visible&&!loaded){loaded=true;document.dispatchEvent(new Event('planora:demo-request'));}
    },{threshold:.05});observer.observe(hero);
  }else{visible=true;policy();document.dispatchEvent(new Event('planora:demo-request'));}
  policy();
}
