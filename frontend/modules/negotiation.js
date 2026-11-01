import {state} from './state.js';
import {$,h,clear,financialMoney} from './helpers.js';

export function mountNegotiation({api,setWorkspaceBusy,hasUnsavedDetails}){
  const field=(label,input)=>h('div',{class:'field'},h('label',{htmlFor:input.id,text:label}),input);
  const root=h(
    'section',
    {
      id:'negotiation-assistant',
      class:'surface signature-tool people-tool',
      'aria-labelledby':'negotiation-title'
    }
  );
  const vendor=h('select',{id:'negotiation-vendor',required:true}),
  quote=h('select',{id:'negotiation-quote'}),
  compare=h('select',{id:'negotiation-comparisons',multiple:true,size:3});
  const scenario=h(
    'select',
    {id:'negotiation-scenario'},
    [
      ['lower_price','Request a lower price'],
      ['additional_services','Additional services within the quoted total'],
      ['package_discount','Package discount'],
      ['payment_terms','Payment terms'],
      ['hidden_charges','Clarify hidden charges'],
      ['compare_offers','Compare supplied offers'],
      ['custom_package','Customized package']
    ].map(([value,text])=>h('option',{value,text}))
  );
  const target=h(
    'input',
    {
      id:'negotiation-target',
      type:'text',
      inputMode:'decimal',
      maxLength:24,
      placeholder:'Optional explicit target in event currency'
    }
  ),
  instruction=h('textarea',{id:'negotiation-instruction',rows:3,maxLength:400});
  const generate=h(
    'button',{id:'negotiation-generate',type:'submit',class:'primary',text:'Generate negotiation draft'}
  ),
  regenerate=h('button',{id:'negotiation-regenerate',type:'button',class:'ghost',text:'Regenerate'}),
  clearButton=h('button',{id:'negotiation-clear',type:'button',class:'ghost',text:'Clear unsaved draft'});
  const editor=h(
    'textarea',
    {
      id:'negotiation-message',
      class:'negotiation-draft',
      rows:12,
      maxLength:8000,
      placeholder:'Your editable draft appears here. Nothing is sent.'
    }
  );
  const copy=h('button',{id:'negotiation-copy',type:'button',class:'ghost',text:'Copy message'}),
  save=h('button',{id:'negotiation-save',type:'button',class:'primary',text:'Save reviewed draft only'}),
  load=h('button',{id:'negotiation-load',type:'button',class:'ghost',text:'Reopen saved draft'});
  const sourceLabel=h('p',{id:'negotiation-source-context',class:'muted'});
  const facts=h('div',{id:'negotiation-facts',class:'negotiation-facts'}),
  result=h('div',{id:'negotiation-result'}),
  status=h('p',{id:'negotiation-status',role:'status'}),
  error=h('p',{id:'negotiation-error',role:'alert',class:'error',hidden:true});
  const form=h(
    'form',
    {id:'negotiation-form'},
    h(
      'div',
      {class:'people-grid'},
      field('Saved vendor',vendor),
      field('Primary recorded quotation',quote),
      field('Negotiation scenario',scenario),
      field('Target price (a request, not an agreed price)',target)
    ),
    field('Other recorded quotes to compare (optional, up to three)',compare),
    field('Optional custom request (included as user-supplied text)',instruction),
    h('div',{class:'people-actions'},generate,regenerate,clearButton)
  );
  root.append(
    h('p',{class:'eyebrow',text:'PRIVATE VENDOR NEGOTIATION'}),
    h('h3',{id:'negotiation-title',text:'A considered request. A clearer agreement.'}),
    h(
      'p',
      {
        class:'muted',
        text:'Uses saved vendor/event facts and quoted prices. Gemini can select validated tactics and tone; draft wording and all prices remain grounded in server facts. Missing AI uses the built-in planner. Drafts never send communications or change your ledger. Review every statement before copying.'
      }
    ),
    facts,
    form,
    sourceLabel,
    status,
    error,
    result,
    field('Editable message — review before use',editor),
    h('div',{class:'people-actions'},copy,save,load)
  );
  $('panel-vendors').append(root);
  let context='',
  revision=0,
  selectedVendor='',
  stored=null,
  draftRevision=0,
  generation=0,
  ready=false,
  payload=null,
  sources=null,
  variant=0,
  baseKnown=false;
  const endpoint=()=>`/api/events/${state.workspace.id}/vendors/${vendor.value}/negotiation`;
  function sync(){
    const busy=state.workspaceBusy;
    save.disabled=busy||!ready||editor.value.trim().length<2;
    copy.disabled=busy||!editor.value.trim();
    load.disabled=busy||!stored;
    regenerate.disabled=busy||!vendor.value;
  }
  function reset(){
    editor.value='';
    target.value='';
    instruction.value='';
    state.negotiationDirty=false;
    ready=false;
    payload=null;
    sources=null;
    sourceLabel.textContent='';
    clear(result);
    error.hidden=true;
    sync();
  }
  function choices(){
    clear(quote);clear(compare);clear(facts);if(!state.workspace)return;
    const event=state.workspace,
    v=event.vendors.find(item=>item.id===vendor.value);
    if(!v)return;
    const category=event.plan.vendors[v.group_index];
    facts.append(
      h(
        'p',
        {
          text:`${v.name||'Vendor name missing — add it using Edit vendor details'} · ${category.label} · ${event.details.event_date}${event.details.city?' · '+event.details.city:''}`
        }
      ),
      h(
        'p',
        {
          text:`Event budget: ${financialMoney(event.details.budget)}. Category allowance: ${financialMoney(category.budget)}. An allowance is not a vendor quote.`
        }
      )
    );
    quote.append(h('option',{value:'',text:'Choose a quote or reuse a source from Quote Analyzer'}));
    for(
      const e of event.expenses.filter(e=>!e.cancelled&&e.category_key===category.key&&e.quoted_amount!==null)
    ){
      if(e.vendor_id===null||e.vendor_id===v.id)quote.append(
        h(
          'option',
          {
            value:'expense:'+e.id,
            text:`${e.description} · ${financialMoney(e.quoted_amount)}${e.vendor_id?'':' · unlinked category quote'}`
          }
        )
      );
      compare.append(h('option',{value:e.id,text:`${e.description} · ${financialMoney(e.quoted_amount)}`}));
    }
    for(const q of v.quotes)quote.append(
      h('option',{value:'vendor:'+q.id,text:`Saved vendor offer · ${financialMoney(q.amount)}`})
    );
    if(quote.options.length===2)quote.selectedIndex=1;
  }
  async function metadata(){
    if(!state.workspace||!vendor.value)return;
    const id=state.workspace.id,
    key=vendor.value,
    current=++generation;
    stored=null;sync();
    try{
      const data=await(await api(endpoint()+'/draft',undefined,'GET')).json();
      if(current!==generation||state.workspace?.id!==id||vendor.value!==key)return;
      stored=data;
      if(!baseKnown){draftRevision=data?.draft_revision||0;baseKnown=true;}status.textContent=data?`Saved user-reviewed draft available (version ${data.draft_revision}). ${data.draft_revision!==draftRevision?'Another edit was saved; reopen before overwriting. ':''}${data.stale?'Event changed since it was saved; regenerate/review against current facts.':''}`:'No saved draft for this vendor. Nothing will be sent.';
      sync();
    }
    catch(ex){if(current===generation){error.textContent=ex.message;error.hidden=false;}}
  }
  function refresh(){
    const id=state.workspace?.id||'',rev=state.workspace?.revision||0;
    if(id!==context){context=id;
    revision=rev;
    generation++;
    reset();
    clear(vendor);
    stored=null;
    draftRevision=0;
    baseKnown=false;
    if(!id){clear(facts);return;}
      for(const v of state.workspace.vendors)vendor.append(
        h('option',{value:v.id,text:v.name||state.workspace.plan.vendors[v.group_index].label})
      );
      selectedVendor=vendor.value;
      choices();
      if(!$('panel-vendors').hidden)metadata();
    }else if(rev!==revision){
      revision=rev;
      ready=false;
      sources=null;
      sourceLabel.textContent='';
      const keep=vendor.value;
      clear(vendor);
      for(const v of state.workspace.vendors)vendor.append(
        h('option',{value:v.id,text:v.name||state.workspace.plan.vendors[v.group_index].label})
      );
      vendor.value=keep;
      choices();
      if(editor.value)status.textContent='Saved event facts changed. Draft text was kept; regenerate or review it before use.';
      sync();
      if(!$('panel-vendors').hidden)metadata();
    }
  }
  vendor.addEventListener(
    'change',
    ()=>{
      if(state.negotiationDirty&&!confirm('Discard the unsaved negotiation draft before changing vendor?')){
        vendor.value=selectedVendor;return;
      }selectedVendor=vendor.value;
      reset();
      baseKnown=false;
      draftRevision=0;
      choices();
      metadata();
    }
  );
  for(const control of [quote,scenario,target,instruction,compare])control.addEventListener(
    'input',
    ()=>{
      state.negotiationDirty=true;
      ready=false;
      if(control===quote){sources=null;sourceLabel.textContent='';}sync();
    }
  );
  editor.addEventListener('input',()=>{state.negotiationDirty=true;sync();});
  clearButton.addEventListener(
    'click',
    ()=>{
      if(state.negotiationDirty&&!confirm('Discard unsaved negotiation text and source context?'))return;
      reset();
      status.textContent='Unsaved draft cleared. The saved draft and ledger are unchanged.';
    }
  );
  async function action(fn){
    if(!state.workspace||!vendor.value||state.workspaceBusy)return;
    if(hasUnsavedDetails({ignoreNegotiationDraft:true})){
      error.textContent='Save or cancel other unsaved edits first.';error.hidden=false;return;
    }
    const id=state.workspace.id,
    v=vendor.value;
    error.hidden=true;
    status.textContent='Working from saved facts...';
    setWorkspaceBusy(true);
    root.setAttribute('aria-busy','true');
    try{await fn(id,v);}catch(ex){
      error.textContent=ex.message;
      error.hidden=false;
      status.textContent='Action was not confirmed. Your inputs and draft were kept.';
    }
    finally{setWorkspaceBusy(false);root.removeAttribute('aria-busy');sync();}
  }
  async function generateDraft(){
    if(
      editor.value&&state.negotiationDirty&&!confirm(
        'Replace the unsaved message with a newly generated draft?'
      )
    )return;
    await action(async(id,v)=>{
      const [kind,key]=quote.value.split(':');
      const body={
        revision:state.workspace.revision,
        scenario:scenario.value,
        target_price:target.value.trim()||null,
        instruction:instruction.value,
        variant:variant%3,
        expense_id:kind==='expense'?key:null,
        vendor_quote_id:kind==='vendor'?key:null,
        comparison_expense_ids:[...compare.selectedOptions].map(o=>o.value).filter(value=>value!==key),
        ...(sources||{})
      };
      const response=await(await api(endpoint(),body)).json();
      if(state.workspace?.id!==id||vendor.value!==v||state.workspace.revision!==body.revision)throw Error(
        'Event changed. Regenerate for the current saved revision.'
      );
      clear(result);const f=response.facts;
      result.append(
        h(
          'span',
          {
            class:'badge',
            text:response.source==='gemini'?'GEMINI STRATEGY · GROUNDED SERVER DRAFT':'BUILT-IN STRATEGY · GROUNDED SERVER DRAFT'
          }
        ),
        h('p',{text:response.approach})
      );
      for(
        const [label,value] of [
          ['Selected quote',f.quote],
          ['Requested target',f.target],
          ['Requested potential reduction (unagreed)',f.requested_reduction],
          ['Suggested counteroffer (your target, not accepted)',f.counteroffer]
        ]
      )result.append(h('p',{text:`${label}: ${financialMoney(value,f.currency)}`}));
      result.append(h('p',{text:'Quote evidence: '+f.quote_source}));
      for(
        const [label,items] of [
          ['Missing information',response.missing],
          ['Suggested approach',response.suggestions],
          ['Quoted scope',f.scope],
          ['Supplied comparison evidence',f.comparisons],
          ['Protect these terms',f.protected],
          ['Assumptions and warnings',response.warnings]
        ]
      )if(items.length)result.append(
        h(
          'details',
          {open:label==='Missing information'},
          h('summary',{text:label}),
          h('ul',{},items.map(text=>h('li',{text})))
        )
      );
      if(response.message){
        editor.value=response.message;
        payload=body;
        ready=true;
        state.negotiationDirty=true;
        status.textContent='Draft generated for review. Nothing was sent or changed in your budget.';
        variant++;
      }
      else{
        ready=false;
        status.textContent='Complete the missing information above. Existing draft text has been kept.';
      }
    });
  }
  form.addEventListener('submit',event=>{event.preventDefault();generateDraft();});
  regenerate.addEventListener('click',generateDraft);
  copy.addEventListener(
    'click',
    async()=>{
      try{
        await navigator.clipboard.writeText(editor.value);
        status.textContent='Message copied. Planora did not send it.';
      }catch{
        editor.focus();
        editor.select();
        status.textContent='Clipboard unavailable. Text selected for manual copy; nothing was sent.';
      }
    }
  );
  save.addEventListener('click',()=>action(async(id,v)=>{
    if(!ready||!payload||editor.value.trim().length<2)return;
    const saved=await(
      await api(
        endpoint()+'/draft',
        {
          revision:state.workspace.revision,
          draft_revision:draftRevision,
          approved:true,
          scenario:payload.scenario,
          message:editor.value,
          target_price:payload.target_price,
          instruction:payload.instruction,
          expense_id:payload.expense_id,
          vendor_quote_id:payload.vendor_quote_id
        },
        'PUT'
      )
    ).json();
    if(state.workspace?.id!==id||vendor.value!==v)return;
    stored=saved;
    draftRevision=saved.draft_revision;
    state.negotiationDirty=false;
    status.textContent=`Reviewed text saved privately (version ${draftRevision}). No communication was sent and no expense was changed.`;
  }));
  load.addEventListener('click',
  ()=>{if(!stored)return;
  if(state.negotiationDirty&&!confirm('Replace unsaved text with the saved draft?'))return;
    draftRevision=stored.draft_revision;
    baseKnown=true;
    editor.value=stored.message;
    scenario.value=stored.scenario;
    target.value=stored.target_price??'';
    instruction.value=stored.instruction;
    const key=stored.expense_id?'expense:'+stored.expense_id:stored.vendor_quote_id?'vendor:'+stored.vendor_quote_id:'';
    quote.value=[...quote.options].some(o=>o.value===key)?key:'';
    sources=null;
    payload={
      scenario:stored.scenario,
      target_price:stored.target_price,
      instruction:stored.instruction,
      expense_id:stored.expense_id,
      vendor_quote_id:stored.vendor_quote_id
    };
    ready=true;
    state.negotiationDirty=false;
    clear(result);
    status.textContent=`Saved user-reviewed text reopened. ${stored.stale?'Event facts changed; review or regenerate. ':''}Unrecorded analyzer sources must be reattached to regenerate. This text is not proof of agreed terms.`;
    sync();
  });
  document.addEventListener('planora:workspace',refresh);
  document.addEventListener(
    'planora:view',event=>{refresh();if(event.detail==='vendors'&&state.workspace)metadata();}
  );
  document.addEventListener('planora:busy',()=>{refresh();sync();});
  document.addEventListener('planora:negotiate',event=>{
    const detail=event.detail;
    if(detail.eventId!==state.workspace?.id||detail.source.revision!==state.workspace.revision)return;
    if(state.negotiationDirty&&!confirm('Replace unsaved negotiation context with this analyzed source?'))return;
    const chosen=state.workspace.vendors.find(
      v=>(
        detail.source.vendor_id?v.id===detail.source.vendor_id:state.workspace.plan.vendors[v.group_index].key===detail.source.category_key
      )
    );
    if(!chosen){
      error.textContent='Select or create the correct saved vendor record first.';error.hidden=false;return;
    }
    reset();
    baseKnown=false;
    draftRevision=0;
    vendor.value=selectedVendor=chosen.id;
    choices();
    quote.value='';
    sources={source:detail.source,comparisons:detail.comparisons};
    sourceLabel.textContent=`Attached analyzer source: ${detail.source.filename} | ${detail.comparisons.length} other supplied offer(s). Not recorded in ledger.`;
    state.negotiationDirty=true;
    status.textContent=`Reusing ${detail.source.filename} and ${detail.comparisons.length} analyzed comparison(s). Prices will be revalidated; nothing is recorded in the ledger.`;
    metadata();
    root.scrollIntoView({block:'start',behavior:'instant'});
    generate.focus();
  });
  refresh();sync();
}
