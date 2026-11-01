import {$,h,clear,financialMoney} from './helpers.js';
import {state} from './state.js';
import {decisionDelta} from './decision-metrics.js';

export function mountDecisionComparison(){
  const root=h(
    'section',
    {class:'surface decision-comparison',id:'decision-comparison','aria-label':'Saved scenario comparison'}
  );
  $('scenario-saved').closest('.field').after(root);
  function render(items=[]){
    clear(root);
    root.append(
      h('p',{class:'eyebrow',text:'ONE EVENT · SEPARATE FUTURES'}),
      h('h3',{text:'Compare before you commit.'}),
      h(
        'p',
        {
          class:'muted',
          text:'Up to six recent saved previews. Each baseline belongs to its recorded revision. Percentages use the absolute baseline; a zero baseline has no percentage.'
        }
      )
    );
    if(!items.length){
      root.append(h('p',{text:'Create a preview to compare its recorded financial impact here.'}));return;
    }
    const head=h('tr');
    for(
      const text of [
        'Preview / revision',
        'Baseline cost',
        'Proposed cost',
        'Difference',
        'Change',
        'Remaining / reserve',
        'Status',
        'Review'
      ]
    )head.append(h('th',{scope:'col',text}));
    const body=h('tbody');
    for(const item of [...items].sort((a,b)=>b.created_at.localeCompare(a.created_at)).slice(0,6)){
      const delta=decisionDelta(item.original_budget.projected_cost,item.proposed_budget.projected_cost);
      const review=h(
        'button',
        {
          type:'button',
          class:'ghost',
          text:'Review',
          'aria-label':`Review ${item.parameters.type.replaceAll('_',' ')} preview from revision ${item.base_revision}`
        }
      );
      review.addEventListener(
        'click',
        ()=>{
          if(state.workspaceBusy)return;
          $('scenario-saved').value=item.id;
          $('scenario-saved').dispatchEvent(new Event('change'));
        }
      );
      body.append(
        h(
          'tr',
          {},
          h('th',{scope:'row',text:`${item.parameters.type.replaceAll('_',' ')} · r${item.base_revision}`}),
          h('td',{text:financialMoney(item.original_budget.projected_cost)}),
          h('td',{text:financialMoney(item.proposed_budget.projected_cost)}),
          h('td',{text:financialMoney(delta.amount)}),
          h('td',{text:delta.percentage===null?'Not defined':`${delta.percentage}%`}),
          h(
            'td',
            {
              text:`${financialMoney(item.proposed_budget.remaining_funds)} / ${financialMoney(item.proposed_budget.contingency_remaining)}`
            }
          ),
          h(
            'td',
            {
              text:`${item.feasibility} · ${item.status}${item.stale||item.base_revision!==state.workspace?.revision?' · stale':''}`
            }
          ),
          h('td',{},review)
        )
      );
    }
    root.append(
      h(
        'div',
        {class:'table-wrap'},
        h(
          'table',
          {},
          h(
            'caption',
            {
              text:'Saved preview financial comparison; review each option for categories, tasks, assumptions and approval'
            }
          ),
          h('thead',{},head),
          body
        )
      )
    );
  }
  document.addEventListener('planora:scenarios',event=>render(event.detail));
  document.addEventListener('planora:workspace',()=>render());render();
}
