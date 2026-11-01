import {state} from './state.js';
import {$,h,clear,financialMoney} from './helpers.js';
import {notify} from './shell.js';

export function mountRescue(
  {api,setWorkspaceBusy,hasUnsavedDetails,fillScenarioInputs,renderScenarioPreview,refreshScenarios}
){
  let assessment=null,eventId=null,requestId=null;
  const kind=$('rescue-kind'),form=$('rescue-form');
  const actionStatus=h('p',{id:'rescue-action-status',role:'status','aria-live':'polite'});
  $('rescue-options').before(actionStatus);
  document.addEventListener(
    'planora:status',
    event=>{
      if(event.detail.origin==='scenario'){
        actionStatus.textContent=event.detail.error||event.detail.message;
        actionStatus.className=event.detail.error?'error':'muted';
      }
    }
  );
  function fields(){
    for(const field of form.querySelectorAll('[data-rescue-kind]')){
      field.hidden=!field.dataset.rescueKind.split(' ').includes(kind.value);
      field.disabled=field.hidden;
    }
    if(!state.workspace)return;
    const selected=$('rescue-vendor').value;clear($('rescue-vendor'));
    for(const vendor of state.workspace.vendors){
      const group=state.workspace.plan.vendors[vendor.group_index];
      if(kind.value==='venue_unavailable'&&group.key!=='venue')continue;
      $('rescue-vendor').append(h('option',{value:vendor.id,text:vendor.name||group.label}));
    }
    if([...$('rescue-vendor').options].some(item=>item.value===selected))$('rescue-vendor').value=selected;
  }
  kind.addEventListener('change',fields);
  form.addEventListener('input',()=>{requestId=null;});form.addEventListener('change',()=>{requestId=null;});
  function optionCard(option,index){
    const scenario=option.scenario;
    const changes=scenario.budget_impact;
    const card=h(
      'article',
      {class:'recovery-option'},
      h(
        'span',
        {
          class:'badge',
          text:`OPTION ${index+1} · ${scenario.status.toUpperCase()} · ${scenario.feasibility.toUpperCase()}`
        }
      ),
      h('h4',{text:option.title}),
      h('p',{text:option.approach})
    );
    const metric=(name,value)=>h('div',{},h('dt',{text:name}),h('dd',{text:value}));
    card.append(
      h(
        'dl',
        {},
        metric('Projected cost',financialMoney(scenario.proposed_budget.projected_cost)),
        metric('Cost impact',financialMoney(changes.projected_cost)),
        metric('Affected task deadlines',String(scenario.affected_tasks.length)),
        metric('Proposed event date',scenario.proposed_values.event_date)
      )
    );
    const notes=h('ul');
    for(const note of [...new Set([...scenario.reasons,...scenario.warnings,...option.tradeoffs])].slice(0,4))notes.append(
      h('li',{text:note})
    );
    card.append(notes);
    const button=h('button',{type:'button',class:'primary',text:'Review this option →'});
    button.addEventListener('click',()=>{
      if(hasUnsavedDetails()){
        notify('Save or cancel your unsaved edits before opening a recovery preview.',true);return;
      }
      state.selectedScenario=scenario;state.scenarioDirty=false;fillScenarioInputs(scenario.parameters);
      $('rescue-review-host').append($('scenario-preview'));
      renderScenarioPreview();
      $('scenario-preview').scrollIntoView(
        {block:'start',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'}
      );
    });card.append(button);return card;
  }
  function render(){
    if(!assessment||!state.workspace)return;
    const root=$('rescue-assessment');clear(root);root.className='surface rescue-assessment';
    root.append(
      h('p',{class:'eyebrow',text:'DETERMINISTIC INCIDENT ASSESSMENT'}),
      h('h3',{text:assessment.incident}),
      h(
        'span',
        {class:'badge',text:`${assessment.urgency.toUpperCase()} · ${assessment.options.length} OPTION(S)`}
      ),
      h('p',{class:'muted',text:assessment.urgency_reason})
    );
    if(assessment.revision!==state.workspace.revision)root.append(
      h(
        'p',
        {class:'error',text:'The event has changed. These options are stale; assess again before applying.'}
      )
    );
    const constraints=h('ul');
    for(const text of assessment.constraints)constraints.append(h('li',{text}));
    root.append(h('h4',{text:'Known constraints'}),constraints);
    const affected=h('ul');
    for(const text of assessment.affected.slice(0,8))affected.append(h('li',{text}));
    root.append(h('h4',{text:'What needs attention'}),affected);
    const steps=h('ul');
    for(const text of assessment.next_steps)steps.append(h('li',{text}));
    root.append(h('h4',{text:'Next steps'}),steps);
    clear($('rescue-options'));
    assessment.options.forEach((option,i)=>$('rescue-options').append(optionCard(option,i)));
  }
  form.addEventListener('submit',async e=>{
    e.preventDefault();if(!state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails()){
      notify('Save or cancel unsaved edits before assessing the saved event.',true);return;
    }
    const body={
      revision:state.workspace.revision,
      request_id:requestId||(requestId=crypto.randomUUID()),
      kind:kind.value,
      description:$('rescue-description').value.trim()
    };
    const optional=id=>$(id).value.trim()||null;
    if(kind.value==='budget_reduction')body.target_budget=Number($('rescue-budget').value);
    else if(kind.value==='guest_change'){
      body.guest_count=Number($('rescue-guests').value);
      if(optional('rescue-guests-alt'))body.alternative_guest_count=Number($('rescue-guests-alt').value);
    }
    else if(kind.value==='timeline_risk'){
      body.event_date=$('rescue-date').value;
      if(optional('rescue-date-alt'))body.alternative_event_date=$('rescue-date-alt').value;
    }
    else{
      body.vendor_id=$('rescue-vendor').value;
      body.cancellation_fee=optional('rescue-fee');
      body.quotes=['a','b'].map(
        (key,i)=>(
          {
            label:`Replacement ${String.fromCharCode(65+i)} (your assumption)`,
            amount:optional(`rescue-quote-${key}`),
            confirmed:$(`rescue-confirm-${key}`).checked
          }
        )
      );
    }
    setWorkspaceBusy(true);
    $('rescue-assess').disabled=true;
    $('rescue-error').hidden=true;
    $('rescue-options').classList.add('is-loading');
    try{
      const response=await api(`/api/events/${state.workspace.id}/rescue`,body);
      assessment=await response.json();
      eventId=state.workspace.id;
      render();
      await refreshScenarios();
      notify('Recovery previews saved. Your event is unchanged.');
    }catch(err){$('rescue-error').textContent=err.message;$('rescue-error').hidden=false;}
    finally{
      setWorkspaceBusy(false);
      $('rescue-assess').disabled=false;
      $('rescue-options').classList.remove('is-loading');
      fields();
    }
  });
  document.addEventListener('planora:workspace',()=>{
    if(eventId&&eventId!==state.workspace?.id){
      assessment=null;
      clear($('rescue-options'));
      clear($('rescue-assessment'));
      $('rescue-assessment').append(h('h3',{text:'Describe the disruption to begin.'}));
      requestId=null;
    }
    fields();render();
  });
  document.addEventListener(
    'planora:scenarios',
    event=>{
      if(!assessment)return;
      for(const option of assessment.options){
        const saved=event.detail.find(item=>item.id===option.scenario.id);if(saved)option.scenario=saved;
      }render();
    }
  );
  fields();
}
