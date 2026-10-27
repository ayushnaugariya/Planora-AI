import {$,h,fmtDate} from './helpers.js';

// A reversible presentation of the existing fictional example, with no write APIs.
export function mountPortal(){
  const hero=$('cinematic-hero'),camera=$('scene-camera'),viewport=$('scene-viewport');
  if(!hero||!camera||!viewport)return;
  const invitation=camera.querySelector('.depth-invitation');if(!invitation)return;
  const arrival=h('div',{class:'portal-arrival-stage'});camera.before(arrival);arrival.append(camera);
  arrival.addEventListener('animationend',event=>{if(event.target===arrival)arrival.dataset.finished='true';});
  hero.dataset.portal='closed';
  invitation.append(h('div',{class:'portal-envelope'},h('div',{class:'envelope-back'}),h('div',{class:'envelope-front'},h('small',{text:'SOMETHING WONDERFUL AWAITS'})),h('div',{class:'envelope-flap'}),h('span',{class:'envelope-seal',text:'p'})));
  camera.prepend(h('div',{class:'portal-floor-plan','aria-hidden':'true'},h('span'),h('span'),h('span')));
  const people=h('strong',{id:'portal-people',text:'Your people'});
  const date=h('strong',{id:'portal-date',text:'The right moment'});
  const priority=h('strong',{id:'portal-priority',text:'The thoughtful details'});
  const note=(className,label,value,caption)=>h('div',{class:`portal-note ${className}`},h('small',{text:label}),value,h('span',{text:caption}));
  const facts=h('div',{id:'portal-facts',class:'portal-facts','aria-hidden':'true'},
    note('portal-people','THE PEOPLE',people,'Make everyone feel welcome.'),
    note('portal-date','THE OCCASION',date,'A dated plan, built around you.'),
    note('portal-priority','THE PRIORITY',priority,'Preview first. Your choice always.'));
  facts.inert=true;viewport.append(facts);
  const label=h('span',{class:'portal-launch-label',text:'Open the invitation'});
  const button=h('button',{id:'portal-toggle',type:'button',class:'portal-launch','aria-expanded':'false','aria-controls':'portal-facts','aria-describedby':'portal-description'},h('span',{class:'portal-launch-symbol','aria-hidden':'true',text:'↗'}),h('span',{},h('small',{text:'A LITTLE MOMENT OF POSSIBILITY'}),label));
  const description=h('p',{id:'portal-description',class:'sr',role:'status','aria-live':'polite',text:'Open a dimensional fictional event example. No saved event is changed.'});
  viewport.append(button);hero.append(description);
  let open=false;
  function setOpen(next){
    open=next;hero.dataset.portal=open?'open':'closed';button.setAttribute('aria-expanded',String(open));
    label.textContent=open?'Fold the invitation':'Open the invitation';facts.setAttribute('aria-hidden',String(!open));facts.inert=!open;
    description.textContent=open?'The invitation is open. These are fictional planning details; no saved event has changed.':'The invitation is folded. Your saved events are unchanged.';
  }
  button.addEventListener('click',()=>setOpen(!open));
  hero.addEventListener('keydown',event=>{if(event.key==='Escape'&&open){event.stopPropagation();setOpen(false);button.focus({preventScroll:true});}});
  document.addEventListener('planora:demo-data',event=>{
    const example=event.detail.workspace;
    people.textContent=`${example.details.guest_count} guests`;
    date.textContent=fmtDate(example.details.event_date);
    priority.textContent=example.plan.budget_lines.find(line=>line.priority)?.label||'A balanced plan';
  });
}
