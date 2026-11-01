import {$,h,clear,financialMoney,store} from './helpers.js';
import {state} from './state.js';

// Briefs only populate a reviewed draft; the original wizard owns event creation.
export function mountIntelligence(
  {
    api,
    restoreForm,
    wizard,
    applyWorkspace,
    refreshAfterSave,
    setWorkspaceBusy,
    hasUnsavedDetails,
    workspaceStatus,
    go
  }
){
  const description=h(
    'textarea',
    {
      id:'brief-description',
      maxLength:1200,
      rows:4,
      required:true,
      minLength:2,
      placeholder:'A wedding in Mumbai on 2027-06-12 for 120 guests with a budget of INR 800000. Theme: candlelit garden'
    }
  );
  const submit=h('button',{id:'brief-extract',type:'submit',class:'primary',text:'Shape my event brief'});
  const error=h('p',{id:'brief-error',class:'error',role:'alert',hidden:true});
  const result=h(
    'section',{id:'brief-result',class:'brief-result',hidden:true,'aria-label':'Unsaved event brief'}
  );
  const use=h(
    'button',{id:'brief-use',type:'button',class:'ghost',text:'Use reviewed brief in the wizard',hidden:true}
  );
  const form=h(
    'form',
    {id:'brief-form'},
    h('label',{htmlFor:description.id,text:'Describe the occasion in your own words'}),
    description,
    h(
      'p',
      {
        class:'muted',
        text:'Use a currency code and an exact YYYY-MM-DD date. Missing details become questions. Nothing is saved here.'
      }
    ),
    submit,
    error
  );
  const panel=h(
    'section',
    {class:'surface brief-intake',id:'brief-intake'},
    h('p',{class:'eyebrow',text:'IMAGINE → REVIEW → PLAN'}),
    h('h2',{text:'Start with a little imagination.'}),
    form,
    result,
    use
  );
  document.querySelector('.wizard-progress-row').before(panel);
  let draft=null,generation=0,busy=false;
  function reset(){generation++;draft=null;result.hidden=true;use.hidden=true;panel.hidden=!!state.workspace;}
  description.addEventListener('input',()=>{generation++;draft=null;use.hidden=true;result.hidden=true;});
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(busy||state.workspace)return;
    const token=++generation;
    busy=true;
    submit.disabled=true;
    submit.textContent='Reading your brief…';
    error.hidden=true;
    use.hidden=true;
    try{
      const response=await api('/api/intake',{description:description.value.trim()});
      const data=await response.json();
      if(token!==generation||state.workspace)return;
      draft=data;clear(result);result.hidden=false;
      result.append(
        h(
          'span',
          {
            class:'badge',
            text:`${data.source==='gemini'?'GEMINI EXTRACTION':'BUILT-IN EXTRACTION'} · UNSAVED PROPOSAL`
          }
        ),
        h(
          'h3',{text:data.missing.length?'A few details will make this yours.':'Your occasion, taking shape.'}
        )
      );
      const facts=h('dl',{class:'review-grid'});
      for(const [key,value] of Object.entries(data.fields))if(
        value!==null&&(!Array.isArray(value)||value.length)
      )facts.append(
        h(
          'div',
          {},
          h('dt',{text:key.replaceAll('_',' ')}),
          h('dd',{text:Array.isArray(value)?value.join(', '):String(value)})
        )
      );
      result.append(facts);
      if(data.questions.length){
        const questions=h('ul');
        for(const text of data.questions)questions.append(h('li',{text}));
        result.append(h('h4',{text:'Before planning'}),questions);
      }
      if(data.preview){
        result.append(h('p',{text:data.explanation}));
        const allocation=h('div',{class:'brief-allocations'});
        for(const line of data.preview.budget_lines)allocation.append(
          h(
            'div',
            {},
            h('span',{text:line.label}),
            h('strong',{text:financialMoney(line.amount,data.preview.currency)})
          )
        );
        result.append(
          h('h4',{text:'Calculated planning allowances · not quotes'}),
          allocation,
          h(
            'p',
            {
              class:'muted',
              text:`${data.preview.timeline.length} dated milestones · ${data.preview.vendors.length} vendor groups. Complete the wizard to save and manage them.`
            }
          )
        );
      }
      const assumptions=h('ul',{class:'muted'});
      for(const text of data.assumptions)assumptions.append(h('li',{text}));
      result.append(assumptions);
      use.hidden=!!data.missing.length;
    }catch(ex){if(token===generation){error.textContent=ex.message;error.hidden=false;}}
    finally{busy=false;submit.disabled=false;submit.textContent='Shape my event brief';}
  });
  use.addEventListener('click',()=>{
    if(!draft||draft.missing.length||state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails()&&!confirm('Replace the unsaved form fields with this reviewed brief?'))return;
    restoreForm(Object.fromEntries(Object.entries(draft.fields).filter(([,value])=>value!==null)));
    $('plan-form').dispatchEvent(new Event('input',{bubbles:true}));wizard.review();
    $('wizard-review').scrollIntoView({block:'center',behavior:'instant'});
    $('wizard-review').closest('section').querySelector('h2').focus();
  });
  $('new-event-btn').addEventListener('click',reset);
  document.addEventListener('planora:workspace',reset);
  reset();

  const demoButton=h(
    'button',{id:'demo-create-workspace',type:'button',class:'primary',text:'Try the full saved demo'}
  );
  const demoError=h('p',{id:'demo-workspace-error',class:'error',role:'alert',hidden:true});
  const demoPanel=h(
    'section',
    {class:'demo-workspace-launch surface'},
    h(
      'div',
      {},
      h('p',{class:'eyebrow',text:'FROM DEMONSTRATION TO A REAL SAVED WORKFLOW'}),
      h('h3',{text:'Try a change of plans. Keep the proof.'}),
      h(
        'p',
        {
          text:'Create a separate fictional workspace with sample costs and a deposit. Compare recovery options, approve one, then reload to verify it. Your other events stay intact.'
        }
      )
    ),
    demoButton,
    demoError
  );
  $('experience').append(demoPanel);
  demoButton.addEventListener('click',async()=>{
    if(state.workspaceBusy||state.booting)return;
    if(hasUnsavedDetails()&&!confirm('Leave unsaved edits and open a separate fictional demonstration?'))return;
    if(
      !confirm(
        'Create a new saved fictional workspace? All prices, deposits and supplier confirmations are illustrative.'
      )
    )return;
    const requestId=store.get('planora:demo-create-retry',null)||crypto.randomUUID();
    store.set('planora:demo-create-retry',requestId);
    setWorkspaceBusy(true);
    demoButton.disabled=true;
    demoButton.textContent='Saving the fictional workspace…';
    demoError.hidden=true;
    try{
      const response=await api('/api/demo/workspace',{request_id:requestId,acknowledge_fictional:true});
      applyWorkspace(await response.json());
      store.set('planora:demo-create-retry',null);
      await refreshAfterSave();
      workspaceStatus(
        'Fictional workspace saved. Assess the supplied disruption, review an option, then explicitly approve.'
      );
      go('rescue');
      const fields={
        'rescue-kind':'vendor_cancellation',
        'rescue-description':'Fictional demonstration: the entertainment supplier cancels. Prices and confirmations below are illustrative.',
        'rescue-fee':'100',
        'rescue-quote-a':'950',
        'rescue-quote-b':'1250'
      };
      for(const [id,value] of Object.entries(fields)){
        $(id).value=value;$(id).dispatchEvent(new Event('change',{bubbles:true}));
      }
      const vendor=state.workspace.vendors.find(
        item=>state.workspace.plan.vendors[item.group_index].key==='entertainment'
      );
      $('rescue-vendor').value=vendor.id;
      $('rescue-confirm-a').checked=$('rescue-confirm-b').checked=true;
    }catch(ex){demoError.textContent=ex.message;demoError.hidden=false;}
    finally{
      setWorkspaceBusy(false);demoButton.disabled=false;demoButton.textContent='Try the full saved demo';
    }
  });
}
