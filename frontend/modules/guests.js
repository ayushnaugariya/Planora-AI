import {state} from './state.js';
import {$,h,clear} from './helpers.js';

export function mountGuests({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails}){
  const field=(label,input)=>h('div',{class:'field'},h('label',{htmlFor:input.id,text:label}),input);
  const select=(id,values)=>h('select',{id},values.map(([value,text])=>h('option',{value,text})));
  const statuses=['pending','confirmed','declined','maybe'],
  groups=['Family','Friends','Colleagues','VIP','Other'];
  const titleCase=s=>s[0].toUpperCase()+s.slice(1);
  const root=h(
    'section',
    {id:'guest-manager',class:'surface signature-tool people-tool','aria-labelledby':'guest-manager-title'}
  );
  const status=h('p',{id:'guest-manager-status',role:'status'}),
  error=h('p',{id:'guest-manager-error',class:'error',role:'alert',hidden:true});
  const metrics=h('div',{id:'guest-roster-stats',class:'people-stats','aria-live':'polite'});
  const name=h('input',{id:'guest-name',maxLength:100,required:true,autocomplete:'name'}),
  email=h('input',{id:'guest-email',type:'email',maxLength:254,autocomplete:'email'});
  const group=select('guest-group',groups.map(s=>[s,s])),
  rsvp=select('guest-rsvp',statuses.map(s=>[s,titleCase(s)]));
  group.value='Other';
  const plus=h('input',{id:'guest-plus',type:'number',min:0,max:20,step:1,value:0,required:true});
  const dietary=h('textarea',{id:'guest-dietary',rows:2,maxLength:300}),
  access=h('textarea',{id:'guest-accessibility',rows:2,maxLength:300}),
  notes=h('textarea',{id:'guest-notes',rows:2,maxLength:500});
  const save=h('button',{id:'guest-save',type:'submit',class:'primary',text:'Add guest'}),
  cancel=h('button',{id:'guest-cancel',type:'button',class:'ghost',text:'Clear form'});
  const form=h(
    'form',
    {id:'guest-editor'},
    h(
      'div',
      {class:'people-grid'},
      field('Guest name',name),
      field('Email (optional)',email),
      field('Group',group),
      field('RSVP for this party',rsvp),
      field('Accompanying guests (0–20)',plus)
    ),
    field('Dietary preferences for this party',dietary),
    field('Accessibility requirements',access),
    field('Private notes',notes),
    h('div',{class:'people-actions'},save,cancel)
  );
  const search=h('input',{id:'guest-search',type:'search',maxLength:120,placeholder:'Name or email'}),
  filter=select('guest-filter',[['','All responses'],...statuses.map(s=>[s,titleCase(s)])]),
  groupFilter=select('guest-group-filter',[['','All groups'],...groups.map(s=>[s,s])]);
  const rows=h('ul',{id:'guest-roster',class:'people-list'}),
  retry=h('button',{id:'guest-refresh',type:'button',class:'ghost',text:'Refresh guest list'}),
  preview=h(
    'button',
    {id:'guest-preview-headcount',type:'button',class:'ghost',text:'Review confirmed headcount as a What-if'}
  );
  root.append(
    h('p',{class:'eyebrow',text:'PRIVATE GUEST LIST & RSVP'}),
    h('h3',{id:'guest-manager-title',text:'Your people, thoughtfully accounted for.'}),
    h(
      'p',
      {
        class:'muted',
        text:'Responses apply to each named guest and their accompanying guests. Expected attendance counts confirmed people only; pending and maybe remain uncertain. RSVP edits never change your saved planning budget/headcount automatically.'
      }
    ),
    metrics,
    status,
    error,
    retry,
    form,
    h(
      'div',
      {class:'people-grid'},
      field('Search guests',search),
      field('Filter by RSVP',filter),
      field('Filter by group',groupFilter)
    ),
    rows,
    preview
  );
  $('panel-guests').append(root);
  let data=null,context='',token=0,editing=null,requestId=null;
  function reset(){
    form.reset();
    group.value='Other';
    plus.value='0';
    editing=requestId=null;
    state.guestDirty=false;
    save.textContent='Add guest';
  }
  form.addEventListener('input',()=>{state.guestDirty=true;});
  form.addEventListener('change',()=>{state.guestDirty=true;});
  cancel.addEventListener(
    'click',()=>{if(state.guestDirty&&!confirm('Discard unsaved guest details?'))return;reset();}
  );
  function render(){
    clear(metrics);clear(rows);
    if(!data){preview.disabled=true;return;}
    for(
      const [key,label] of [
        ['total_invited','Invited people'],
        ['confirmed','Confirmed'],
        ['pending','Pending people'],
        ['pending_responses','Pending responses'],
        ['declined','Declined'],
        ['maybe','Maybe'],
        ['expected_attendees','Expected attendees']
      ]
    )metrics.append(
      h('div',{},h('span',{text:label}),h('strong',{'data-guest-stat':key,text:String(data.stats[key])}))
    );
    const query=search.value.trim().toLocaleLowerCase();
    const found=data.guests.filter(
      g=>(!query||`${g.name} ${g.email}`.toLocaleLowerCase().includes(query))&&(
        !filter.value||g.rsvp===filter.value
      )&&(!groupFilter.value||g.group===groupFilter.value)
    );
    status.textContent=`${data.stats.records} guest records · ${found.length} shown. Totals include plus-ones. ${data.stats.possible_attendees} people could attend if every non-declined party accepts. Planning headcount: ${state.workspace.details.guest_count}.`;
    for(const guest of found){
      const edit=h(
        'button',
        {type:'button',class:'ghost',text:'Edit','data-guest-edit':guest.id,'aria-label':`Edit ${guest.name}`}
      ),
      remove=h(
        'button',
        {
          type:'button',
          class:'ghost',
          text:'Remove',
          'data-guest-remove':guest.id,
          'aria-label':`Remove ${guest.name}`
        }
      );
      edit.addEventListener(
        'click',
        ()=>{
          if(state.workspaceBusy)return;
          if(state.guestDirty&&!confirm('Discard unsaved guest details?'))return;
          editing=guest.id;
          for(
            const [input,key] of [
              [name,'name'],
              [email,'email'],
              [group,'group'],
              [rsvp,'rsvp'],
              [plus,'plus_ones'],
              [dietary,'dietary'],
              [access,'accessibility'],
              [notes,'notes']
            ]
          )input.value=guest[key];
          state.guestDirty=false;
          save.textContent='Save guest changes';
          name.focus();
        }
      );
      remove.addEventListener(
        'click',
        ()=>{
          if(!confirm(`Remove ${guest.name} and their accompanying guests from this event?`))return;
          mutate(
            async id=>{
              const result=await(
                await api(
                  `/api/events/${id}/guests/${guest.id}`,
                  {revision:state.workspace.revision,confirm_id:guest.id},
                  'DELETE'
                )
              ).json();
              accept(id,result);
              if(editing===guest.id)reset();
            }
          );
        }
      );
      rows.append(
        h(
          'li',
          {'data-guest-id':guest.id},
          h(
            'div',
            {},
            h('strong',{text:guest.name}),
            h('p',{text:[guest.email,guest.group,`${1+guest.plus_ones} invited`].filter(Boolean).join(' · ')}),
            h('span',{class:'badge',text:titleCase(guest.rsvp)}),
            guest.notes.startsWith('Public website response (unverified).')?h(
              'span',{class:'badge',text:'Public RSVP · unverified'}
            ):null,
            h(
              'details',
              {},
              h('summary',{text:'Requirements and notes'}),
              h('p',{text:`Dietary: ${guest.dietary||'None recorded'}`}),
              h('p',{text:`Accessibility: ${guest.accessibility||'None recorded'}`}),
              h('p',{text:guest.notes||'No private notes'})
            )
          ),
          h('div',{class:'people-actions'},edit,remove)
        )
      );
    }
    if(!found.length)rows.append(
      h(
        'li',
        {
          class:'muted',
          text:data.guests.length?'No guests match these filters.':'No guests yet. Add the first person above.'
        }
      )
    );
    preview.disabled=state.workspaceBusy||data.revision!==state.workspace?.revision||data.stats.expected_attendees<2||data.stats.expected_attendees>5000;
  }
  async function load(){
    if(!state.workspace)return;
    const id=state.workspace.id,
    revision=state.workspace.revision,
    current=++token;
    root.setAttribute('aria-busy','true');
    status.textContent='Loading private guest list…';
    try{
      const result=await(await api(`/api/events/${id}/guests`,undefined,'GET')).json();
      if(current!==token||state.workspace?.id!==id||state.workspace.revision!==revision)return;
      data=result;
      error.hidden=true;
      render();
    }
    catch(ex){
      if(current===token){
        error.textContent=ex.message;
        error.hidden=false;
        status.textContent='Guest list could not be refreshed. Retry before relying on totals.';
      }
    }
    finally{if(current===token)root.removeAttribute('aria-busy');}
  }
  function accept(id,result){
    if(state.workspace?.id!==id)throw Error('Event changed. Reopen it to confirm the saved guest data.');
    applyWorkspace(result.workspace,true,true);
    data=result.roster;
    render();
  }
  async function mutate(fn){
    if(!state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails({ignoreGuestDraft:true})){
      error.textContent='Save or cancel other unsaved edits first.';error.hidden=false;return;
    }
    if(!data||data.revision!==state.workspace.revision){
      error.textContent='Guest data is stale or unavailable. Reopen the saved event before editing.';
      error.hidden=false;
      return;
    }
    const id=state.workspace.id;error.hidden=true;setWorkspaceBusy(true);save.textContent='Saving guest…';
    try{await fn(id);}catch(ex){
      error.textContent=ex.message;
      error.hidden=false;
      status.textContent='Save was not confirmed. Inputs were retained; reopen after a conflict.';
    }
    finally{setWorkspaceBusy(false);save.textContent=editing?'Save guest changes':'Add guest';render();}
  }
  form.addEventListener('submit',
  event=>{event.preventDefault();
  if(!requestId)requestId=crypto.randomUUID();
  mutate(async id=>{
    const body={
      revision:state.workspace.revision,
      guest:{
        name:name.value,
        email:email.value,
        group:group.value,
        rsvp:rsvp.value,
        plus_ones:Number(plus.value),
        dietary:dietary.value,
        accessibility:access.value,
        notes:notes.value
      }
    };
    if(!editing)body.request_id=requestId;
    const result=await(
      await api(`/api/events/${id}/guests`+(editing?`/${editing}`:''),body,editing?'PUT':'POST')
    ).json();
    accept(id,result);
    reset();
  });});
  for(const input of [search,filter,groupFilter])input.addEventListener('input',render);
  retry.addEventListener('click',load);
  preview.addEventListener(
    'click',
    ()=>{
      if(preview.disabled)return;
      $('guest-proposed').value=data.stats.expected_attendees;
      $('guest-plan-form').requestSubmit();
    }
  );
  function refreshContext(){
    const id=state.workspace?.id||'';
    if(id!==context){
      context=id;
      token++;
      root.removeAttribute('aria-busy');
      data=null;
      reset();
      search.value=filter.value=groupFilter.value='';
      error.hidden=true;
      render();
    }return id;
  }
  document.addEventListener('planora:workspace',()=>{if(refreshContext()&&!$('panel-guests').hidden)load();});
  document.addEventListener('planora:view',event=>{if(refreshContext()&&event.detail==='guests')load();});
  document.addEventListener(
    'planora:busy',
    ()=>{
      refreshContext();
      if(data)preview.disabled=state.workspaceBusy||data.revision!==state.workspace?.revision||data.stats.expected_attendees<2||data.stats.expected_attendees>5000;
    }
  );
}
