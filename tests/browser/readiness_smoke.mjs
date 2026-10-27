import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';

export async function checkReadiness({evaluate,send,waitFor,click,viewport,values,restart,savedEvent}){
  const folder=path.resolve('.artifacts/readiness');mkdirSync(folder,{recursive:true});
  const id=await evaluate("JSON.parse(localStorage.getItem('eventra:selected-event'))");
  const before=await savedEvent(id),others=await evaluate(`fetch('/api/events').then(r=>r.json()).then(async list=>Promise.all(list.filter(e=>e.id!==${JSON.stringify(id)}).map(e=>fetch('/api/events/'+e.id).then(r=>r.json()))))`);
  const report=async()=>evaluate(`fetch('/api/events/${id}/readiness',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:${(await savedEvent(id)).revision}})}).then(r=>{if(!r.ok)throw Error(r.status);return r.json()})`);
  async function overview(){await evaluate(`location.hash='#/event/${id}/overview'`);await waitFor("!document.getElementById('panel-overview').hidden&&Boolean(document.getElementById('readiness-dashboard').dataset.revision)&&!document.getElementById('readiness-refresh').disabled");}
  async function capture(name){await evaluate("document.getElementById('readiness-dashboard').scrollIntoView({block:'start',behavior:'instant'});document.getElementById('toast').hidden=true");await new Promise(r=>setTimeout(r,400));const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(path.join(folder,name+'.png'),Buffer.from(shot.data,'base64'));}
  await viewport(1440);await send('Emulation.setEmulatedMedia',{features:[]});await overview();
  const initial=await report();
  assert.equal(await evaluate("document.querySelectorAll('#readiness-dimensions details').length"),5);
  assert.equal(await evaluate("document.querySelectorAll('#readiness-actions>li').length"),3);
  assert(await evaluate("document.getElementById('readiness-content').textContent.includes('not a readiness score')"));
  assert.equal(await evaluate("document.getElementById('readiness-dashboard').dataset.revision"),String(before.revision));
  assert.deepEqual(await savedEvent(id),before);await capture('overview-desktop');
  await evaluate("document.querySelector('#readiness-dimensions summary').focus()");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  assert(await evaluate("document.querySelector('#readiness-dimensions details').open"));
  await evaluate("document.querySelector('#readiness-actions a').focus()");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  await waitFor(`!document.getElementById('panel-${initial.actions[0].destination}').hidden`);
  assert.deepEqual(await savedEvent(id),before);await overview();
  // Actual failed read must clear old evidence and cannot report verified success.
  await evaluate("window.__readinessFetch=window.fetch;window.fetch=()=>Promise.reject(new Error('Offline fixture'))");
  await click('#readiness-refresh');await waitFor("!document.getElementById('readiness-error').hidden");
  assert.equal(await evaluate("document.getElementById('readiness-content').children.length"),0);
  await evaluate("window.fetch=window.__readinessFetch;delete window.__readinessFetch");await click('#readiness-refresh');
  await waitFor("Boolean(document.getElementById('readiness-dashboard').dataset.revision)&&!document.getElementById('readiness-refresh').disabled");
  await click('#readiness-explain');await waitFor("document.getElementById('readiness-status').textContent.includes('Built-in priorities')&&!document.getElementById('readiness-explain').disabled");
  assert.deepEqual(await savedEvent(id),before);
  const vendor=before.vendors.find(item=>item.booking_status==='cancelled')||before.vendors[0];
  async function saveVendor(status){
    await evaluate(`location.hash='#/event/${id}/vendors'`);await waitFor("!document.getElementById('panel-vendors').hidden");
    if(!await evaluate(`document.querySelector('[data-vendor-id="${vendor.id}"]').closest('details').open`))await click(`#vendor-list details:has([data-vendor-id="${vendor.id}"]) > summary`);
    await click(`[data-vendor-id="${vendor.id}"]`);await waitFor("document.getElementById('vendor-dialog').open");
    await values({'vendor-edit-name':'Fictional readiness supplier','vendor-edit-contact':'Fictional fixture only','vendor-edit-status':status});
    await click('#vendor-edit-save');await waitFor("!document.getElementById('vendor-dialog').open&&!document.getElementById('submit-btn').disabled");await overview();
  }
  // Explicit Save in the original vendor editor is the confirmed update, not an AI write.
  await saveVendor('cancelled');const risk=await report();
  assert.equal(risk.dimensions.find(d=>d.id==='vendors').state,'attention');
  await capture('cancelled-supplier-evidence');
  await saveVendor('booked');let confirmed=await savedEvent(id),after=await report();
  assert.notEqual(after.dimensions.find(d=>d.id==='vendors').state,'attention');
  assert.equal(after.revision,confirmed.revision);assert(confirmed.revision>before.revision);
  assert.equal(after.dimensions.find(d=>d.id==='resilience').checks.find(c=>c.id==='resilience_coverage').status,'unknown');
  // A missing fictional cost is repaired only through the original scenario approval path.
  const cost=confirmed.expenses.find(item=>item.category_key==='cake'&&!item.cancelled&&item.paid_amount==='0.00'&&item.committed_amount===null);
  assert(cost,'Fictional uncommitted cake estimate is required for this demonstration');
  await evaluate(`location.hash='#/event/${id}/budget';window.confirm=()=>true`);await waitFor("!document.getElementById('panel-budget').hidden");
  await click(`[data-expense-id="${cost.id}"] button:last-child`);await waitFor("document.getElementById('budget-status').textContent==='Expense deleted and totals reconciled.'&&!document.getElementById('submit-btn').disabled");
  await overview();const incomplete=await report();
  assert.equal(incomplete.dimensions.find(d=>d.id==='budget').checks.find(c=>c.id==='budget_prices').status,'unknown');
  const unpriced=await savedEvent(id);
  await evaluate(`location.hash='#/event/${id}/scenarios'`);await waitFor("!document.getElementById('panel-scenarios').hidden");
  await values({'scenario-type':'additional_function','scenario-function-name':'Fictional reconfirmed cake service','scenario-function-category':'cake','scenario-function-cost':cost.estimate});
  await click('#scenario-create');await waitFor("document.getElementById('scenario-status').textContent==='Preview saved. Original event unchanged.'&&!document.getElementById('scenario-create').disabled");
  assert.deepEqual(await savedEvent(id),unpriced);assert(await evaluate("document.getElementById('scenario-apply').disabled"));
  await click('#scenario-approval');await click('#scenario-apply');await waitFor("document.getElementById('scenario-status').textContent==='Scenario applied and saved.'&&!document.getElementById('scenario-create').disabled");
  await overview();confirmed=await savedEvent(id);after=await report();
  assert.equal(after.dimensions.find(d=>d.id==='budget').checks.find(c=>c.id==='budget_prices').status,'pass');
  assert(after.passed>incomplete.passed);assert.notEqual(after.state,'recorded_checks_clear');await capture('approved-cost-evidence');
  for(const width of [768,390,320]){await viewport(width);await capture(`overview-${width}`);assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));}
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.readiness-emblem')).animationName"),'none');
  await restart();await overview();assert.deepEqual(await savedEvent(id),confirmed);assert.deepEqual(await report(),after);
  await evaluate("document.getElementById('readiness-refresh').focus()");
  assert.equal(await evaluate('document.activeElement.id'),'readiness-refresh');
  for(const event of others)assert.deepEqual(await savedEvent(event.id),event);
  console.log('PASS saved readiness evidence, top-three links and native keyboard disclosure/navigation, offline failure/retry, AI fallback and read-only analysis');
  console.log('PASS confirmed vendor update and original explicitly approved scenario improve readiness evidence, no full-ready claim, 1440/768/390/320 responsive/reduced motion, browser/server restart, other-event isolation; .artifacts/readiness');
}
