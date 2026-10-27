import {$,h,clear,fmtDate} from './helpers.js';
import {state} from './state.js';

export function mountReadiness({api}){
  const names={attention_needed:'Attention needed',incomplete_evidence:'Evidence incomplete',recorded_checks_clear:'Recorded checks clear'};
  const statuses={pass:'Recorded check passes',attention:'Needs attention',unknown:'Incomplete / unknown'};
  const root=h('section',{id:'readiness-dashboard',class:'surface readiness-dashboard','aria-labelledby':'readiness-title',hidden:true});
  const refresh=h('button',{id:'readiness-refresh',type:'button',class:'ghost',text:'Refresh saved evidence'});
  const explain=h('button',{id:'readiness-explain',type:'button',class:'ghost',text:'Prioritize with AI'});
  const status=h('p',{id:'readiness-status',role:'status',class:'muted'});
  const error=h('p',{id:'readiness-error',role:'alert',class:'error',hidden:true});
  const content=h('div',{id:'readiness-content'});
  root.append(h('div',{class:'readiness-heading'},h('div',{},h('p',{class:'eyebrow',text:'EVENT READINESS INTELLIGENCE'}),h('h3',{id:'readiness-title',text:'Know where you stand.'})),h('div',{class:'readiness-controls'},refresh,explain)),status,error,content);
  $('panel-overview').prepend(root);
  let token=0,pending=false,dirty=true,scheduled=false;
  const active=()=>state.workspace&&location.hash.endsWith('/overview');
  function buttons(){refresh.disabled=explain.disabled=pending||state.workspaceBusy||!state.workspace;}
  function invalidate(){token++;pending=false;dirty=true;clear(content);delete root.dataset.revision;buttons();}
  function schedule(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;if(active()&&dirty&&!state.workspaceBusy)load(false);});}
  async function load(useAI){
    if(!state.workspace||state.workspaceBusy)return;
    const id=state.workspace.id,revision=state.workspace.revision,sequence=++token;
    pending=true;dirty=false;root.hidden=false;root.setAttribute('aria-busy','true');clear(content);error.hidden=true;delete root.dataset.revision;
    status.textContent='Reading confirmed saved evidence…';buttons();
    try{
      const data=await(await api(`/api/events/${id}/readiness`,{revision,explain:useAI})).json();
      if(sequence!==token||state.workspace?.id!==id||state.workspace.revision!==revision)return;
      if(data.event_id!==id||data.revision!==revision)throw Error('Saved event changed. Refresh its evidence.');
      root.dataset.revision=String(revision);root.dataset.state=data.state;
      status.textContent=`Saved revision ${revision} · Assessed ${fmtDate(data.evaluated_on)} · ${data.ordering_source==='gemini'?'Gemini ordered validated actions':'Built-in priorities'} · Read-only`;
      const lead=h('div',{class:`readiness-lead readiness-${data.state}`},h('span',{class:'readiness-emblem','aria-hidden':'true',text:'P'}),h('div',{},h('p',{class:'eyebrow',text:'YOUR SAVED PLANNING PICTURE'}),h('h4',{id:'readiness-state',text:names[data.state]}),h('p',{text:data.explanation})),h('div',{class:'readiness-count'},h('strong',{text:`${data.passed} / ${data.total}`}),h('span',{text:'recorded checks pass'}),h('small',{text:'A check count, not a readiness score'})));
      const dimensions=h('div',{id:'readiness-dimensions',class:'readiness-dimensions'});
      for(const dimension of data.dimensions){
        const details=h('details',{class:'readiness-dimension'},h('summary',{},h('span',{class:'eyebrow',text:dimension.state==='clear'?'RECORDED CHECKS CLEAR':dimension.state==='attention'?'ATTENTION NEEDED':'INCOMPLETE EVIDENCE'}),h('strong',{text:dimension.title}),h('span',{text:`${dimension.passed} of ${dimension.total} checks pass · Show evidence`})));
        for(const check of dimension.checks){
          const facts=h('ul');for(const fact of check.evidence)facts.append(h('li',{text:fact}));
          details.append(h('div',{class:`readiness-check readiness-check-${check.status}`},h('h5',{text:check.title}),h('small',{text:statuses[check.status]}),facts,h('a',{class:'text-link',href:`#/event/${id}/${check.destination}`,text:'Open the existing workflow →'})));
        }
        dimensions.append(details);
      }
      const actions=h('ol',{id:'readiness-actions',class:'readiness-actions'});
      for(const action of data.actions){
        const evidence=h('ul');for(const fact of action.evidence)evidence.append(h('li',{text:fact}));
        actions.append(h('li',{'data-readiness-check':action.check_id},h('span',{class:'badge',text:action.priority===0?'KNOWN CONSTRAINT':action.priority===1?'CLOSE AN EVIDENCE GAP':'RECONFIRM SAVED FACTS'}),h('h4',{text:action.title}),evidence,h('p',{class:'muted',text:`Potential impact: ${action.potential_impact}`}),h('a',{class:'text-link',href:`#/event/${id}/${action.destination}`,text:'Take the next step →'})));
      }
      const limits=h('ul');for(const limit of data.limitations)limits.append(h('li',{text:limit}));
      content.append(lead,dimensions,h('div',{class:'section-heading'},h('h4',{text:'Your next three actions'}),h('span',{class:'muted',text:'Known constraints first. No automatic changes.'})),actions,h('details',{class:'readiness-limits'},h('summary',{text:'How this assessment works, and what remains unknown'}),limits));
    }catch(ex){if(sequence===token){status.textContent='Readiness could not be verified. No saved event was changed.';error.textContent=ex.message;error.hidden=false;dirty=true;}}
    finally{if(sequence===token){pending=false;root.removeAttribute('aria-busy');buttons();}}
  }
  refresh.addEventListener('click',()=>load(false));explain.addEventListener('click',()=>load(true));
  document.addEventListener('planora:workspace',()=>{invalidate();root.hidden=!state.workspace;schedule();});
  document.addEventListener('planora:scenarios',()=>{dirty=true;schedule();});
  document.addEventListener('planora:view',event=>{if(event.detail==='overview'){dirty=true;schedule();}});
  document.addEventListener('planora:busy',()=>{buttons();schedule();});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){dirty=true;schedule();}});
  root.hidden=!state.workspace;schedule();
}
