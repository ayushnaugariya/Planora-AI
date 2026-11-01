import {checkGuests} from './guest_manager_smoke.mjs';
import {checkNegotiation} from './negotiation_smoke.mjs';
import {checkCommandCenter} from './command_center_smoke.mjs';
import {checkWebsites} from './website_smoke.mjs';
import {checkLegacyCompletion,checkPublicTimeouts} from './final_audit_smoke.mjs';
import {checkAuditNavigation,checkAuditDocs} from './audit_regression_smoke.mjs';
import {checkWizardKeyboard,checkVendorFocus} from './optimization_smoke.mjs';
// Additional real-browser product checks, invoked by browser_workspace_smoke.mjs.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {checkCinematic,checkLanguageAndQuotes} from './cinematic_smoke.mjs';
import {checkMotionRefinement,checkRescueFailureFeedback} from './motion_refinement_smoke.mjs';
import {checkPortal} from './portal_smoke.mjs';
import {checkDecisionLoop} from './decision_loop_smoke.mjs';
import {checkScrollStory} from './scroll_story_smoke.mjs';
import {checkSignature} from './signature_smoke.mjs';
import {checkReadiness} from './readiness_smoke.mjs';
import {checkEventPortal} from './event_portal_smoke.mjs';

export async function runProductSmoke({evaluate,send,waitFor,savedEvent,restart}){
  const artifacts=path.resolve('.artifacts/planora');mkdirSync(artifacts,{recursive:true});
  const visible=id=>`!document.getElementById('${id}').hidden`;
  const settle=()=>new Promise(resolve=>setTimeout(resolve,450));
  async function capture(name,selector=null){
    await evaluate(selector?`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'start',behavior:'instant'})`:"scrollTo({top:0,behavior:'instant'});document.getElementById('sidebar').scrollTop=0");
    await settle();
    const image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    writeFileSync(path.join(artifacts,`${name}.png`),Buffer.from(image.data,'base64'));
  }
  async function click(selector){
    await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el||!el.getClientRects().length||el.disabled)throw Error('Control unavailable: '+${JSON.stringify(selector)});el.scrollIntoView({block:'center',behavior:'instant'});})()`);
    // Wait for scroll/reveal geometry before dispatching a real pointer click.
    // This does not retry a failed action or bypass disabled/covered controls.
    let previous=null;
    for(let i=0;i<16;i++){
      await new Promise(resolve=>setTimeout(resolve,60));
      const current=await evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:r.x,y:r.y};})()`);
      if(previous&&Math.abs(current.x-previous.x)<.5&&Math.abs(current.y-previous.y)<.5)break;
      previous=current;
    }
    const rect=await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el||!el.getClientRects().length||el.disabled)throw Error('Control unavailable: '+${JSON.stringify(selector)});el.scrollIntoView({block:'center',behavior:'instant'});const r=el.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await send('Input.dispatchMouseEvent',{type:'mousePressed',...rect,button:'left',clickCount:1});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',...rect,button:'left',clickCount:1});
  }
  async function values(fields){
    await evaluate(`(()=>{for(const [id,value] of Object.entries(${JSON.stringify(fields)})){const el=document.getElementById(id);if(el.type==='checkbox')el.checked=value;else el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}})()`);
  }
  async function viewport(width,height=960){await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<760});await settle();}
  async function noOverflow(){assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'Unexpected horizontal page overflow');}
  await viewport(1440);await evaluate("location.hash='#/';scrollTo(0,0)");await waitFor(visible('landing-view'));
  await capture('landing-desktop');await noOverflow();
  await checkCinematic({evaluate,send,waitFor,click,viewport});
  await checkMotionRefinement({evaluate,send,waitFor,click,viewport});
  await checkPortal({evaluate,send,waitFor,click,viewport});
  await checkScrollStory({evaluate,send,waitFor,click,viewport});
  await click('a[href="#experience"]');
  await waitFor("document.querySelector('#demo-content .demo-total')?.textContent.includes('20,000')");
  const eventsBefore=await evaluate("fetch('/api/events').then(r=>r.json())");
  await click('#demo-rescue-tab');await waitFor("document.getElementById('demo-rescue-tab').getAttribute('aria-selected')==='true'");await click('#demo-content .demo-option');
  assert(await evaluate("document.querySelector('#demo-content .primary').disabled"));
  await click('#demo-approval');await click('#demo-content .primary');
  await waitFor("document.getElementById('demo-content').textContent.includes('SIMULATED APPROVAL')");
  assert.deepEqual(await evaluate("fetch('/api/events').then(r=>r.json())"),eventsBefore);
  await capture('landing-demo');

  await click('.hero-actions [data-new-event]');await waitFor(visible('creation-view'));
  await values({title:'Planora product smoke'});
  await evaluate(`(()=>{const previous=window.confirm;try{window.confirm=()=>false;const select=document.getElementById('saved-event-select');select.value=${JSON.stringify(eventsBefore[0].id)};select.dispatchEvent(new Event('change'));}finally{window.confirm=previous;}})()`);
  assert.equal(await evaluate("document.getElementById('saved-event-select').value"),'');
  assert.equal(await evaluate("document.getElementById('title').value"),'Planora product smoke');
  await checkWizardKeyboard({evaluate,send,waitFor,click,values});
  await click('#wizard-next');
  await values({city:'Pune',guest_count:'60'});await click('#wizard-next');
  await values({budget:'90000',currency:'INR'});await click('#wizard-next');
  await values({theme:'Candlelit garden',accessibility_requirements:'Step-free entrance'});
  await click('#wizard-back');await click('#wizard-next');
  assert.equal(await evaluate("document.getElementById('theme').value"),'Candlelit garden');
  await click('#wizard-next');await waitFor("document.getElementById('wizard-position').textContent==='5 / 5'");
  await capture('wizard-review');await click('#submit-btn');
  await waitFor("document.getElementById('workspace-status').textContent==='Event and plan saved.'&&!document.getElementById('submit-btn').disabled");
  await waitFor(visible('app-shell'));
  const id=await evaluate("JSON.parse(localStorage.getItem('eventra:selected-event'))");
  assert(id);await waitFor(visible('panel-overview'));await capture('overview-desktop');
  await checkVendorFocus({evaluate,send,waitFor,click,values,savedEvent,id});
  let event=await savedEvent(id);assert.equal(event.vendors[0].name,'Test garden venue');assert.equal(event.vendors[0].booking_status,'booked');
  await capture('vendors-desktop');
  await click('#tab-checklist');await waitFor(visible('panel-checklist'));
  await values({'checklist-search':'impossible search query'});assert.equal(await evaluate("document.querySelectorAll('#checklist-items input').length"),0);
  await values({'checklist-search':''});await click('#checklist-items input');
  await waitFor("document.getElementById('workspace-status').textContent==='Checklist saved.'&&!document.getElementById('submit-btn').disabled");
  assert((await savedEvent(id)).tasks.some(item=>item.completed));
  await click('#tab-guests');await waitFor(visible('panel-guests'));await waitFor("document.querySelector('[data-guest-stat=total_invited]')?.textContent==='0'");
  assert(await evaluate("document.getElementById('guest-summary').textContent.includes('Managed in the private guest list')"));
  assert(await evaluate("document.getElementById('guest-name').required&&Boolean(document.querySelector('#guest-rsvp option[value=confirmed]'))"));

  // Explicit test-only known zero-cost assumptions, never production sample data.
  const seed=await evaluate(`(async()=>{let event=await fetch('/api/events/${id}').then(r=>r.json());for(const line of event.plan.budget_lines.filter(item=>item.key!=='contingency')){const result=await fetch('/api/events/${id}/budget/expenses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:event.revision,request_id:crypto.randomUUID(),expense:{category_key:line.key,description:'Browser test confirmed '+line.label,currency:event.details.currency,unit_amount:'0'}})});if(!result.ok)throw Error(await result.text());event=await result.json();}return event;})()`);
  await send('Page.reload');await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event')&&!document.getElementById('submit-btn').disabled");
  await click('#tab-budget');await capture('budget-desktop');
  await click('#tab-rescue');await waitFor(visible('panel-rescue'));
  await values({'rescue-kind':'vendor_cancellation','rescue-description':'The venue supplier cancelled. Compare the two replacement quotes.','rescue-fee':'0','rescue-quote-a':'1000.15','rescue-quote-b':'1200.22','rescue-confirm-a':true,'rescue-confirm-b':true});
  await click('#rescue-assess');await waitFor("document.querySelectorAll('#rescue-options .recovery-option').length===2&&!document.getElementById('rescue-assess').disabled");
  assert.deepEqual(await savedEvent(id),seed);
  await click('#rescue-options .recovery-option .primary');await waitFor(visible('scenario-preview'));
  assert(await evaluate("document.getElementById('scenario-apply').disabled"));
  await capture('rescue-desktop');await capture('rescue-review','#scenario-preview');
  await checkRescueFailureFeedback({evaluate,send,waitFor,click,savedEvent,id});
  await click('#scenario-approval');await click('#scenario-apply');
  await waitFor("document.getElementById('scenario-status').textContent==='Scenario applied and saved.'&&!document.getElementById('submit-btn').disabled");
  const rescued=await savedEvent(id);assert.equal(rescued.revision,seed.revision+1);assert.equal(rescued.budget_summary.projected_cost,'1000.15');assert.equal(rescued.vendors[0].booking_status,'cancelled');
  assert.equal(await evaluate("document.getElementById('rescue-action-status').dataset.tone"),'success');
  assert.equal(await evaluate("document.getElementById('tab-rescue').getAttribute('aria-selected')"),'true');
  const history=await evaluate(`fetch('/api/events/${id}/scenarios').then(r=>r.json())`);
  assert.equal(history.filter(item=>item.status==='applied').length,1);
  assert(history.some(item=>item.status==='pending'&&item.stale));

  await values({'rescue-kind':'guest_change','rescue-description':'Compare two safe guest counts.','rescue-guests':'70','rescue-guests-alt':'75'});
  await click('#rescue-assess');await waitFor("document.querySelector('#rescue-options h4')?.textContent.includes('70')&&!document.getElementById('rescue-assess').disabled");
  await click('#rescue-options .primary');await click('#scenario-discard');
  await waitFor("document.getElementById('scenario-status').textContent==='Preview discarded. Saved event unchanged.'&&!document.getElementById('submit-btn').disabled");
  assert.deepEqual(await savedEvent(id),rescued);
  await click('#rescue-options .recovery-option:nth-child(2) .primary');
  // A concurrent edit makes this preview stale; the frontend must disable apply.
  await evaluate(`fetch('/api/events/${id}',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:${rescued.revision},title:'Planora revised'})}).then(r=>{if(!r.ok)throw Error('concurrent edit failed')})`);
  await click('#scenario-approval');await click('#scenario-apply');
  await waitFor("!document.getElementById('scenario-error').hidden&&!document.getElementById('submit-btn').disabled");
  assert.equal((await savedEvent(id)).details.guest_count,60);
  await send('Page.reload');await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event')&&!document.getElementById('submit-btn').disabled");
  const beforeRestart=await savedEvent(id);
  await restart();
  await viewport(1440);
  assert.deepEqual(await savedEvent(id),beforeRestart);
  const persisted=await evaluate(`fetch('/api/events/${id}/scenarios').then(r=>r.json())`);assert(persisted.some(item=>item.status==='applied'));assert(persisted.some(item=>item.status==='discarded'));
  await evaluate(`location.hash='#/event/${id}/rescue'`);await waitFor(visible('panel-rescue'));
  await evaluate(`location.hash='#/event/${id}/timeline'`);await waitFor(visible('panel-timeline'));
  await send('Page.reload');await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event')&&!document.getElementById('submit-btn').disabled");await waitFor(visible('panel-timeline'));
  await send('Runtime.evaluate',{expression:'history.back()'});await waitFor(visible('panel-rescue'));
  await evaluate("document.getElementById('tab-overview').focus()");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowDown',code:'ArrowDown'});
  await waitFor(visible('panel-budget'));
  assert.equal(await evaluate('document.activeElement.id'),'tab-budget');
  await click('#sidebar-collapse');assert(await evaluate("document.body.classList.contains('sidebar-collapsed')"));
  await click('#sidebar-collapse');assert(!(await evaluate("document.body.classList.contains('sidebar-collapsed')")));
  await checkLanguageAndQuotes({evaluate,send,waitFor,click,values,savedEvent,id});

  await viewport(390,844);await evaluate("location.hash='#/';scrollTo(0,0)");await waitFor(visible('landing-view'));await capture('landing-mobile');await noOverflow();
  await click('.public-menu-toggle');assert.equal(await evaluate("document.querySelector('.public-menu-toggle').getAttribute('aria-expanded')"),'true');await click('.site-links a');
  await evaluate(`location.hash='#/event/${id}/overview'`);await waitFor(visible('panel-overview'));await capture('overview-mobile');await noOverflow();
  await click('#mobile-menu');await settle();assert.equal(await evaluate("document.getElementById('sidebar').inert"),false);
  await click('#tab-budget');await waitFor(visible('panel-budget'));assert.equal(await evaluate("document.getElementById('mobile-menu').getAttribute('aria-expanded')"),'false');await noOverflow();await capture('budget-mobile');
  for(const section of ['vendors','guests','checklist','timeline','scenarios','rescue','ask','ideas','settings']){
    await evaluate(`location.hash='#/event/${id}/${section}'`);await waitFor(visible(`panel-${section}`));await noOverflow();
  }
  await evaluate(`location.hash='#/event/${id}/rescue'`);await waitFor(visible('panel-rescue'));await capture('rescue-mobile');
  await click('#mobile-menu');await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});assert.equal(await evaluate("document.activeElement.id"),'mobile-menu');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await evaluate("location.hash='#/';scrollTo(0,0)");await waitFor(visible('landing-view'));
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.hero-copy h1')).animationDuration"),'1e-06s');
  await capture('landing-reduced-motion');await noOverflow();
  await viewport(768);await evaluate(`location.hash='#/event/${id}/scenarios'`);await waitFor(visible('panel-scenarios'));await noOverflow();
  console.log('PASS landing/demo, five-step wizard, vendor edit, checklist, real Rescue compare/approve/discard/stale handling, persisted history and restart');
  console.log('PASS desktop/mobile/tablet routes, mobile menu/escape, overflow checks and reduced motion; screenshots: .artifacts/planora');
  await checkDecisionLoop({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkSignature({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkReadiness({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkGuests({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkNegotiation({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkCommandCenter({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkWebsites({evaluate,send,waitFor,click,viewport,values,restart,savedEvent});
  await checkLegacyCompletion({evaluate,send,waitFor,click,viewport,values,savedEvent});
  await checkPublicTimeouts({evaluate,send,waitFor,click,viewport,values,savedEvent});
  await checkEventPortal({evaluate,send,waitFor,click,viewport});
  await checkAuditNavigation({evaluate,send,waitFor,click,viewport});
  await checkAuditDocs({evaluate,send,waitFor,click,viewport});
}
