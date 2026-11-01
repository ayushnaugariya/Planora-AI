import {state} from './state.js';
import {$,h,clear,fmtDate,financialMoney,store} from './helpers.js';

const views = {
  website:[
    'Your occasion, beautifully shared',
    'Create an invitation from your saved event. Preview and approve the public details before publishing.'
  ],
  command:[
    'Your event, in motion',
    'Coordinate the day with saved tasks, arrivals and incidents. Every operational change needs your approval.'
  ],
  overview:[
    'Your occasion, at a glance','A clear view of the details you have saved, and what needs your attention.'
  ],
  budget:[
    'A little room for everything','Keep allowances, estimates, commitments and payments in the same picture.'
  ],
  vendors:[
    'Good people. Clear details.',
    'Keep contacts, booking status and the right questions together. Supplier availability is not checked live.'
  ],
  guests:[
    'Make everyone feel welcome',
    'Plan the headcount, dietary needs and access requirements that shape your occasion.'
  ],
  checklist:['One thoughtful step at a time','A focused list of the tasks in your saved event timeline.'],
  timeline:[
    'The right thing, at the right time',
    'Your saved planning milestones, from the first booking to the day itself.'
  ],
  scenarios:[
    'Your What-If Studio','Explore a separate snapshot. Compare the impact, then choose what becomes real.'
  ],
  rescue:[
    'A change of plans. A way forward.',
    'Turn a disruption into grounded options. Every change starts as a preview.'
  ],
  ask:[
    'A thoughtful second opinion',
    'Advice grounded in your saved event. Financial changes always need a separate approved preview.'
  ],
  ideas:[
    'Make it unmistakably yours','Personalized inspiration, with a clear source and room for your own ideas.'
  ],
  settings:[
    'Your event, your rules','Refine the details, rename your occasion, or manage this private workspace.'
  ]
};

export function notify(message,error=false) {
  if (!message) return;
  const toast=$('toast');
  toast.textContent=message;
  toast.classList.toggle('is-error',error);
  toast.hidden=false;
  clearTimeout(notify.timer);notify.timer=setTimeout(()=>{toast.hidden=true;},6500);
}

export function mountShell({wizard,selectTab,openWorkspace,workspaceAction,hasUnsavedDetails}) {
  let routing=false, opening=null, currentSection='';
  const mobile=matchMedia('(max-width:760px)');
  const previewHome=$('scenario-preview').parentElement;
  const sidebar=$('sidebar');
  const brandWord=sidebar.querySelector('.brand>span:last-child');brandWord.classList.add('brand-word');
  function menu(open,returnFocus=false) {
    document.body.classList.toggle('sidebar-open',open);
    $('mobile-menu').setAttribute('aria-expanded',String(open));
    $('sidebar-scrim').hidden=!open;
    sidebar.inert=mobile.matches&&!open;
    if(open) sidebar.querySelector('[aria-selected=true]')?.focus();
    else if(returnFocus) $('mobile-menu').focus();
  }
  $('mobile-menu').addEventListener('click',()=>menu(true));
  $('sidebar-scrim').addEventListener('click',()=>menu(false,true));
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&document.body.classList.contains('sidebar-open')) menu(false,true);
    if(e.key==='Tab'&&mobile.matches&&document.body.classList.contains('sidebar-open')){
      const controls=[...sidebar.querySelectorAll('a,button,select')].filter(
        el=>!el.disabled&&el.getClientRects().length&&el.tabIndex>=0
      );
      const first=controls[0],last=controls.at(-1);
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  });
  mobile.addEventListener('change',()=>menu(false));menu(false);
  $('sidebar-collapse').addEventListener('click',()=>{
    const collapsed=document.body.classList.toggle('sidebar-collapsed');
    $('sidebar-collapse').setAttribute('aria-label',collapsed?'Expand sidebar':'Collapse sidebar');
    store.set('planora:sidebar-collapsed',collapsed);
  });
  if(store.get('planora:sidebar-collapsed',false)) document.body.classList.add('sidebar-collapsed');
  const links=document.querySelector('.site-links');links.id='public-navigation';
  const toggle=h(
    'button',
    {
      type:'button',
      class:'public-menu-toggle icon-button',
      'aria-label':'Open main navigation',
      'aria-expanded':'false',
      'aria-controls':links.id,
      text:'☰'
    }
  );
  links.before(toggle);
  toggle.addEventListener(
    'click',
    ()=>{const open=links.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open));}
  );
  links.addEventListener(
    'click',()=>{links.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');}
  );
  document.addEventListener(
    'keydown',
    event=>{
      if(event.key==='Escape'&&links.classList.contains('is-open')){
        links.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');toggle.focus();
      }
    }
  );

  // Move existing authoritative render targets, retaining their IDs and handlers.
  const source=h('section',{class:'surface overview-source'},h('h3',{text:'The planning picture'}));
  for(const id of ['plan-summary','source-note']) source.append($(id));
  source.append($('health-meter').closest('.health'),$('warnings'));
  $('panel-overview').append(source);
  $('health-label').textContent='Original plan heuristic';
  for(const id of ['rename-event-btn','delete-event-btn','import-event-btn']) $('settings-actions').append(
    $(id)
  );
  const importButton=$('import-event-btn'),
  utilities=h('div',{class:'workspace-actions',id:'gallery-utilities'});
  const refresh=h('button',{type:'button',class:'ghost',text:'Refresh saved events'});
  refresh.addEventListener('click',()=>{$('events-error').hidden=true;$('refresh-events-btn').click();});
  utilities.append(refresh);
  $('event-gallery').after(utilities);
  $('settings-name').addEventListener('input',()=>{$('title').value=$('settings-name').value;});
  document.querySelectorAll('[data-edit-details]').forEach(
    button=>button.addEventListener('click',()=>{wizard.open();location.hash='#/create';})
  );
  document.querySelectorAll('[data-new-event]').forEach(link=>link.addEventListener('click',e=>{
    e.preventDefault();if(state.workspaceBusy)return;
    $('new-event-btn').click();if(!state.workspace){wizard.open();location.hash='#/create';route();}
  }));
  $('new-event-btn').addEventListener(
    'click',()=>{if(!state.workspace){wizard.open();location.hash='#/create';}}
  );
  $('rescue-history-btn').addEventListener('click',()=>go('scenarios'));
  function go(section){if(state.workspace)location.hash=`#/event/${state.workspace.id}/${section}`;}
  function show(view){
    for(const id of ['landing-view','events-view','creation-view','app-shell']) $(id).hidden=id!==view;
    document.body.dataset.view=view;
    if(view!=='app-shell')currentSection='';
    menu(false);
  }
  function section(name){
    if(!views[name])name='overview';
    const key=state.workspace?.id+'/'+name;
    if(currentSection!==key){scrollTo({top:0,behavior:'instant'});currentSection=key;}
    routing=true;selectTab(`tab-${name}`,false);routing=false;
    $('breadcrumb').textContent=$(`tab-${name}`).getAttribute('aria-label');
    $('view-title').textContent=views[name][0];$('view-description').textContent=views[name][1];
    $('view-eyebrow').textContent=name==='rescue'?'EVENT RESCUE':name==='scenarios'?'COMPARE BEFORE YOU COMMIT':'YOUR PLANNING STUDIO';
    if(name==='scenarios')previewHome.append($('scenario-preview'));
    if(name==='rescue'&&state.selectedScenario)$('rescue-review-host').append($('scenario-preview'));
    document.dispatchEvent(new CustomEvent('planora:view',{detail:name}));
  }
  async function route(){
    const hash=location.hash;
    const match=hash.match(/^#\/event\/([a-f0-9-]{36})\/(\w+)$/i);
    if(match){
      show('app-shell');
      if(state.workspace?.id!==match[1]){
        if(state.booting||opening===match[1])return;
        if(hasUnsavedDetails()&&!confirm('Discard unsaved changes and open this event?')){
          go('overview');return;
        }
        opening=match[1];
        await workspaceAction(()=>openWorkspace(match[1]));opening=null;
        if(state.workspace?.id!==match[1]){location.hash='#/events';return;}
      }
      section(match[2]);return;
    }
    if(hash==='#/events'){show('events-view');gallery();scrollTo({top:0,behavior:'instant'});return;}
    if(hash==='#/create'){show('creation-view');return;}
    show('landing-view');
    if(!hash||hash==='#/')scrollTo({top:0,behavior:'instant'});
    if(hash&&!hash.startsWith('#/')) requestAnimationFrame(
      ()=>document.getElementById(hash.slice(1))?.scrollIntoView()
    );
  }
  document.addEventListener(
    'planora:tab',
    e=>{
      if(!routing){
        const focus=mobile.matches&&sidebar.contains(document.activeElement);
        go(e.detail.replace('tab-',''));
        menu(false);
        if(focus)requestAnimationFrame(()=>$(e.detail.replace('tab-','panel-')).focus({preventScroll:true}));
      }
    }
  );
  document.addEventListener('planora:workspace',e=>{
    overview();
    if(state.booting){route();return;}
    const match=location.hash.match(/^#\/event\/([^/]+)\/(\w+)$/);
    const name=e.detail.preserveView&&match?.[1]===state.workspace.id?match[2]:'overview';
    if(opening)return;
    go(name);route();
  });
  document.addEventListener('planora:events',gallery);
  document.addEventListener('planora:status',e=>{
    if(e.detail.error||/saved\.|deleted\.|imported\./i.test(e.detail.message))notify(
      e.detail.error||e.detail.message,Boolean(e.detail.error)
    );
    if(e.detail.error){$('events-error').textContent=e.detail.error;$('events-error').hidden=false;}
    if(!state.workspace&&e.detail.message==='Event deleted.')location.hash='#/events';
  });
  addEventListener('hashchange',route);
  function gallery(){
    const root=$('event-gallery');clear(root);
    if(state.workspace)$('settings-actions').append(importButton);else utilities.append(importButton);
    const events=state.events||[];
    if(!events.length){
      root.append(
        h(
          'div',
          {class:'surface view-empty'},
          h('p',{class:'eyebrow',text:'A FRESH PAGE'}),
          h('h3',{text:state.booting?'Opening your studio…':'Your next occasion starts here.'}),
          h(
            'p',
            {
              class:'muted',
              text:'Saved events belong to this browser session. Create your first event to keep every detail together.'
            }
          )
        )
      );
      return;
    }
    events.forEach(
      (event,index)=>root.append(
        h(
          'a',
          {class:'event-card',href:`#/event/${event.id}/overview`},
          h('span',{class:'event-card-number','aria-hidden':'true',text:String(index+1).padStart(2,'0')}),
          h('span',{class:'badge',text:'SAVED WORKSPACE'}),
          h('h2',{text:event.title}),
          h('p',{text:fmtDate(event.event_date)}),
          h(
            'div',
            {class:'event-card-footer'},
            h('small',{text:`Revision ${event.revision}`}),
            h('span',{text:'Open event →'})
          )
        )
      )
    );
  }
  function overview(){
    if(!state.workspace)return;
    const event=state.workspace,summary=event.budget_summary;
    const root=$('overview-content');clear(root);
    const metric=(label,value,note,accent=false)=>h(
      'div',
      {class:'metric'+(accent?' accent':'')},
      h('small',{text:label}),
      h('strong',{text:value}),
      h('p',{text:note})
    );
    const complete=event.tasks.filter(t=>t.completed).length;
    root.append(
      h(
        'div',
        {class:'metrics'},
        metric('Your total budget',financialMoney(summary.total_budget),'Saved financial target',true),
        metric(
          'Projected cost',
          financialMoney(summary.projected_cost),
          summary.unknown_expenses.length||summary.missing_categories.length?'Incomplete pricing — confirm missing costs':'Based on recorded expense values'
        ),
        metric(
          'Outstanding commitments',
          financialMoney(summary.outstanding_commitments),
          'Committed amounts still to be paid'
        )
      )
    );
    const milestones=h('ul',{class:'overview-list'});
    event.tasks.filter(t=>!t.completed).slice(0,5).forEach(
      task=>{
        const item=event.plan.timeline[task.milestone_index];
        milestones.append(
          h(
            'li',
            {},
            h('div',{},item.title,h('small',{text:fmtDate(item.due)})),
            h('a',{href:`#/event/${event.id}/timeline`,text:'View →'})
          )
        );
      }
    );
    if(!milestones.children.length)milestones.append(h('li',{text:'All saved planning tasks are complete.'}));
    const vendorList=h('ul',{class:'overview-list'});
    event.vendors.slice(0,5).forEach(
      v=>vendorList.append(
        h(
          'li',
          {},
          h(
            'div',
            {},
            v.name||event.plan.vendors[v.group_index].label,
            h('small',{text:v.contact||'Contact to confirm'})
          ),
          h('span',{class:'badge',text:v.booking_status})
        )
      )
    );
    root.append(
      h(
        'div',
        {class:'overview-columns'},
        h(
          'section',
          {class:'surface'},
          h(
            'div',
            {class:'section-heading'},
            h('h3',{text:'Your next few steps'}),
            h(
              'a',
              {
                class:'text-link',
                href:`#/event/${event.id}/checklist`,
                text:`${complete}/${event.tasks.length} complete →`
              }
            )
          ),
          milestones
        ),
        h(
          'section',
          {class:'surface'},
          h('h3',{text:'The people behind the day'}),
          vendorList,
          h('a',{class:'text-link',href:`#/event/${event.id}/vendors`,text:'Manage your vendors →'})
        )
      )
    );
    $('settings-name').value=event.details.title;
    $('settings-meta').textContent=`Revision ${event.revision} · Last saved ${new Date(event.updated_at).toLocaleString()}. Updating full event details rebuilds the plan; existing tracked identities are reconciled.`;
  }
  route();return{go,route,overview};
}
