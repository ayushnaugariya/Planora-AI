import {$,h,clear,financialMoney,fmtDate} from './helpers.js';
import {state} from './state.js';

export function mountSignatureIntelligence({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails,fillScenarioInputs,renderScenarioPreview,refreshScenarios,go}){
  const field=(label,input)=>h('div',{class:'field'},h('label',{htmlFor:input.id,text:label}),input);
  const error=()=>h('p',{class:'error',role:'alert',hidden:true});
  const list=(label,items)=>{const ul=h('ul');for(const text of items)ul.append(h('li',{text}));return h('div',{},h('h4',{text:label}),ul);};
  const section=(id,kicker,title,copy)=>h('section',{id,class:'surface signature-tool'},h('p',{class:'eyebrow',text:kicker}),h('h3',{text:title}),h('p',{class:'muted',text:copy}));
  let context='',quotes=[],preferredToken=0;
  async function action(button,err,fn){
    if(!state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails()){err.textContent='Save or cancel unsaved edits before analyzing the saved event.';err.hidden=false;return;}
    err.hidden=true;const id=state.workspace.id,revision=state.workspace.revision;
    const originalText=button.textContent;setWorkspaceBusy(true);button.disabled=true;button.setAttribute('aria-busy','true');button.textContent='Working from saved facts…';
    try{await fn({id,revision});}catch(ex){err.textContent=ex.message;err.hidden=false;}
    finally{setWorkspaceBusy(false);button.disabled=false;button.removeAttribute('aria-busy');button.textContent=originalText;syncReview();}
  }
  const endpoint=id=>`/api/events/${id}/intelligence`;
  const decision=section('decision-engine','GROUNDED DECISION ENGINE','A question. A considered way forward.','Analyze saved facts, see the impact and save a separate preview. Analysis never changes your event.');
  const question=h('textarea',{id:'decision-question',maxLength:400,minLength:2,required:true,rows:2,placeholder:'How can I reduce my event budget by ₹50,000?'});
  const ask=h('button',{id:'decision-analyze',type:'submit',class:'primary',text:'Analyze my saved event'}),decisionError=error(),decisions=h('div',{id:'decision-cards',class:'signature-grid'});
  decision.append(h('form',{id:'decision-form'},field('Your planning question',question),ask,decisionError),decisions);$('panel-ask').prepend(decision);
  $('decision-form').addEventListener('submit',event=>{event.preventDefault();action(ask,decisionError,async({id,revision})=>{
    const data=await(await api(endpoint(id)+'/decide',{revision,question:question.value.trim()})).json();clear(decisions);
    if(data.clarification)decisions.append(h('p',{role:'status',text:data.clarification}));
    for(const card of data.recommendations){
      const article=h('article',{class:'signature-card'},h('span',{class:'badge',text:`${data.source==='gemini'?'GEMINI INTERPRETATION':'BUILT-IN PLANNER'} · UNSAVED`}),h('h4',{text:card.title}),h('p',{text:card.explanation}),list('Supporting saved facts',card.evidence));
      if(card.preview){
        article.append(h('p',{class:'signature-impact',text:`Total budget: ${financialMoney(card.preview.original_budget.total_budget)} → ${financialMoney(card.preview.proposed_budget.total_budget)}.`}));
        article.append(h('p',{class:'signature-impact',text:`${financialMoney(card.preview.original_budget.projected_cost)} → ${financialMoney(card.preview.proposed_budget.projected_cost)} projected; ${financialMoney(card.preview.budget_impact.projected_cost)} impact.`}));
        const save=h('button',{type:'button',class:'ghost',text:'Save isolated preview for review'});
        save.addEventListener('click',()=>action(save,decisionError,async()=>{
          if(state.workspace.id!==id||state.workspace.revision!==revision)throw Error('Saved facts changed. Analyze again.');
          const preview=await(await api(`/api/events/${id}/scenarios`,{revision,parameters:card.preview.parameters})).json();
          state.selectedScenario=preview;state.scenarioDirty=false;fillScenarioInputs(preview.parameters);renderScenarioPreview();await refreshScenarios();go('scenarios');
        }));article.append(save);
      }else article.append(h('p',{text:'No financial change proposed. Savings are not estimated.'}));
      const assessment={feasible:'Feasible under recorded constraints',infeasible:'Infeasible under recorded constraints',indeterminate:'Essential information is missing'}[card.uncertainty]||card.uncertainty;
      article.append(list('Operational impact',card.operational_impact),list('Trade-offs and assumptions',[...card.tradeoffs,...card.assumptions]),h('p',{class:'muted',text:`Assessment: ${assessment}. Changes require separate explicit approval.`}));decisions.append(article);
    }
  });});

  const quote=section('quote-analyzer','SOURCE → REVIEW → LEDGER','Understand the quote before the commitment.','Supported: labeled UTF-8 .txt, at most 10,000 bytes / 6,000 characters. No PDF, OCR or provider upload. Compare terms as well as prices; nothing records automatically.');
  const category=h('select',{id:'analyzer-category'}),vendor=h('select',{id:'analyzer-vendor'}),expense=h('select',{id:'analyzer-expense'});
  const file=h('input',{id:'analyzer-file',type:'file',accept:'.txt,text/plain'}),source=h('textarea',{id:'analyzer-text',maxLength:6000,minLength:2,required:true,rows:8});
  const template=h('button',{id:'analyzer-template',type:'button',class:'ghost',text:'Use labeled-text example'}),analyze=h('button',{id:'analyzer-analyze',type:'submit',class:'primary',text:'Analyze source text'}),quoteError=error(),quoteStatus=h('p',{id:'analyzer-status',role:'status'}),comparison=h('div',{id:'analyzer-results'});
  const recordAs=h('select',{id:'analyzer-record-as'},h('option',{value:'quote',text:'Record quote only'}),h('option',{value:'commitment',text:'Record quote and explicitly confirmed full commitment'}));
  let filename='quote.txt';
  quote.append(h('form',{id:'analyzer-form'},h('div',{class:'signature-fields'},field('Service category',category),field('Linked vendor record (optional)',vendor)),field('Optional plain-text file',file),template,field('Quote source (edit to resolve missing terms)',source),analyze,quoteError),h('div',{class:'signature-fields'},field('Expense to update; no duplicate cost records',expense),field('Reviewed recording choice',recordAs)),quoteStatus,comparison);$('panel-vendors').prepend(quote);
  function choices(){
    if(!state.workspace)return;const previous=category.value;clear(category);
    for(const line of state.workspace.plan.budget_lines)if(line.key!=='contingency')category.append(h('option',{value:line.key,text:line.label}));
    if([...category.options].some(option=>option.value===previous))category.value=previous;
    targets();
    clear(taskSelect);for(const task of state.workspace.tasks){const milestone=state.workspace.plan.timeline[task.milestone_index];if(!task.completed&&milestone.category!=='event')taskSelect.append(h('option',{value:task.id,text:`${milestone.title} · ${fmtDate(milestone.due)}`}));}
  }
  function targets(){
    if(!state.workspace)return;const chosen=expense.value;clear(vendor);clear(expense);
    vendor.append(h('option',{value:'',text:'No vendor link selected'}));
    for(const item of state.workspace.vendors)if(state.workspace.plan.vendors[item.group_index].key===category.value)vendor.append(h('option',{value:item.id,text:item.name||state.workspace.plan.vendors[item.group_index].label}));
    expense.append(h('option',{value:'',text:'New record only when no active category costs exist'}));
    const records=state.workspace.expenses.filter(item=>!item.cancelled&&item.category_key===category.value);
    for(const item of records)expense.append(h('option',{value:item.id,text:item.description}));
    if(records.some(item=>item.id===chosen))expense.value=chosen;else if(records.length===1)expense.value=records[0].id;
  }
  category.addEventListener('change',()=>{targets();quotes=[];renderQuotes();});vendor.addEventListener('change',()=>{quotes=[];renderQuotes();});
  template.addEventListener('click',()=>{filename='quote.txt';source.value=`Vendor: Example supplier\nCurrency: ${state.workspace?.details.currency||'INR'}\nItem: Service package | 1 | 1000\nTax: 0\nFee: 0\nAll-in total: 1000\nDeposit: 200\nPayment: ${state.workspace?.details.event_date||'2027-01-01'} | 1000\nCancellation: Confirm deposit terms\nInclusions: Service package\nOvertime: Not included`;});
  file.addEventListener('change',async()=>{const selected=file.files[0];if(!selected)return;quoteError.hidden=true;try{
    if(selected.size>10000||!/^.+\.txt$/i.test(selected.name)||selected.type&&selected.type!=='text/plain')throw Error('Choose a UTF-8 .txt file up to 10,000 bytes.');
    const buffer=await selected.arrayBuffer();source.value=new TextDecoder('utf-8',{fatal:true}).decode(buffer);filename=selected.name;
  }catch(ex){quoteError.textContent=ex.message;quoteError.hidden=false;file.value='';}});
  $('analyzer-form').addEventListener('submit',event=>{event.preventDefault();action(analyze,quoteError,async({id,revision})=>{
    const payload={revision,filename,media_type:'text/plain',text:source.value,category_key:category.value,vendor_id:vendor.value||null};
    const analysis=await(await api(endpoint(id)+'/quotes/analyze',payload)).json();
    quotes.push({analysis,payload,requestId:crypto.randomUUID(),eventId:id});quotes=quotes.slice(-3);renderQuotes();
  });});
  function syncReview(){for(const button of comparison.querySelectorAll('[data-quote-record]'))button.disabled=state.workspaceBusy||!button.closest('article').querySelector('input[type=checkbox]').checked||button.dataset.importable!=='true';}
  const quoteMoney=(value,analysis)=>analysis.currency?financialMoney(value,analysis.currency):value===null?'Unknown':`${value} (currency missing)`;
  function renderQuotes(){
    clear(comparison);quoteStatus.textContent=quotes.length?`${quotes.length} source(s) in this category. Keep each quote's currency; no FX conversion or lowest-price ranking. Compare inclusions and conditions.`:'';
    if(quotes.length){
      const header=h('tr');for(const text of ['Source','Currency','All-in','Tax / fee','Quoted deposit','Terms / recording'])header.append(h('th',{scope:'col',text}));
      const rows=h('tbody');for(const {analysis:a} of quotes)rows.append(h('tr',{},h('th',{scope:'row',text:a.vendor_name||a.filename}),h('td',{text:a.currency||'Not supplied'}),h('td',{text:quoteMoney(a.comparable_total,a)}),h('td',{text:`${quoteMoney(a.tax,a)} / ${quoteMoney(a.fee,a)}`}),h('td',{text:quoteMoney(a.deposit,a)}),h('td',{text:`${a.missing.length} missing term(s); ${a.importable?'review required':'cannot record'}`})));
      comparison.append(h('div',{class:'table-wrap signature-quote-table'},h('table',{},h('caption',{text:'Normalized service category; prices retain source currency and do not establish equivalent inclusions'}),h('thead',{},header),rows)));
    }
    for(const entry of quotes){const a=entry.analysis;
      const article=h('article',{class:'signature-card'},h('span',{class:'badge',text:'BUILT-IN TEXT ANALYSIS · UNVERIFIED SUPPLIER TERMS'}),h('h4',{text:a.vendor_name||a.filename}),h('p',{class:'signature-impact',text:`Quoted all-in: ${quoteMoney(a.comparable_total,a)} · quoted deposit: ${quoteMoney(a.deposit,a)}`}),h('p',{class:'muted',text:'A quoted deposit is not a recorded payment. Source terms may be incomplete.'}));
      const evidence=h('dl',{class:'review-grid'});for(const item of a.items)evidence.append(h('div',{},h('dt',{text:item.description}),h('dd',{text:`${item.quantity} × ${quoteMoney(item.unit_price,a)} = ${quoteMoney(item.total,a)}`}),h('small',{text:item.source})));article.append(evidence);
      article.append(list('Conditions and missing information',[...a.issues,...a.missing.map(item=>`Not supplied: ${item}`),...Object.entries(a.terms).map(([key,value])=>`${key}: ${value}`)]));
      const details=h('details',{},h('summary',{text:'Inspect original source and extracted evidence'}),h('pre',{text:a.source_text}));for(const [key,value] of Object.entries(a.evidence))details.append(h('p',{class:'muted',text:`${key}: ${value}`}));article.append(details);
      const negotiate=h('button',{type:'button',class:'ghost',text:'Use in negotiation','data-negotiate-source':entry.requestId});
      negotiate.addEventListener('click',()=>document.dispatchEvent(new CustomEvent('planora:negotiate',{detail:{eventId:entry.eventId,source:entry.payload,comparisons:quotes.filter(other=>other!==entry).slice(-2).map(other=>other.payload)}})));article.append(negotiate);
      const approval=h('input',{id:`quote-review-${entry.requestId}`,type:'checkbox'}),record=h('button',{type:'button',class:'primary',text:'Record reviewed choice',disabled:true,'data-quote-record':true,'data-importable':String(a.importable)});
      approval.addEventListener('change',syncReview);article.append(h('label',{htmlFor:approval.id,class:'signature-approval'},approval,'I reviewed this source, the selected expense and the recording choice.'),record);
      record.addEventListener('click',()=>{if(!approval.checked||!a.importable)return;action(record,quoteError,async()=>{
        const body={...entry.payload,request_id:entry.requestId,approved:true,expense_id:expense.value||null,record_as:recordAs.value};
        if(state.workspace.id!==entry.eventId||state.workspace.revision!==body.revision)throw Error('Saved facts changed. Analyze again before recording.');
        const saved=await(await api(endpoint(entry.eventId)+'/quotes/record',body)).json();applyWorkspace(saved,true,true);quoteStatus.textContent='Reviewed cost recorded and verified in the saved ledger. No payment was inferred.';
      });});comparison.append(article);
    }
    syncReview();
  }

  const design=section('design-studio','CONNECTED DESIGN STUDIO','A feeling, with a place in your plan.','Local concept inspiration with your saved budget context. These mood boards are not photographs, vendor offerings or priced designs.');
  const brief=h('textarea',{id:'design-brief',rows:3,maxLength:300,minLength:2,required:true,placeholder:'Warm candlelight, accessible routes and a simple garden focal point'}),colors=h('input',{id:'design-colors',type:'text',placeholder:'#f2e5d4, #59453c'}),generate=h('button',{id:'design-generate',type:'submit',class:'primary',text:'Explore three concepts'}),designError=error(),concepts=h('div',{id:'design-concepts',class:'signature-grid'}),preferred=h('div',{id:'design-preferred',role:'status'});
  design.append(h('form',{id:'design-form'},field('Design brief and priorities',brief),field('Optional palette: up to four six-digit hex colors',colors),generate,designError),preferred,concepts);$('panel-ideas').prepend(design);
  $('design-form').addEventListener('submit',event=>{event.preventDefault();action(generate,designError,async({id,revision})=>{
    const payload={revision,brief:brief.value.trim(),colors:colors.value.split(',').map(value=>value.trim()).filter(Boolean)};
    const data=await(await api(endpoint(id)+'/design',payload)).json();clear(concepts);
    for(const item of data.concepts){
      const board=h('div',{class:`concept-mood concept-${item.style}`,'aria-label':`${item.title} local illustrative mood board`},h('div',{class:'concept-vault'},h('span',{text:'p'})),h('p',{text:item.title}));for(let i=0;i<4;i++)board.style.setProperty(`--concept-${i+1}`,item.palette[i%item.palette.length]);
      const palette=h('div',{class:'concept-palette'});for(const color of item.palette){const swatch=h('span',{text:color});swatch.style.setProperty('--swatch',color);palette.append(swatch);}
      const save=h('button',{type:'button',class:'ghost',text:'Save as preferred concept'}),quoteLink=h('button',{type:'button',class:'ghost',text:'Price this direction with a written quote'});
      const article=h('article',{class:'signature-card'},board,palette,h('span',{class:'badge',text:`${data.ranking_source==='gemini'?'GEMINI ORDERING':'BUILT-IN ORDERING'} · LOCAL RECIPES`}),list('Design direction',Object.entries(item.directions).map(([key,value])=>`${key}: ${value}`)),list('Linked saved allowances',item.budget_links.map(line=>`${line.label}: ${financialMoney(line.allowance,line.currency)} allowance; ${financialMoney(line.recorded_projected,line.currency)} recorded. ${line.note}`)),list('Assumptions',item.assumptions),save,quoteLink);
      save.addEventListener('click',()=>action(save,designError,async()=>{if(state.workspace.id!==id||state.workspace.revision!==revision)throw Error('Event changed. Regenerate the design context.');await api(endpoint(id)+'/design/preferred',{...payload,style:item.style,approved:true});await loadPreferred();}));
      quoteLink.addEventListener('click',()=>{go('vendors');category.value=[...category.options].some(option=>option.value==='decor')?'decor':category.value;targets();source.focus();});concepts.append(article);
    }
  });});
  async function loadPreferred(){
    if(!state.workspace)return;const token=++preferredToken,id=state.workspace.id;
    try{const data=await(await api(endpoint(id)+'/design/preferred',undefined,'GET')).json();if(token!==preferredToken||state.workspace?.id!==id)return;clear(preferred);
      preferred.append(h('p',{text:data?`Preferred: ${data.concept.title} · ${data.stale?'budget context changed; regenerate before relying on allowances':'saved for this event'}`:'No preferred concept saved yet.'}));
      if(data){
        preferred.append(h('p',{text:`Saved brief: ${data.brief}`}));
        const palette=h('div',{class:'concept-palette'});for(const color of data.concept.palette){const swatch=h('span',{text:color});swatch.style.setProperty('--swatch',color);palette.append(swatch);}preferred.append(palette);
        preferred.append(h('details',{},h('summary',{text:'Reopen the saved concept directions and budget snapshot'}),list('Saved directions',Object.entries(data.concept.directions).map(([key,value])=>`${key}: ${value}`)),list(`Saved revision ${data.base_revision} allowances`,data.concept.budget_links.map(line=>`${line.label}: ${financialMoney(line.allowance,line.currency)} allowance; ${financialMoney(line.recorded_projected,line.currency)} recorded.`))));
        const restore=h('button',{type:'button',class:'ghost',text:'Edit this saved brief'});restore.addEventListener('click',()=>{brief.value=data.brief;colors.value=data.concept.palette.join(', ');brief.focus();});preferred.append(restore);
      }
    }catch(ex){if(token===preferredToken){preferred.textContent=ex.message;}}
  }

  const timeline=section('timeline-intelligence','SAVED DEPENDENCIES · EXPLICIT ASSUMPTIONS','If one task slips, what follows?','Analyze recorded links with a buffer you supply. No task owners, durations or supplier capacity are inferred. This analysis cannot apply dates.');
  const taskSelect=h('select',{id:'delay-task',required:true}),days=h('input',{id:'delay-days',type:'number',min:0,max:90,step:1,value:3,required:true}),buffer=h('input',{id:'delay-buffer',type:'number',min:0,max:14,step:1,value:0,required:true}),delay=h('button',{id:'delay-analyze',type:'submit',class:'primary',text:'Analyze delay impact'}),delayError=error(),impacts=h('div',{id:'delay-results'});
  timeline.append(h('form',{id:'delay-form'},field('Open saved milestone',taskSelect),h('div',{class:'signature-fields'},field('Delay in days',days),field('Buffer after affected prerequisites (days)',buffer)),delay,delayError),impacts);$('panel-timeline').prepend(timeline);
  $('delay-form').addEventListener('submit',event=>{event.preventDefault();action(delay,delayError,async({id,revision})=>{
    const data=await(await api(endpoint(id)+'/timeline',{revision,task_id:taskSelect.value,delay_days:Number(days.value),buffer_days:Number(buffer.value)})).json();clear(impacts);
    impacts.append(list('Constraints and assumptions',[...data.issues,...data.assumptions]));
    const ul=h('ul');for(const item of data.impacts)ul.append(h('li',{text:`${item.title}: ${fmtDate(item.original_due)} → ${fmtDate(item.proposed_due)}${item.beyond_event?' · crosses event date':''}`}));impacts.append(ul);
    const recovery=h('button',{type:'button',class:'ghost',text:'Explore a date alternative in Event Rescue'});recovery.addEventListener('click',()=>{go('rescue');$('rescue-kind').value='timeline_risk';$('rescue-kind').dispatchEvent(new Event('change'));});impacts.append(recovery);
  });});
  function render(){
    const key=state.workspace?`${state.workspace.id}/${state.workspace.revision}`:'';
    if(key.split('/')[0]!==context.split('/')[0]){source.value='';file.value='';filename='quote.txt';question.value='';brief.value='';colors.value='';recordAs.value='quote';}
    if(key!==context){context=key;quotes=[];clear(decisions);clear(concepts);clear(impacts);clear(preferred);clear(comparison);quoteStatus.textContent='';preferredToken++;}
    choices();syncReview();if(location.hash.endsWith('/ideas'))loadPreferred();
  }
  document.addEventListener('planora:busy',syncReview);document.addEventListener('planora:workspace',render);document.addEventListener('planora:view',event=>{if(event.detail==='ideas')loadPreferred();});render();
}
