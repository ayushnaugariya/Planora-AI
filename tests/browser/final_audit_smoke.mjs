import assert from 'node:assert/strict';

async function newEvent(evaluate,title){return evaluate(`(async()=>{await fetch('/api/events');const d=new Date();d.setDate(d.getDate()+60);const r=await fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({details:{event_type:'birthday',event_date:d.toISOString().slice(0,10),guest_count:30,budget:60000,currency:'INR',title:${JSON.stringify(title)}}})});if(!r.ok)throw Error('Create failed');return r.json()})()`);}

export async function checkLegacyCompletion({evaluate,send,waitFor,click,viewport,values,savedEvent}){
  await viewport(1440,960);await evaluate('window.confirm=()=>true');
  const event=await newEvent(evaluate,'Final audit: shared checklist');const id=event.id;
  const milestone=event.tasks.find(t=>event.plan.timeline[t.milestone_index].category==='event');assert(milestone);
  await evaluate(`location.hash='#/event/${id}/command'`);await waitFor("document.getElementById('day-status').textContent.startsWith('Saved revision')&&!document.getElementById('day-task-save').disabled");
  await click(`[data-day-task="${milestone.id}"]`);await values({'day-task-status':'completed'});await click('#day-task-approval');await click('#day-task-save');
  await waitFor("document.querySelector('[data-day-stat=completed]')?.textContent==='1'&&!document.getElementById('day-task-save').disabled");
  const before=await savedEvent(id);
  await evaluate(`location.hash='#/event/${id}/timeline'`);await waitFor("!document.getElementById('panel-timeline').hidden");await click('#timeline-list input');
  await waitFor("document.getElementById('workspace-status').textContent==='Checklist saved.'&&!document.getElementById('submit-btn').disabled");
  let saved=await savedEvent(id);assert(saved.tasks.find(t=>t.id===milestone.id).completed);
  await evaluate(`location.hash='#/event/${id}/vendors'`);await waitFor("!document.getElementById('panel-vendors').hidden");await click('#vendor-list .checks input');
  await waitFor("document.getElementById('workspace-status').textContent==='Checklist saved.'&&!document.getElementById('submit-btn').disabled");
  saved=await savedEvent(id);assert(saved.tasks.find(t=>t.id===milestone.id).completed);assert.deepEqual(saved.budget_summary,before.budget_summary);
  console.log('PASS Command Center event completion survives real legacy timeline and vendor checklist saves without changing budgets');
}

export async function checkPublicTimeouts({evaluate,send,waitFor,click,viewport,values,savedEvent}){
  await viewport(1440,960);
  const event=await newEvent(evaluate,'Final audit: public timeout');const id=event.id;
  const state=await evaluate(`(async()=>{const ep='/api/events/${id}/website';const s=await(await fetch(ep)).json();const saved=await(await fetch(ep,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_revision:s.event_revision,revision:s.revision,request_id:crypto.randomUUID(),config:{...s.draft,rsvp_enabled:true}})})).json();const preview=await(await fetch(ep+'/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_revision:saved.event_revision,revision:saved.revision,request_id:crypto.randomUUID(),config:saved.draft})})).json();return(await fetch(ep+'/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_revision:saved.event_revision,revision:saved.revision,request_id:crypto.randomUUID(),approved:true,preview_hash:preview.preview_hash})})).json()})()`);
  const publicAPI='/api/public/websites/'+state.public_path.split('/').at(-1),origin=await evaluate('location.origin');
  await send('Page.enable');
  // Only the existing 45-second transport timer is accelerated in this isolated test document.
  const init=await send('Page.addScriptToEvaluateOnNewDocument',{source:"(()=>{const timer=window.setTimeout;window.setTimeout=(fn,ms,...args)=>timer(fn,ms===45000?1000:ms,...args);const fetcher=window.fetch;window.__responseAttempts=[];window.fetch=(url,options)=>{if(String(url).endsWith('/rsvp'))window.__responseAttempts.push(JSON.parse(options.body));return fetcher(url,options);};})()"});
  await send('Fetch.enable',{patterns:[{urlPattern:`*${publicAPI}`,requestStage:'Request'}]});
  try{
    await send('Page.navigate',{url:origin+state.public_path});
    await waitFor("!document.getElementById('invitation-error').hidden&&!document.getElementById('invitation-retry').hidden");
    assert((await evaluate("document.getElementById('invitation-error').textContent")).toLowerCase().includes('timed out'));
    await send('Fetch.disable');await click('#invitation-retry');await waitFor("Boolean(document.getElementById('invite-rsvp-form'))");
    await values({'invite-name':'Timeout guest','invite-email':'timeout@example.org','invite-message':'Retain these details'});
    await send('Fetch.enable',{patterns:[{urlPattern:`*${publicAPI}/rsvp`,requestStage:'Request'}]});await click('#invite-rsvp-form button');
    await waitFor("!document.getElementById('invite-response-error').hidden&&!document.querySelector('#invite-rsvp-form fieldset').disabled");
    assert.equal(await evaluate("document.getElementById('invite-name').value"),'Timeout guest');
    assert.equal(await evaluate("document.getElementById('invite-message').value"),'Retain these details');
    assert.equal(await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json()).then(r=>r.guests.length)`),0);
    await send('Fetch.disable');await click('#invite-rsvp-form button');await waitFor("document.getElementById('invite-response-status').textContent.includes('Thank you')");
    const attempts=await evaluate('window.__responseAttempts');assert.equal(attempts.length,2);assert.deepEqual(attempts[0],attempts[1],'A timeout retry must retain its request UUID and payload');
    assert.equal(await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json()).then(r=>r.guests.length)`),1);
    const saved=await savedEvent(id);assert.deepEqual(saved.budget_summary,event.budget_summary);
  }finally{await send('Fetch.disable');await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:init.identifier});}
  await send('Page.navigate',{url:origin+`/#/event/${id}/overview`});await waitFor("!document.getElementById('panel-overview').hidden&&!document.getElementById('submit-btn').disabled");
  console.log('PASS stalled public GET/RSVP requests abort, expose retry controls, retain inputs/request UUID and save once without budget mutation');
}
