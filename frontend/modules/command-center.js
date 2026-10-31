import {state} from './state.js';
import {$,h,clear} from './helpers.js';

export function mountCommandCenter({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails}){
  const root=$('panel-command');
  const field=(label,input)=>h('div',{class:'field'},h('label',{htmlFor:input.id,text:label}),input);
  const label=s=>s.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
  const select=(id,items)=>h('select',{id},items.map(s=>h('option',{value:s,text:label(s)})));
  const input=(id,maxLength=100)=>h('input',{id,maxLength});
  const area=id=>h('textarea',{id,maxLength:800,rows:2});
  const button=(id,text,fn)=>{const b=h('button',{id:id||undefined,type:'button',class:'ghost',text});b.addEventListener('click',fn);return b;};
  const error=h('p',{id:'day-error',class:'error',role:'alert',hidden:true});
  const status=h('p',{id:'day-status',role:'status'}),summary=h('div',{id:'day-stats',class:'day-stats'});
  const heading=h('h3',{id:'day-title',text:'Event Day Command Center'}),phase=h('span',{id:'day-phase',class:'badge'});
  const times=h('p',{id:'day-timezone',class:'muted'});
  const refresh=button('day-refresh','Refresh now',()=>load(true));
  root.append(h('section',{class:'surface day-hero'},h('p',{class:'eyebrow',text:'EVENT OPERATIONS'}),heading,phase,times,summary,status,error,refresh,h('details',{},h('summary',{text:'How readiness and time work'}),h('p',{id:'day-readiness-rule'}),h('ul',{id:'day-assumptions'}))));
  let data=null,context='',token=0,loading=false,visible=false,lastLoad=0;
  const dirty=new Set(),requests=new Map(),revisions=new Map(),forms=[];
  function mark(name){dirty.add(name);requests.delete(name);state.commandDirty=true;}
  function clean(name){dirty.delete(name);requests.delete(name);state.commandDirty=dirty.size>0;}
  function fail(ex){error.textContent=ex.message||String(ex);error.hidden=false;}
  function card(title,...children){return h('section',{class:'surface day-section'},h('h3',{text:title}),...children);}
  function form(name,title,fields,action){
    const approve=h('input',{id:`day-${name}-approval`,type:'checkbox',required:true});
    const save=h('button',{id:`day-${name}-save`,type:'submit',class:'primary',text:'Save approved update'});
    const reset=button(`day-${name}-cancel`,'Clear unsaved form',()=>{if(dirty.has(name)&&!confirm('Discard this unsaved operational update?'))return;el.reset();clean(name);revisions.set(name,data?.revision);resetEditors(name);});
    const el=h('form',{id:`day-${name}-form`,class:'day-editor'},h('h4',{text:title}),...fields,h('label',{class:'day-approval'},approve,'I approve this operational update. No budget or original schedule change.'),h('div',{class:'people-actions'},save,reset));
    el.addEventListener('input',()=>mark(name));el.addEventListener('change',()=>mark(name));
    el.addEventListener('submit',event=>{event.preventDefault();if(!approve.checked)return;saveOperation(name,action);});
    forms.push([name,el]);return el;
  }
  const taskChoice=select('day-task-choice',[]),taskTitle=input('day-task-title',120),taskStatus=select('day-task-status',['upcoming','in_progress','completed','delayed','blocked']);
  const responsible=input('day-task-owner'),taskLocation=input('day-task-location',160),taskVendor=select('day-task-vendor',[]);
  const dateInput=id=>h('input',{id,type:'datetime-local',step:60});
  const plannedStart=dateInput('day-task-planned-start'),plannedEnd=dateInput('day-task-planned-end'),expectedStart=dateInput('day-task-expected');
  const reason=area('day-task-reason'),taskNotes=area('day-task-notes'),dependencies=h('select',{id:'day-task-dependencies',multiple:true,size:4});
  const browserZone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  const taskForm=form('task','Edit a timeline task or add an operation',[
    field('Task',taskChoice),field('Title (custom operations)',taskTitle),
    h('div',{class:'people-grid'},field('Status',taskStatus),field('Responsible person',responsible),field('Assigned vendor',taskVendor),field('Venue area',taskLocation)),
    h('p',{class:'muted',text:`Time editors use your browser timezone (${browserZone}). Saved timestamps include an offset; displayed times use the configured event timezone. Original times lock after their first save.`}),
    h('div',{class:'people-grid'},field('Original planned start',plannedStart),field('Original planned end',plannedEnd),field('Current expected start / deadline',expectedStart)),
    field('Prerequisites (Ctrl / Command to select multiple)',dependencies),field('Delay reason (required when delayed)',reason),field('Operational notes',taskNotes)
  ],()=>({kind:'task',id:taskChoice.value||newKey('task'),value:{title:taskTitle.value,status:taskStatus.value,responsible:responsible.value,
    vendor_id:taskVendor.value||null,location:taskLocation.value,planned_start:fromLocal(plannedStart,data?.tasks.find(t=>t.id===taskChoice.value)?.planned_start),planned_end:fromLocal(plannedEnd,data?.tasks.find(t=>t.id===taskChoice.value)?.planned_end),expected_start:fromLocal(expectedStart,data?.tasks.find(t=>t.id===taskChoice.value)?.expected_start),
    delay_reason:reason.value,notes:taskNotes.value,depends_on:[...dependencies.selectedOptions].map(o=>o.value)}}));
  const taskRows=h('div',{id:'day-tasks',class:'day-list'}),taskFilter=select('day-task-filter',['all','upcoming','in_progress','completed','delayed','blocked']),ownerFilter=input('day-owner-filter');
  const nowNext=h('div',{id:'day-now-next',class:'day-now-next'});
  root.append(card('Live timeline & operations',nowNext,h('div',{class:'people-grid'},field('Filter by status',taskFilter),field('Filter by responsibility',ownerFilter)),taskRows,taskForm));

  const vendorChoice=select('day-vendor-choice',[]),arrival=select('day-vendor-status',['expected','arrived','delayed','not_required']),expectedArrival=dateInput('day-vendor-expected'),vendorNotes=area('day-vendor-notes');
  const vendorForm=form('vendor','Record vendor coordination',[
    field('Vendor',vendorChoice),h('div',{class:'people-grid'},field('Arrival status',arrival),field(`Expected arrival (${browserZone})`,expectedArrival)),field('Arrival notes',vendorNotes)
  ],()=>({kind:'vendor',id:vendorChoice.value,value:{status:arrival.value,expected_at:fromLocal(expectedArrival,data?.vendors.find(v=>v.vendor_id===vendorChoice.value)?.expected_at),notes:vendorNotes.value}}));
  const vendorRows=h('div',{id:'day-vendors',class:'day-list'}),missingOnly=h('input',{id:'day-vendors-outstanding',type:'checkbox'});
  root.append(card('Vendor arrivals',h('p',{class:'muted',text:'Arrival is a manual report. Saved contacts are shown as text; Planora never sends messages or makes calls.'}),h('label',{},missingOnly,'Show vendors not yet arrived'),vendorRows,vendorForm));

  const incidentChoice=select('day-incident-choice',[]),category=select('day-incident-category',['vendor','catering','equipment','weather','venue','guest','timeline','other']),severity=select('day-incident-severity',['low','medium','high','critical']);severity.value='medium';
  const incidentStatus=select('day-incident-status',['open','in_progress','resolved']),description=area('day-incident-description');description.required=true;description.minLength=2;
  const incidentOwner=input('day-incident-owner'),incidentTask=select('day-incident-task',[]),incidentVendor=select('day-incident-vendor',[]),incidentNotes=area('day-incident-notes');
  const incidentForm=form('incident','Report or update an incident',[
    field('Incident',incidentChoice),h('div',{class:'people-grid'},field('Category',category),field('Severity',severity),field('Status',incidentStatus),field('Responsible person',incidentOwner),field('Related task',incidentTask),field('Related vendor',incidentVendor)),field('Description',description),field('Follow-up notes',incidentNotes)
  ],()=>({kind:'incident',id:incidentChoice.value||newKey('incident'),value:{category:category.value,severity:severity.value,status:incidentStatus.value,description:description.value,responsible:incidentOwner.value,task_id:incidentTask.value||null,vendor_id:incidentVendor.value||null,notes:incidentNotes.value}}));
  const incidentRows=h('div',{id:'day-incidents',class:'day-list'});
  root.append(card('Incidents & recovery',incidentRows,incidentForm));
  const activity=h('ol',{id:'day-activity',class:'day-activity'}),allActivity=h('input',{id:'day-all-activity',type:'checkbox'});
  root.append(card('Activity log',h('label',{},allActivity,'Show all recorded activity (latest first)'),activity));
  const zone=input('day-zone',80),zoneForm=form('settings','Event timezone',[field('IANA timezone (leave blank for server-local day)',zone),h('p',{class:'muted',text:'For example Asia/Kolkata or Europe/London. This sets the event phase and displayed times; it does not move the saved plan.'})],()=>({kind:'settings',value:{timezone:zone.value||null}}));
  root.append(card('Time settings',zoneForm));
  const question=area('day-question');question.maxLength=500;question.required=true;question.value='What should I focus on right now?';
  const delayTask=select('day-delay-task',[]),delayMinutes=h('input',{id:'day-delay-minutes',type:'number',min:1,max:1440,value:30,required:true});
  const answer=h('div',{id:'day-copilot-result','aria-live':'polite'}),ask=h('button',{id:'day-ask',type:'submit',class:'primary',text:'Analyze saved operations'});
  const prompts=h('div',{class:'people-actions'});
  for(const text of ['What should I focus on right now?','Which vendors have not arrived?','What are the most urgent unresolved incidents?'])prompts.append(button('',text,()=>{question.value=text;question.focus();}));
  const copilot=h('form',{id:'day-copilot-form'},field('Ask the event-day copilot',question),prompts,h('div',{class:'people-grid'},field('Optional delay hypothesis: task',delayTask),field('Delay in minutes',delayMinutes)),ask);
  copilot.addEventListener('submit',event=>{event.preventDefault();analyze();});
  root.append(card('AI Event-Day Copilot',h('p',{class:'muted',text:'Saved facts, user reports and recommendations are kept separate. Recommendations never execute themselves. Gemini optionally orders grounded suggestions; a built-in fallback is always available.'}),copilot,answer));

  function newKey(name){if(!requests.has(name))requests.set(name,{request:crypto.randomUUID(),entity:crypto.randomUUID()});return requests.get(name).entity;}
  function fromLocal(el,original=null){if(!el.value)return null;if(original&&el.value===local(original))return original;const date=new Date(el.value);if(!Number.isFinite(date.getTime()))throw Error('Enter a valid time.');const round=local(date.toISOString());if(round!==el.value.slice(0,16))throw Error('This local time does not exist because of a timezone transition. Choose a valid time.');return date.toISOString();}
  function local(iso){if(!iso)return '';const d=new Date(iso);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;}
  function time(iso){if(!iso)return 'Not recorded';return new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short',...(data?.timezone&&!data.timezone.startsWith('server-')?{timeZone:data.timezone}:{})}).format(new Date(iso));}
  function options(el,items,empty){const value=el.value,selected=[...el.selectedOptions].map(o=>o.value);clear(el);if(empty!==undefined)el.append(h('option',{value:'',text:empty}));for(const [id,text] of items)el.append(h('option',{value:id,text}));if(el.multiple){for(const o of el.options)o.selected=selected.includes(o.value);}else if([...el.options].some(o=>o.value===value))el.value=value;}
  function choose(name,fn){if(dirty.has(name)&&!confirm('Discard this unsaved operational form?'))return false;clean(name);revisions.set(name,data?.revision);fn();return true;}
  let selectedTask='',selectedVendor='',selectedIncident='';
  function fillTask(){const value=data?.tasks.find(t=>t.id===taskChoice.value);selectedTask=taskChoice.value;for(const [el,key] of [[taskTitle,'title'],[taskStatus,'status'],[responsible,'responsible'],[taskVendor,'vendor_id'],[taskLocation,'location'],[reason,'delay_reason'],[taskNotes,'notes']])el.value=value?.[key]||((key==='status')?'upcoming':'');for(const [el,key] of [[plannedStart,'planned_start'],[plannedEnd,'planned_end'],[expectedStart,'expected_start']])el.value=local(value?.[key]);plannedStart.disabled=plannedEnd.disabled=!!value?.planned_start;taskTitle.readOnly=!!value&&!value.custom;for(const o of dependencies.options)o.selected=(value?.depends_on||[]).includes(o.value);$('day-task-approval').checked=false;}
  function fillVendor(){selectedVendor=vendorChoice.value;const value=data?.vendors.find(v=>v.vendor_id===vendorChoice.value);arrival.value=value?.status||'expected';expectedArrival.value=local(value?.expected_at);vendorNotes.value=value?.notes||'';$('day-vendor-approval').checked=false;}
  function fillIncident(){selectedIncident=incidentChoice.value;const value=data?.incidents.find(i=>i.id===incidentChoice.value);category.value=value?.category||'vendor';severity.value=value?.severity||'medium';incidentStatus.value=value?.status||'open';description.value=value?.description||'';incidentOwner.value=value?.responsible||'';incidentTask.value=value?.task_id||'';incidentVendor.value=value?.vendor_id||'';incidentNotes.value=value?.notes||'';$('day-incident-approval').checked=false;}
  taskChoice.addEventListener('change',()=>{if(!choose('task',fillTask))taskChoice.value=selectedTask;});
  vendorChoice.addEventListener('change',()=>{if(!choose('vendor',fillVendor))vendorChoice.value=selectedVendor;});
  incidentChoice.addEventListener('change',()=>{if(!choose('incident',fillIncident))incidentChoice.value=selectedIncident;});
  function resetEditors(name){if(name==='task'){taskChoice.value='';fillTask();}if(name==='vendor')fillVendor();if(name==='incident'){incidentChoice.value='';fillIncident();}if(name==='settings')zone.value=data?.timezone.startsWith('server-')?'':data?.timezone||'';}
  function render(){
    clear(summary);clear(taskRows);clear(vendorRows);clear(incidentRows);clear(activity);clear(nowNext);
    if(!data)return;
    heading.textContent=`${data.title} · Event Day Command Center`;phase.textContent=label(data.phase);times.textContent=`${data.event_date} · ${data.timezone} · Updated ${time(data.as_of)}`;
    for(const [key,text] of [['readiness','Operational readiness'],['total','Tasks'],['completed','Completed'],['in_progress','In progress'],['delayed','Delayed'],['blocked','Blocked'],['vendors_expected','Required vendors'],['vendors_arrived','Arrived'],['open_incidents','Open incidents'],['critical_incidents','Critical incidents']])summary.append(h('div',{},h('span',{text}),h('strong',{'data-day-stat':key,text:data.stats[key]===null?'Unknown':String(data.stats[key])+(key==='readiness'?'%':'')})));
    $('day-readiness-rule').textContent=data.readiness_rule;clear($('day-assumptions'));for(const text of data.assumptions)$('day-assumptions').append(h('li',{text}));
    const current=data.tasks.filter(t=>t.status==='in_progress'),next=data.tasks.find(t=>t.status==='upcoming');
    nowNext.append(h('div',{},h('strong',{text:'Happening now'}),h('p',{text:current.length?current.map(t=>t.title).join(' · '):'No task reported in progress.'})),h('div',{},h('strong',{text:'Coming next'}),h('p',{text:next?`${next.title} · ${time(next.effective_start)}`:'No upcoming task recorded.'})));
    const found=data.tasks.filter(t=>(taskFilter.value==='all'||t.status===taskFilter.value)&&(!ownerFilter.value||t.responsible.toLocaleLowerCase().includes(ownerFilter.value.toLocaleLowerCase())));
    for(const t of found){const edit=button('',`Update ${t.title}`,()=>{if(choose('task',()=>{taskChoice.value=t.id;fillTask();}))taskForm.scrollIntoView({block:'center'});});edit.dataset.dayTask=t.id;
      taskRows.append(h('article',{class:`day-row day-${t.status}`},h('span',{class:'badge',text:label(t.status)+(t.overdue?' · Past expected time':'')}),h('h4',{text:t.title}),h('p',{class:'muted',text:`${t.custom?'Custom operation':`Original deadline: ${t.original_due}`} · ${t.responsible||'Unassigned'} · ${t.location||'No area recorded'}`}),h('dl',{class:'day-times'},h('dt',{text:'Original start / end'}),h('dd',{text:`${time(t.planned_start)} / ${time(t.planned_end)}`}),h('dt',{text:'Expected start / delay'}),h('dd',{text:`${time(t.expected_start)} / ${t.delay_minutes===null?'Unknown':`${t.delay_minutes} min`}`}),h('dt',{text:'Actual start / completion'}),h('dd',{text:`${time(t.actual_started_at)} / ${time(t.actual_completed_at)}`})),h('p',{text:`Prerequisites: ${t.depends_on.map(id=>data.tasks.find(x=>x.id===id)?.title||'Unavailable').join(', ')||'None recorded'}`}),h('p',{text:`Vendor: ${data.vendors.find(v=>v.vendor_id===t.vendor_id)?.name||'Unassigned'}`}),h('p',{text:[t.delay_reason,t.notes].filter(Boolean).join(' · ')}),edit));}
    if(!found.length)taskRows.append(h('p',{class:'muted',text:'No tasks match. Add an operation or change the filters.'}));
    for(const v of data.vendors.filter(v=>!missingOnly.checked||['expected','delayed'].includes(v.status)))vendorRows.append(h('article',{class:'day-row'},h('span',{class:'badge',text:label(v.status)}),h('h4',{text:v.name}),h('p',{text:`${v.category} · ${v.booking_status} · ${v.contact||'No contact recorded'}`}),h('p',{text:`Expected: ${time(v.expected_at)} · Actual: ${time(v.actual_arrived_at)}`}),h('p',{text:`Responsibilities: ${v.task_ids.map(id=>data.tasks.find(t=>t.id===id)?.title).join(', ')||'No task association recorded'}`}),h('p',{text:v.notes}),button('',`Update ${v.name}`,()=>{if(choose('vendor',()=>{vendorChoice.value=v.vendor_id;fillVendor();}))vendorForm.scrollIntoView({block:'center'});}))); 
    if(!vendorRows.children.length)vendorRows.append(h('p',{class:'muted',text:'No vendors match this view.'}));
    for(const i of data.incidents){const analysis=button('', 'Analyze impact',()=>analyze(i.id));analysis.dataset.dayAnalyze=i.id;const recovery=button('', 'Review in Event Rescue',()=>handoff(i));recovery.dataset.dayRescue=i.id;
      const edit=button('', 'Update incident',()=>{if(choose('incident',()=>{incidentChoice.value=i.id;fillIncident();}))incidentForm.scrollIntoView({block:'center'});});edit.dataset.dayIncident=i.id;
      incidentRows.append(h('article',{class:`day-row day-severity-${i.severity}`},h('span',{class:'badge',text:`${label(i.severity)} · ${label(i.status)}`}),h('h4',{text:i.description}),h('p',{text:`${i.category} · ${i.responsible||'Unassigned'} · Reported ${time(i.created_at)}${i.resolved_at?` · Resolved ${time(i.resolved_at)}`:''}`}),h('p',{text:i.notes}),h('div',{class:'people-actions'},edit,analysis,recovery)));}
    if(!data.incidents.length)incidentRows.append(h('p',{class:'muted',text:'No incidents reported. Add an issue below when something needs attention.'}));
    for(const a of [...data.activity].reverse().slice(0,allActivity.checked?1000:50))activity.append(h('li',{},h('time',{dateTime:a.created_at,text:time(a.created_at)}),' · ',a.description,h('small',{text:a.reference_id?`Reference: ${a.reference_id}`:'Event settings'})));
    if(!data.activity.length)activity.append(h('li',{text:'No operational changes recorded yet.'}));
    options(taskChoice,data.tasks.map(t=>[t.id,t.title]),'Add custom operation');options(dependencies,data.tasks.map(t=>[t.id,t.title]));
    for(const el of [taskVendor,incidentVendor])options(el,data.vendors.map(v=>[v.vendor_id,v.name]),'Not assigned');
    options(vendorChoice,data.vendors.map(v=>[v.vendor_id,v.name]));options(incidentChoice,data.incidents.map(i=>[i.id,i.description.slice(0,80)]),'Report new incident');
    for(const el of [incidentTask,delayTask])options(el,data.tasks.map(t=>[t.id,t.title]),'No specific task');
    for(const [name] of forms)if(!dirty.has(name)){revisions.set(name,data.revision);if(name==='task')fillTask();else if(name==='vendor')fillVendor();else if(name==='incident')fillIncident();else zone.value=data.timezone.startsWith('server-')?'':data.timezone;}
    status.textContent=`Saved revision ${data.revision}. Auto-refresh checks every 30 seconds while this view is open; unsaved inputs are retained.`;
  }
  for(const el of [taskFilter,ownerFilter,missingOnly,allActivity])el.addEventListener('input',render);
  async function load(force=false){
    if(!state.workspace||loading||(!force&&Date.now()-lastLoad<2000))return;
    const id=state.workspace.id,revision=state.workspace.revision,current=++token;loading=true;root.setAttribute('aria-busy','true');status.textContent='Loading saved event-day operations…';
    try{const result=await(await api(`/api/events/${id}/command-center`,undefined,'GET')).json();if(token!==current||state.workspace?.id!==id||state.workspace.revision!==revision)return;data=result;lastLoad=Date.now();error.hidden=true;render();if(result.revision!==revision)status.textContent+=' Another tab changed this event. Reopen the event before saving; stale updates are rejected.';}
    catch(ex){if(token===current){fail(ex);status.textContent='Refresh failed. Displayed information may be stale. Retry before acting.';}}
    finally{if(token===current){loading=false;root.removeAttribute('aria-busy');}}
  }
  async function saveOperation(name,action){
    if(!data||!state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails(false,false,false,true)){fail(Error('Save or cancel other workspace edits first.'));return;}
    const id=state.workspace.id;let body;
    try{const operation=action();newKey(name);body={revision:revisions.get(name),request_id:requests.get(name).request,approved:true,operation};}catch(ex){fail(ex);return;}
    let incidentSaved=null;setWorkspaceBusy(true);error.hidden=true;
    try{const result=await(await api(`/api/events/${id}/command-center/operations`,body)).json();if(state.workspace?.id!==id)throw Error('Event changed. Reopen to verify the saved update.');if(body.operation.kind==='incident'&&body.operation.value.status!=='resolved')incidentSaved=body.operation.id;clean(name);data=result.dashboard;applyWorkspace(result.workspace,true,true);render();$('day-'+name+'-approval').checked=false;clear(answer);}
    catch(ex){fail(ex);status.textContent='Save not confirmed. Your input is retained. Reopen after a revision conflict; do not assume the update was applied.';}
    finally{setWorkspaceBusy(false);lock();}
    if(incidentSaved)await analyze(incidentSaved);
  }
  function showAnswer(result){clear(answer);answer.append(h('p',{class:'eyebrow',text:`${result.source==='gemini'?'GEMINI ORDERING · GROUNDED SERVER ADVICE':'BUILT-IN GROUNDED ADVICE'} · REVISION ${result.revision}`}));
    for(const [title,texts] of [['Confirmed saved context',result.confirmed],['User-provided operational reports',result.operational_updates],['Limits and approval',result.warnings]]){const list=h('ul');for(const text of texts)list.append(h('li',{text}));answer.append(h('h4',{text:title}),list);}
    answer.append(h('h4',{text:'Recommendations — no changes applied'}));for(const r of result.recommendations)answer.append(h('article',{class:'day-row'},h('strong',{text:r.label}),h('p',{text:r.explanation}),h('p',{class:'muted',text:`Affected tasks: ${r.task_ids.map(id=>data.tasks.find(t=>t.id===id)?.title||id).join(', ')||'None specifically linked'}`})));
    if(result.revision!==state.workspace?.revision)answer.prepend(h('p',{class:'error',text:'This advice uses a newer/different revision. Reopen the event and analyze again.'}));
  }
  async function analyze(incidentId=null){
    if(!data||!state.workspace||state.workspaceBusy)return;const id=state.workspace.id,revision=data.revision;setWorkspaceBusy(true);error.hidden=true;ask.textContent='Analyzing…';
    try{const path=`/api/events/${id}/command-center`+(incidentId?`/incidents/${incidentId}/analysis`:'/copilot');const result=await(await api(path,incidentId?undefined:{revision,question:question.value,task_id:delayTask.value||null,delay_minutes:Number(delayMinutes.value)},incidentId?'GET':'POST')).json();if(state.workspace?.id===id){showAnswer(result);answer.scrollIntoView({block:'start'});}}
    catch(ex){fail(ex);}finally{ask.textContent='Analyze saved operations';setWorkspaceBusy(false);lock();}
  }
  function handoff(incident){if(state.workspaceBusy)return;if(hasUnsavedDetails()){fail(Error('Save or cancel unsaved updates before opening Event Rescue.'));return;}
    const vendor=data.vendors.find(v=>v.vendor_id===incident.vendor_id);const kind=vendor?'service_failure':'timeline_risk';$('rescue-kind').value=kind;$('rescue-kind').dispatchEvent(new Event('change',{bubbles:true}));$('rescue-description').value=incident.description.slice(0,500);$('rescue-description').dispatchEvent(new Event('input',{bubbles:true}));if(vendor)$('rescue-vendor').value=vendor.vendor_id;
    // Never infer cancellation, replacement price, fee, availability or an alternative date.
    for(const id of ['rescue-fee','rescue-quote-a','rescue-quote-b','rescue-date','rescue-date-alt'])$(id).value='';for(const id of ['rescue-confirm-a','rescue-confirm-b'])$(id).checked=false;
    location.hash=`#/event/${state.workspace.id}/rescue`;
  }
  function lock(){if(!state.workspaceBusy){const task=data?.tasks.find(t=>t.id===taskChoice.value);plannedStart.disabled=plannedEnd.disabled=!!task?.planned_start;}}
  function resetContext(){const id=state.workspace?.id||'';if(id!==context){context=id;token++;loading=false;data=null;lastLoad=0;dirty.clear();requests.clear();revisions.clear();state.commandDirty=false;for(const [,el] of forms)el.reset();selectedTask=selectedVendor=selectedIncident='';for(const el of [taskChoice,taskVendor,vendorChoice,incidentChoice,incidentTask,incidentVendor,dependencies,delayTask])clear(el);clear(answer);error.hidden=true;root.removeAttribute('aria-busy');render();}}
  document.addEventListener('planora:workspace',()=>{resetContext();clear(answer);if(visible)load(true);});
  document.addEventListener('planora:busy',()=>{resetContext();lock();});
  document.addEventListener('planora:view',e=>{visible=e.detail==='command';if(visible){resetContext();load(true);}});
  addEventListener('hashchange',()=>{if(!location.hash.endsWith('/command'))visible=false;});
  setInterval(()=>{if(visible&&!document.hidden&&!state.workspaceBusy)load(true);},30000);
}
