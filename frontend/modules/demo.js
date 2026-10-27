import {$,h,clear,financialMoney} from './helpers.js';
import {countTo} from './motion.js';
import {api} from './api.js';

export function mountDemo(){
  let data=null,mode='budget',selected=null,applied=false,loading=null,lastTotal='0';
  const root=$('demo-content');
  root.classList.add('demo-content');root.setAttribute('role','tabpanel');
  const tabs=document.querySelector('.demo-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Fictional product demonstration');
  for(const id of ['demo-budget-tab','demo-rescue-tab']){$(id).setAttribute('role','tab');$(id).setAttribute('aria-controls','demo-content');}
  const heroLink=h('a',{class:'text-link',href:'#experience',text:'Explore budget & recovery →'});document.querySelector('.hero-note>div').append(heroLink);
  const money=value=>financialMoney(value,'USD');
  const colors=['#7863b4','#aa9171','#80958b','#b99ba5','#8994a5','#c8b18c','#a6b39e','#a898ba','#c8c0ad'];
  function allocationChart(event){
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
    svg.setAttribute('viewBox','0 0 100 100');svg.setAttribute('aria-hidden','true');
    const circle=className=>{const node=document.createElementNS(ns,'circle');for(const [name,value] of Object.entries({cx:'50',cy:'50',r:'40',pathLength:'100',class:className}))node.setAttribute(name,value);return node;};
    svg.append(circle('ring-track'));let offset=0;
    event.plan.budget_lines.forEach((line,i)=>{const segment=circle('ring-segment');segment.setAttribute('stroke',colors[i%colors.length]);segment.setAttribute('stroke-dasharray',`${line.percent} ${100-line.percent}`);segment.setAttribute('stroke-dashoffset',String(-offset));offset+=line.percent;svg.append(segment);});
    return h('div',{class:'allocation-visual'},h('div',{class:'allocation-ring'},svg,h('span',{class:'ring-label',text:'A place for everything'})),h('div',{class:'allocation-caption'},'PLANNED CATEGORY ALLOCATION',h('strong',{text:money(event.budget_summary.planned_allocation)}),'Calculated shares. Fictional example.'));
  }
  function render(){
    clear(root);if(!data)return;
    root.dataset.stage=mode==='budget'?'budget':applied?'resolved':selected?'review':'disruption';
    $('demo-budget-tab').setAttribute('aria-selected',String(mode==='budget'));
    $('demo-rescue-tab').setAttribute('aria-selected',String(mode==='rescue'));
    $('demo-budget-tab').setAttribute('aria-pressed',String(mode==='budget'));$('demo-rescue-tab').setAttribute('aria-pressed',String(mode==='rescue'));
    root.setAttribute('aria-labelledby',mode==='budget'?'demo-budget-tab':'demo-rescue-tab');
    $('demo-budget-tab').tabIndex=mode==='budget'?0:-1;$('demo-rescue-tab').tabIndex=mode==='rescue'?0:-1;
    const event=data.workspace;
    root.append(h('div',{class:'demo-event'},h('span',{class:'eyebrow',text:'FICTIONAL EXAMPLE · 60 GUESTS'}),h('h3',{text:event.details.title})));
    if(mode==='budget'){
      const figure=h('strong',{class:'demo-total'});root.append(h('p',{class:'demo-label',text:'Total planning budget'}),figure);
      countTo(figure,event.budget_summary.total_budget,money,{from:lastTotal});lastTotal=event.budget_summary.total_budget;
      root.append(allocationChart(event));
      for(const [index,line] of event.plan.budget_lines.slice(0,5).entries()){
        const bar=h('span',{class:'demo-bar'});bar.style.width=`${line.percent}%`;bar.style.backgroundColor=colors[index%colors.length];
        const row=h('div',{class:'demo-category'},h('div',{},h('span',{text:line.label}),h('b',{text:money(line.amount)})),h('div',{class:'demo-bar-track'},bar));row.style.setProperty('--category-index',index);root.append(row);
      }
      root.append(h('p',{class:'demo-footnote',text:`${money(event.budget_summary.projected_cost)} in fictional estimates. All values calculated by the planning engine.`}));
    }else{
      root.append(h('p',{class:'demo-incident',text:'The unexpected: entertainment supplier cancels.'}));
      if(applied){
        root.append(h('div',{class:'demo-outcome'},h('span',{class:'badge',text:'SIMULATED APPROVAL'}),h('h3',{text:'A clear next step.'}),h('p',{text:`Projected cost in this example: ${money(selected.scenario.proposed_budget.projected_cost)}.`}),h('p',{text:'Your actual workspace would require a current feasible preview and server-validated approval.'})));
        const reset=h('button',{type:'button',class:'ghost',text:'Replay recovery demo'});reset.addEventListener('click',()=>{selected=null;applied=false;render();});root.append(reset);
      }else if(selected){
        const proposed=h('strong');
        root.append(h('h4',{text:selected.title}),h('div',{class:'demo-compare'},h('div',{},h('small',{text:'BEFORE · PROJECTED'}),h('strong',{text:money(selected.scenario.original_budget.projected_cost)})),h('div',{},h('small',{text:'AFTER · PROJECTED'}),proposed)),h('p',{text:`${selected.scenario.affected_tasks.length} affected task(s). Prices and confirmation are fictional demo assumptions.`}));
        countTo(proposed,selected.scenario.proposed_budget.projected_cost,money,{from:selected.scenario.original_budget.projected_cost});
        root.append(h('p',{class:'demo-tradeoff',text:`Recorded commitments stay ${money(selected.scenario.proposed_budget.committed_spending)}. Cancellation and replacement amounts are fictional supplied assumptions, not negotiated savings.`}));
        const approve=h('input',{type:'checkbox',id:'demo-approval'}),button=h('button',{type:'button',class:'primary',disabled:true,text:'Apply to demo preview →'});
        approve.addEventListener('change',()=>{button.disabled=!approve.checked;});button.addEventListener('click',()=>{applied=true;render();});
        const back=h('button',{type:'button',class:'ghost',text:'Back to options'});back.addEventListener('click',()=>{selected=null;render();});
        const discard=h('button',{type:'button',id:'demo-discard-btn',class:'ghost',text:'Discard demo preview'});discard.addEventListener('click',()=>{selected=null;render();root.prepend(h('p',{class:'demo-discard-notice',role:'status',text:'Demo preview discarded. No saved event was changed.'}));});
        root.append(h('label',{class:'demo-approval',htmlFor:'demo-approval'},approve,'I approve this fictional recovery preview'),h('div',{class:'workspace-actions'},button,back,discard));
      }else{
        for(const option of data.rescue.options){const button=h('button',{type:'button',class:'demo-option'},h('span',{},h('b',{text:option.title}),h('small',{text:`${option.scenario.affected_tasks.length} affected tasks · fictional confirmation`})),h('span',{text:money(option.scenario.proposed_budget.projected_cost)}));button.addEventListener('click',()=>{selected=option;render();});root.append(button);}
        root.append(h('p',{class:'demo-footnote',text:'Choose an option to compare and approve a simulated update. No event is saved or changed.'}));
      }
    }
  }
  $('demo-budget-tab').addEventListener('click',()=>{mode='budget';render();});
  $('demo-rescue-tab').addEventListener('click',()=>{mode='rescue';render();});
  for(const id of ['demo-budget-tab','demo-rescue-tab'])$(id).addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();mode=id==='demo-budget-tab'?'rescue':'budget';render();$(mode==='budget'?'demo-budget-tab':'demo-rescue-tab').focus();}});
  $('landing-rescue-demo').addEventListener('click',()=>{mode='rescue';render();});
  document.addEventListener('planora:demo-mode',event=>{mode=event.detail==='rescue'?'rescue':'budget';if(data)render();else load();});
  document.addEventListener('planora:demo-request',load);
  async function load(){
    if(data||loading)return;
    loading=true;
    try{const response=await api('/api/demo',undefined,'GET');data=await response.json();document.dispatchEvent(new CustomEvent('planora:demo-data',{detail:data}));render();}
    catch{clear(root);root.append(h('p',{class:'muted',text:'The interactive example is unavailable. Your own event can still be created in the studio.'}));const retry=h('button',{type:'button',class:'ghost',text:'Retry example'});retry.addEventListener('click',load);root.append(retry);}
    finally{loading=false;}
  }
  // Defer calculation and rendering until the below-fold preview is approached.
  if('IntersectionObserver'in window){const observer=new IntersectionObserver(entries=>{if(entries.some(item=>item.isIntersecting)){observer.disconnect();load();}},{rootMargin:'350px'});observer.observe(root);}else load();
}
