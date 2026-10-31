import assert from 'node:assert/strict';

export async function checkNegotiation({evaluate,send,waitFor,click,viewport,values,restart,savedEvent}){
  const setup=await evaluate(`(async()=>{await fetch('/api/events');const date=new Date();date.setDate(date.getDate()+90);let e=await(await fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({details:{event_type:'birthday',title:'Negotiation browser check',event_date:date.toISOString().slice(0,10),guest_count:30,budget:60000,currency:'INR'}})})).json();const v=e.vendors.find(v=>e.plan.vendors[v.group_index].key==='catering');e=await(await fetch('/api/events/'+e.id+'/vendors/'+v.id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:e.revision,name:'Kind Kitchen',contact:'hello@example.org',booking_status:'shortlisted'})})).json();e=await(await fetch('/api/events/'+e.id+'/budget/expenses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:e.revision,request_id:crypto.randomUUID(),expense:{category_key:'catering',description:'Dinner and setup',currency:'INR',quoted_amount:'1000.25',paid_amount:'100',vendor_id:v.id}})})).json();return{event:e,vendor:v.id,expense:e.expenses[0].id}})()`);
  const {event,vendor,expense}=setup,id=event.id;
  const endpoint=`/api/events/${id}/vendors/${vendor}/negotiation`;
  await viewport(1440,960);await evaluate('window.confirm=()=>true');
  async function open(){await evaluate(`location.hash='#/event/${id}/vendors'`);await waitFor("!document.getElementById('panel-vendors').hidden&&document.getElementById('negotiation-vendor').options.length>0&&!document.getElementById('negotiation-generate').disabled");await values({'negotiation-vendor':vendor});}
  await open();assert.equal(await evaluate("document.getElementById('negotiation-quote').value"),'expense:'+expense);
  await values({'negotiation-target':'900.10','negotiation-instruction':'Please preserve dietary options.'});await click('#negotiation-generate');
  await waitFor("document.getElementById('negotiation-message').value.includes('1000.25 INR')&&!document.getElementById('negotiation-save').disabled");
  assert((await evaluate("document.getElementById('negotiation-result').textContent")).includes('100.15'));
  const first=await evaluate("document.getElementById('negotiation-message').value");
  await values({'negotiation-message':first+'\nMy reviewed edit.'});await click('#negotiation-save');await waitFor("document.getElementById('negotiation-status').textContent.includes('saved privately')&&!document.getElementById('negotiation-save').disabled");
  let saved=await evaluate(`fetch('${endpoint}/draft').then(r=>r.json())`);assert(saved.message.endsWith('My reviewed edit.'));assert.equal(saved.draft_revision,1);
  const origin=await evaluate('location.origin');await send('Browser.grantPermissions',{origin,permissions:['clipboardReadWrite','clipboardSanitizedWrite']});
  await click('#negotiation-copy');await waitFor("document.getElementById('negotiation-status').textContent.includes('copied')");assert.equal((await evaluate('navigator.clipboard.readText()')).replace(/\r\n/g,'\n'),saved.message);
  await click('#negotiation-regenerate');await waitFor("document.getElementById('negotiation-message').value!=="+JSON.stringify(saved.message)+"&&!document.getElementById('negotiation-generate').disabled");
  assert.equal((await evaluate(`fetch('${endpoint}/draft').then(r=>r.json())`)).message,saved.message,'Regenerate must not autosave');
  const retained=await evaluate("document.getElementById('negotiation-message').value");
  await send('Network.enable');await send('Network.setBlockedURLs',{urls:['*'+endpoint]});await click('#negotiation-regenerate');
  await waitFor("!document.getElementById('negotiation-error').hidden&&!document.getElementById('negotiation-generate').disabled");
  assert.equal(await evaluate("document.getElementById('negotiation-message').value"),retained);await send('Network.setBlockedURLs',{urls:[]});await click('#negotiation-clear');
  // Reuse two real analyzer results without retyping their prices in negotiation.
  await values({'analyzer-category':'catering','analyzer-vendor':vendor});
  const source=price=>`Vendor: ${price===1100?'Kind Kitchen':'Other supplied offer'}\nCurrency: INR\nItem: Dinner service | 1 | ${price}\nTax: 0\nFee: 0\nAll-in total: ${price}\nInclusions: Dinner and setup\nCancellation: Confirm in writing\nOvertime: Not included`;
  await values({'analyzer-text':source(1100)});await click('#analyzer-analyze');await waitFor("document.querySelectorAll('[data-negotiate-source]').length===1&&!document.getElementById('analyzer-analyze').disabled");
  await values({'analyzer-text':source(950)});await click('#analyzer-analyze');await waitFor("document.querySelectorAll('[data-negotiate-source]').length===2&&!document.getElementById('analyzer-analyze').disabled");
  await click('[data-negotiate-source]');assert((await evaluate("document.getElementById('negotiation-source-context').textContent")).includes('1 other supplied'));
  await values({'negotiation-scenario':'compare_offers','negotiation-target':'900'});await click('#negotiation-generate');
  await waitFor("document.getElementById('negotiation-message').value.includes('1100.00 INR')&&!document.getElementById('negotiation-save').disabled");
  assert((await evaluate("document.getElementById('negotiation-result').textContent")).includes('950.00 INR'));
  assert.deepEqual(await savedEvent(id),event,'Messages and analyzed offers cannot change expenses or event data');
  await values({'negotiation-message':(await evaluate("document.getElementById('negotiation-message').value"))+'\nReviewed comparison.'});await click('#negotiation-save');
  await waitFor("document.getElementById('negotiation-status').textContent.includes('saved privately')&&!document.getElementById('negotiation-save').disabled");
  saved=await evaluate(`fetch('${endpoint}/draft').then(r=>r.json())`);assert.equal(saved.draft_revision,2);
  for(const width of [768,390,320]){await viewport(width,960);await evaluate("document.getElementById('negotiation-assistant').scrollIntoView({block:'start',behavior:'instant'})");assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));}
  await restart();await open();await waitFor("!document.getElementById('negotiation-load').disabled");await click('#negotiation-load');
  assert.equal(await evaluate("document.getElementById('negotiation-message').value"),saved.message);assert.deepEqual(await savedEvent(id),event);
  // Simulate another tab saving, then refresh metadata while local edits are unsaved.
  const external=await evaluate(`fetch('${endpoint}/draft',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:${event.revision},draft_revision:${saved.draft_revision},approved:true,scenario:'compare_offers',message:'Other tab revised this draft'})}).then(r=>r.json())`);
  await values({'negotiation-message':'My retained unsaved text'});await evaluate("document.dispatchEvent(new CustomEvent('planora:view',{detail:'vendors'}))");
  await waitFor("document.getElementById('negotiation-status').textContent.includes('Another edit was saved')");
  await click('#negotiation-save');await waitFor("!document.getElementById('negotiation-error').hidden&&!document.getElementById('negotiation-save').disabled");
  assert.equal(await evaluate("document.getElementById('negotiation-message').value"),'My retained unsaved text');
  assert.equal((await evaluate(`fetch('${endpoint}/draft').then(r=>r.json())`)).message,external.message);
  await evaluate('window.confirm=()=>true');await click('#negotiation-load');assert.equal(await evaluate("document.getElementById('negotiation-message').value"),external.message);
  console.log('PASS quote-grounded negotiation generate/edit/regenerate/copy/explicit save, real analyzer comparison handoff, failed-input retention, unchanged ledger, responsive layout and browser/server restart');
}
