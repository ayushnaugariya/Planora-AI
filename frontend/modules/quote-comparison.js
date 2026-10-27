import {state} from './state.js';
import {$,h,clear,financialMoney} from './helpers.js';

// Both previews use the original server scenario API; the browser calculates no totals.
export function mountQuoteComparison({api,setWorkspaceBusy,hasUnsavedDetails,fillScenarioInputs,renderScenarioPreview,refreshScenarios}){
  const tool=h('details',{id:'quote-comparison'},h('summary',{text:'Compare written quotes'}));
  const form=h('form',{id:'quote-comparison-form'});
  const field=(id,label,input)=>h('div',{class:'field'},h('label',{htmlFor:id,text:label}),input);
  const category=h('select',{id:'quote-category'},h('option',{value:'catering',text:'Catering'}),h('option',{value:'venue',text:'Venue'}));
  const expense=h('select',{id:'quote-expense'});
  form.append(h('p',{class:'muted',text:'Compare two user-supplied all-in quotes in your saved currency. Taxes and fees must be included. No availability or booking is confirmed.'}),
    h('div',{class:'row2'},field('quote-category','Category',category),field('quote-expense','Saved expense to compare',expense)),
    h('div',{class:'row2'},...['a','b'].map(key=>field(`quote-${key}`,`Quote ${key.toUpperCase()}: all-in amount`,h('input',{id:`quote-${key}`,type:'number',min:'0',max:'100000000',step:'.01',required:true})))),
    h('button',{type:'submit',class:'primary',id:'quote-compare-button',text:'Create two isolated previews'}));
  const status=h('p',{id:'quote-comparison-status',role:'status','aria-live':'polite'}),options=h('div',{id:'quote-comparison-options',class:'quote-options'});
  tool.append(form,status,options);$('scenario-interpret-form').closest('details').after(tool);
  let savedId=null,baseRevision=null,workspaceId=null;
  form.addEventListener('input',()=>{state.quoteDirty=true;});
  form.addEventListener('change',()=>{state.quoteDirty=true;});
  const clearDraft=h('button',{type:'button',class:'ghost',id:'quote-clear',text:'Clear quote inputs'});
  clearDraft.addEventListener('click',()=>{if(state.workspaceBusy)return;form.reset();state.quoteDirty=false;choices();status.textContent='Quote inputs cleared. Saved previews are kept.';});form.append(clearDraft);
  function choices(){
    const previous=expense.value;clear(expense);if(!state.workspace)return;
    const rows=state.workspace.expenses.filter(item=>!item.cancelled&&item.category_key===category.value);
    expense.append(h('option',{value:'',text:rows.length?'Choose the specific saved expense':'No record: preview a new hypothetical expense'}));
    for(const row of rows)expense.append(h('option',{value:row.id,text:row.description}));
    if(rows.some(item=>item.id===previous))expense.value=previous;
    else if(rows.length===1)expense.value=rows[0].id;
  }
  category.addEventListener('change',choices);
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(!state.workspace||state.workspaceBusy)return;
    if(hasUnsavedDetails(true)){status.textContent='Save or clear other unsaved edits before comparing the saved event.';return;}
    const records=state.workspace.expenses.filter(item=>!item.cancelled&&item.category_key===category.value);
    if(records.length&&!expense.value){status.textContent='Which saved expense should these quotes replace? Select a record first.';expense.focus();return;}
    const inputs=['a','b'].map(key=>$(`quote-${key}`).value);
    const eventId=state.workspace.id,revision=state.workspace.revision;
    savedId=eventId;baseRevision=revision;clear(options);setWorkspaceBusy(true);$('quote-compare-button').disabled=true;
    status.textContent='Saving separate quote previews. Your event stays unchanged…';
    let completed=0;
    try{
      for(let i=0;i<inputs.length;i++){
        const response=await api(`/api/events/${eventId}/scenarios`,{revision,parameters:{type:'category_cost',category_key:category.value,amount:inputs[i],expense_id:expense.value||null}});
        const preview=await response.json();completed++;
        const button=h('button',{type:'button',class:'ghost',text:`Review quote ${i===0?'A':'B'} →`});
        button.addEventListener('click',()=>{
          if(state.workspace?.id!==eventId)return;
          if(hasUnsavedDetails(true)){status.textContent='Save or clear unsaved edits before opening this preview.';return;}
          state.selectedScenario=preview;state.scenarioDirty=false;fillScenarioInputs(preview.parameters);renderScenarioPreview();$('scenario-preview').scrollIntoView({block:'start',behavior:'instant'});
        });
        options.append(h('article',{class:'quote-option'},h('span',{class:'badge',text:`QUOTE ${i===0?'A':'B'} · ${preview.feasibility.toUpperCase()}`}),h('h4',{text:financialMoney(preview.parameters.amount)}),h('p',{text:`Proposed recorded cost: ${financialMoney(preview.proposed_budget.projected_cost)}`}),h('p',{class:'muted',text:'Existing payments and commitments remain in the server calculation.'}),button));
      }
      status.textContent='Two previews saved. Compare each with the original event; explicit approval is still required.';
      state.quoteDirty=false;
    }catch(error){status.textContent=`${completed} preview(s) saved; comparison did not complete. ${error.message} Saved previews remain available; the event was not changed.`;}
    finally{setWorkspaceBusy(false);$('quote-compare-button').disabled=false;await refreshScenarios();}
  });
  document.addEventListener('planora:workspace',()=>{
    if(workspaceId!==state.workspace?.id){clear(options);status.textContent='';savedId=null;baseRevision=null;form.reset();state.quoteDirty=false;workspaceId=state.workspace?.id;}
    else if(baseRevision&&baseRevision!==state.workspace?.revision)status.textContent='The event revision changed. These quote snapshots are stale; create a fresh comparison before applying.';
    choices();
  });
  document.addEventListener('planora:status',()=>{if(!state.workspace&&workspaceId){workspaceId=null;savedId=null;baseRevision=null;clear(options);status.textContent='';form.reset();state.quoteDirty=false;}});
  choices();
}
