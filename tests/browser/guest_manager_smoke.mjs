import assert from 'node:assert/strict';

export async function checkGuests({evaluate,send,waitFor,click,viewport,values,restart,savedEvent}){
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  const event=await evaluate(`(async()=>{await fetch('/api/events');const d=new Date();d.setDate(d.getDate()+90);return(await fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({details:{event_type:'birthday',event_date:d.toISOString().slice(0,10),guest_count:30,budget:60000,currency:'INR',title:'Guest browser check'}})})).json()})()`);
  const id=event.id;assert(id);
  async function open(){await evaluate(`location.hash='#/event/${id}/guests'`);await waitFor("!document.getElementById('panel-guests').hidden&&document.getElementById('guest-manager-status').textContent.includes('guest records')&&!document.getElementById('guest-save').disabled");}
  await viewport(1440,960);await open();
  await values({'guest-name':'<img src=x onerror=alert(1)> Asha','guest-email':'asha@example.org','guest-group':'Family','guest-rsvp':'confirmed','guest-plus':'2','guest-dietary':'Vegan','guest-accessibility':'Step-free route','guest-notes':'Private note'});
  await click('#guest-save');await waitFor("document.querySelector('[data-guest-stat=confirmed]')?.textContent==='3'&&!document.getElementById('guest-save').disabled");
  assert.equal(await evaluate("document.querySelector('#guest-roster img')!==null"),false);
  const first=await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json())`);
  assert.equal(first.guests[0].notes,'Private note');assert.equal(first.stats.expected_attendees,3);
  const beforePreview=await savedEvent(id);await click('#guest-preview-headcount');await waitFor("!document.getElementById('panel-scenarios').hidden&&document.getElementById('scenario-guests').value==='3'");
  assert.deepEqual(await savedEvent(id),beforePreview);
  assert.equal((await savedEvent(id)).details.guest_count,30,'Reviewing confirmed attendance cannot apply it');
  await evaluate('window.confirm=()=>true');await click('#scenario-form > button.ghost');await open();
  await values({'guest-name':'Emi','guest-email':'emi@example.org','guest-rsvp':'pending','guest-plus':'1'});await click('#guest-save');
  await waitFor("document.querySelector('[data-guest-stat=total_invited]')?.textContent==='5'&&!document.getElementById('guest-save').disabled");
  await values({'guest-search':'ASHA@EXAMPLE'});assert.equal(await evaluate("document.querySelectorAll('[data-guest-id]').length"),1);
  await values({'guest-search':'','guest-filter':'pending'});assert.equal(await evaluate("document.querySelectorAll('[data-guest-id]').length"),1);
  await values({'guest-filter':'','guest-group-filter':'Family'});assert.equal(await evaluate("document.querySelectorAll('[data-guest-id]').length"),1);
  await values({'guest-group-filter':''});await click(`[data-guest-edit="${first.guests[0].id}"]`);await values({'guest-rsvp':'declined','guest-plus':'0'});await click('#guest-save');
  await waitFor("document.querySelector('[data-guest-stat=confirmed]')?.textContent==='0'&&!document.getElementById('guest-save').disabled");
  assert.equal(await evaluate(`fetch('/api/events/${id}').then(r=>r.json()).then(e=>e.details.guest_count)`),30);
  // A real failed server request retains the draft.
  await values({'guest-name':'Retained draft'});await evaluate("document.getElementById('guest-editor').addEventListener('submit',()=>{}, {once:true})");
  await send('Network.enable');await send('Network.setBlockedURLs',{urls:[`*/api/events/${id}/guests`]});
  await click('#guest-save');await waitFor("!document.getElementById('guest-manager-error').hidden&&!document.getElementById('guest-save').disabled");
  assert.equal(await evaluate("document.getElementById('guest-name').value"),'Retained draft');await send('Network.setBlockedURLs',{urls:[]});await evaluate('window.confirm=()=>true');await click('#guest-cancel');
  // Native confirmation is overridden only for this explicit automated deletion.
  await evaluate('window.confirm=()=>false');await click(`[data-guest-remove="${first.guests[0].id}"]`);assert.equal(await evaluate("document.querySelectorAll('[data-guest-id]').length"),2);
  await evaluate('window.confirm=()=>true');await click(`[data-guest-remove="${first.guests[0].id}"]`);
  await waitFor("document.querySelector('[data-guest-stat=total_invited]')?.textContent==='2'&&!document.getElementById('guest-save').disabled");
  const before=await savedEvent(id),roster=await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json())`);
  for(const width of [768,390,320]){await viewport(width,960);await evaluate("document.getElementById('guest-manager').scrollIntoView({block:'start',behavior:'instant'})");assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'));}
  await restart();await open();assert.deepEqual(await savedEvent(id),before);assert.deepEqual(await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json())`),roster);
  await values({'guest-name':'Unsaved guest draft'});await evaluate('window.confirm=()=>true');
  await click('#mobile-menu');await click('#new-event-btn');await waitFor("!document.getElementById('creation-view').hidden");
  assert.equal(await evaluate("document.getElementById('guest-name').value"),'','Confirmed new-event discard clears private draft inputs');
  assert.deepEqual(await savedEvent(id),before);
  console.log('PASS private guest add/edit/RSVP/search/group/filter/confirmed totals, text-safe rendering, failed-input retention, confirmed removal, three widths and browser/server restart');
}
