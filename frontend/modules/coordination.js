import {state} from './state.js';
import {$,h,clear,fmtDate} from './helpers.js';
import {notify} from './shell.js';

export function mountCoordination({api,applyWorkspace,setWorkspaceBusy,saveProgress,go,hasUnsavedDetails}) {
  let vendorId=null;
  const dialog=$('vendor-dialog');
  $('vendor-dialog-close').addEventListener('click',()=>dialog.close());
  $('vendor-list').addEventListener('click',e=>{
    const button=e.target.closest('[data-vendor-id]');
    if(!button||!state.workspace||state.workspaceBusy)return;
    const vendor=state.workspace.vendors.find(item=>item.id===button.dataset.vendorId);if(!vendor)return;
    vendorId=vendor.id;
    $('vendor-edit-name').value=vendor.name;
    $('vendor-edit-contact').value=vendor.contact;
    $('vendor-edit-status').value=vendor.booking_status;
    $('vendor-edit-error').hidden=true;dialog.showModal();
  });
  $('vendor-edit-form').addEventListener('submit',async e=>{
    e.preventDefault();if(state.workspaceBusy||!vendorId)return;
    if(hasUnsavedDetails()){
      notify('Save or cancel your other unsaved edits before updating this vendor.',true);return;
    }
    setWorkspaceBusy(true);$('vendor-edit-save').disabled=true;
    try{
      const response=await api(
        `/api/events/${state.workspace.id}/vendors/${vendorId}`,
        {
          revision:state.workspace.revision,
          name:$('vendor-edit-name').value.trim(),
          contact:$('vendor-edit-contact').value.trim(),
          booking_status:$('vendor-edit-status').value
        },
        'PATCH'
      );
      applyWorkspace(await response.json(),true,true);dialog.close();notify('Vendor details saved.');
    }catch(err){$('vendor-edit-error').textContent=err.message;$('vendor-edit-error').hidden=false;}
    finally{setWorkspaceBusy(false);$('vendor-edit-save').disabled=false;}
  });
  function checklist(){
    if(!state.workspace)return;
    const event=state.workspace,
    query=$('checklist-search').value.toLocaleLowerCase(),
    filter=$('checklist-filter').value;
    const root=$('checklist-items');clear(root);let count=0;
    event.tasks.forEach(task=>{
      const item=event.plan.timeline[task.milestone_index];
      if(
        item.category==='event'||!`${item.title} ${item.note||''}`.toLocaleLowerCase().includes(query)||filter==='open'&&task.completed||filter==='done'&&!task.completed
      )return;
      count++;
      const input=h('input',{type:'checkbox',checked:task.completed,disabled:state.workspaceBusy});
      input.addEventListener('change',()=>saveProgress(input,task.id,true));
      root.append(
        h(
          'li',
          {class:task.completed?'done':''},
          h(
            'label',
            {},
            input,
            h(
              'span',
              {},
              h('strong',{text:item.title}),
              h(
                'small',
                {text:`${fmtDate(item.due)} · ${task.priority==='high'?'High priority':'Planning milestone'}`}
              ),
              h('small',{text:item.note||''})
            )
          )
        )
      );
    });
    $('checklist-count').textContent=`${count} matching task${count===1?'':'s'}`;
    if(!count)root.append(h('li',{class:'muted',text:'No tasks match. Try a different search or status.'}));
  }
  $('checklist-search').addEventListener('input',checklist);
  $('checklist-filter').addEventListener('change',checklist);
  $('guest-plan-form').addEventListener('submit',e=>{
    e.preventDefault();if(!state.workspace)return;
    if(hasUnsavedDetails()){
      notify('Save or cancel your other edits before starting a guest preview.',true);return;
    }
    $('scenario-type').value='guest_count';$('scenario-type').dispatchEvent(new Event('change'));
    $('scenario-guests').value=$('guest-proposed').value;state.scenarioDirty=true;go('scenarios');
    notify('Guest change copied to Scenario Studio. Create a preview to compare before approving.');
  });
  function render(){
    if(!state.workspace)return;
    checklist();const details=state.workspace.details;
    const root=$('guest-summary');clear(root);
    const item=(name,value)=>h('div',{},h('dt',{text:name}),h('dd',{text:value}));
    root.append(
      h(
        'dl',
        {},
        item('Saved headcount',String(details.guest_count)),
        item('Dietary preferences',details.dietary.join(', ')||'None recorded'),
        item('Individual RSVPs','Managed in the private guest list below')
      )
    );
    $('guest-needs').textContent=details.accessibility_requirements||'No accessibility requirements recorded. Add them in event details.';
    if(document.activeElement!==$('guest-proposed'))$('guest-proposed').value=details.guest_count;
  }
  document.addEventListener('planora:workspace',render);render();
  const tools=h('div',{class:'chat-quick','aria-label':'Suggested planning questions'});
  for(
    const text of [
      'What should I book first?','Where could I review costs?','What information is still missing?'
    ]
  ){
    const button=h('button',{type:'button',class:'ghost',text});
    button.addEventListener('click',()=>{$('chat-input').value=text;$('chat-input').focus();});
    tools.append(button);
  }
  const scenario=h('button',{type:'button',class:'ghost',text:'Explore a what-if →'});
  scenario.addEventListener(
    'click',
    ()=>{
      $('scenario-question').value=$('chat-input').value;
      go('scenarios');
      $('scenario-interpret-form').closest('details').open=true;
      $('scenario-question').focus();
    }
  );
  tools.append(scenario);
  $('chat-log').before(tools);
  // Filtering keeps the original, persisted timeline controls and their handlers.
  const searchId='timeline-search',
  search=h('input',{id:searchId,type:'search',placeholder:'Find a milestone'});
  $('timeline-list').before(
    h('div',{class:'field'},h('label',{htmlFor:searchId,text:'Search your timeline'}),search)
  );
  search.addEventListener(
    'input',
    ()=>{
      for(const item of $('timeline-list').children)item.hidden=!item.textContent.toLocaleLowerCase().includes(
        search.value.toLocaleLowerCase()
      );
    }
  );
}
