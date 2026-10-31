import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';

export async function checkWebsites({evaluate,send,waitFor,click,viewport,values,restart,savedEvent}){
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await viewport(1440,960);await evaluate('window.confirm=()=>true');
  const origin=await evaluate('location.origin');
  const event=await evaluate(`(async()=>{await fetch('/api/events');const d=new Date();d.setDate(d.getDate()+60);return(await fetch('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({details:{event_type:'wedding',event_date:d.toISOString().slice(0,10),guest_count:40,budget:150000,currency:'INR',title:'Mira & Arun',city:'Pune',notes:'PRIVATE_NOTES_SENTINEL'}})})).json()})()`);
  const id=event.id,endpoint=`/api/events/${id}/website`;assert(id);
  async function open(){await evaluate(`location.hash='#/event/${id}/website'`);await waitFor("!document.getElementById('panel-website').hidden&&document.getElementById('website-status').textContent.includes('Website version')&&!document.getElementById('website-save').disabled");}
  const metadata=()=>evaluate(`fetch('${endpoint}').then(r=>r.json())`);
  await open();assert.equal(await evaluate("document.getElementById('website-title').value"),'Mira & Arun');
  assert.equal(await evaluate("document.getElementById('website-date').value"),event.details.event_date);
  assert.equal(await evaluate("document.getElementById('website-publish').disabled"),true);
  // Real shared renderer for all themes, CSP observer and no remote content.
  await evaluate("window.__siteCSP=[];document.addEventListener('securitypolicyviolation',e=>window.__siteCSP.push(e.violatedDirective))");
  await send('Network.enable');await send('Network.setBlockedURLs',{urls:['https://*']});
  for(const theme of ['ethereal','modern_minimal','celebration','editorial_luxe']){
    await click(`[data-website-theme="${theme}"]`);await click('#website-preview');
    await waitFor(`document.querySelector('#website-design-preview.event-site')?.dataset.theme==='${theme}'&&!document.getElementById('website-preview').disabled`);
    assert.equal(await evaluate("document.getElementById('website-publish').disabled"),true,'Unsaved preview cannot publish');
  }
  await values({'website-title':'<img src=x onerror=alert(1)> Mira & Arun','website-subtitle':'A day for our favourite people','website-hosts':'Mira & Arun','website-venue':'Garden Hall','website-address':'1 Garden Avenue','website-dress':'Garden formal','website-cover':'botanical','website-accent':'#136b59','website-rsvp_enabled':true,'website-max-attendees':'3','website-rsvp_email_required':true,'website-show_hosts':true,'website-show_venue':true,'website-show_schedule':true,'website-show_dress_code':true,'website-show_gallery':true,'website-gallery-botanical':true,'website-gallery-venue':true});
  await click('#website-generate-copy');await waitFor("document.getElementById('website-status').textContent.includes('Built-in invitation copy')&&!document.getElementById('website-save').disabled");
  assert((await evaluate("document.getElementById('website-invitation').value")).includes(event.details.event_date));
  await click('#website-save');await waitFor("document.getElementById('website-status').textContent.includes('Website version 1')&&!document.getElementById('website-save').disabled");
  let state=await metadata();const path=state.public_path,publicAPI=`/api/public/websites/${path.split('/').at(-1)}`;assert(path);
  assert.equal(await evaluate(`fetch('${publicAPI}').then(r=>r.status)`),404);
  await click('#website-preview');await waitFor("document.getElementById('website-status').textContent.startsWith('Preview ready')&&!document.getElementById('website-preview').disabled");
  assert.equal(await evaluate("document.querySelector('#website-design-preview img[src=x]')!==null"),false);
  assert.equal(await evaluate("document.querySelector('#website-design-preview fieldset').disabled"),true);
  assert.equal(await evaluate("getComputedStyle(document.getElementById('website-design-preview')).getPropertyValue('--invite-accent').trim()"),'#136b59');
  assert.deepEqual(await evaluate('window.__siteCSP'),[]);
  await click('#website-publication-approval');await click('#website-publish');await waitFor("document.getElementById('website-status').textContent.startsWith('Invitation published')&&!document.getElementById('website-save').disabled");
  const snapshot=await evaluate(`fetch('${publicAPI}').then(r=>r.json())`);assert(snapshot.venue.name==='Garden Hall');
  assert.equal(JSON.stringify(snapshot).includes(id),false);assert.equal(JSON.stringify(snapshot).includes('PRIVATE_NOTES_SENTINEL'),false);
  // Draft edits are persisted separately and cannot change a live snapshot.
  await values({'website-title':'Mira & Arun — revised invitation'});await click('#website-save');await waitFor("document.getElementById('website-status').textContent.includes('Website version 3')&&!document.getElementById('website-save').disabled");
  assert.deepEqual(await evaluate(`fetch('${publicAPI}').then(r=>r.json())`),snapshot);
  await click('#website-preview');await waitFor("document.getElementById('website-status').textContent.startsWith('Preview ready')&&!document.getElementById('website-preview').disabled");await click('#website-publication-approval');await click('#website-publish');await waitFor("document.getElementById('website-status').textContent.startsWith('Invitation published')&&!document.getElementById('website-save').disabled");
  state=await metadata();assert.equal(state.public_path,path);assert.equal(state.published.title,'Mira & Arun — revised invitation');
  const beforeRSVP=await savedEvent(id);
  const cookies=(await send('Network.getCookies',{urls:[origin]})).cookies;
  await send('Network.clearBrowserCookies');
  await send('Page.navigate',{url:origin+path});await waitFor("document.querySelector('#public-event h1')?.textContent==='Mira & Arun — revised invitation'");
  assert.equal((await send('Network.getCookies',{urls:[origin]})).cookies.length,0,'Public view creates no ownership cookie');
  assert.equal(await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.status)`),404);
  assert.equal(await evaluate("document.querySelector('#public-event h1 img')!==null"),false);
  await values({'invite-name':'Public Guest','invite-email':'public@example.org','invite-response':'confirmed','invite-attendees':'3','invite-dietary':'Vegetarian','invite-message':'See you soon'});
  await click('#invite-rsvp-form button');await waitFor("document.getElementById('invite-response-status').textContent.includes('Thank you')");
  assert.equal(await evaluate("document.querySelector('#invite-rsvp-form fieldset').disabled"),true);
  mkdirSync('.artifacts/event-websites',{recursive:true});
  for(const width of [1440,768,390,320]){await viewport(width,960);await evaluate("scrollTo({top:0,behavior:'instant'})");assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),`Public overflow at ${width}`);if(width===1440||width===390){const image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});writeFileSync(`.artifacts/event-websites/public-${width}.png`,Buffer.from(image.data,'base64'));}}
  await send('Emulation.setEmulatedMedia',{media:'print'});assert.equal(await evaluate("getComputedStyle(document.getElementById('invite-rsvp-form')).display"),'none');assert.equal(await evaluate("getComputedStyle(document.querySelector('.invite-utilities')).display"),'none');await send('Emulation.setEmulatedMedia',{media:'screen',features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  // Restore the original owner only inside this isolated browser profile.
  await send('Network.clearBrowserCookies');for(const c of cookies)await send('Network.setCookie',{name:c.name,value:c.value,url:origin,path:c.path,httpOnly:c.httpOnly,secure:c.secure,sameSite:c.sameSite,...(!c.session?{expires:c.expires}:{})});
  const revocation=await evaluate(`(async()=>{const s=await(await fetch('${endpoint}')).json();const r=await fetch('${endpoint}/unpublish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:s.revision,event_revision:s.event_revision,request_id:crypto.randomUUID(),approved:true})});return r.status})()`);assert.equal(revocation,200);
  await evaluate("document.dispatchEvent(new Event('visibilitychange'))");await waitFor("document.getElementById('public-event').children.length===0&&document.getElementById('invitation-error').textContent.includes('not currently available')");
  assert.equal(await evaluate("document.getElementById('invitation-print').hidden"),true);
  // Restore the approved invitation for the remaining owner/restart workflows.
  assert.equal(await evaluate(`(async()=>{const s=await(await fetch('${endpoint}')).json();const p=await(await fetch('${endpoint}/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:s.revision,event_revision:s.event_revision,request_id:crypto.randomUUID(),config:s.draft})})).json();return(await fetch('${endpoint}/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:s.revision,event_revision:s.event_revision,request_id:crypto.randomUUID(),approved:true,preview_hash:p.preview_hash})})).status})()`),200);
  await send('Page.navigate',{url:origin+`/#/event/${id}/guests`});await waitFor("document.getElementById('guest-manager-status')?.textContent.includes('guest records')&&!document.getElementById('guest-save').disabled");
  assert.equal(await evaluate("document.querySelector('[data-guest-stat=confirmed]').textContent"),'3');
  const roster=await evaluate(`fetch('/api/events/${id}/guests').then(r=>r.json())`);assert.equal(roster.guests.length,1);assert(roster.guests[0].notes.includes('unverified'));
  const afterRSVP=await savedEvent(id);for(const key of ['details','plan','expenses','budget_summary','vendors','tasks'])assert.deepEqual(afterRSVP[key],beforeRSVP[key]);
  await open();await evaluate('window.confirm=()=>true');
  await values({'website-description':'Keep this failed edit'});await send('Network.setBlockedURLs',{urls:[`*${endpoint}`]});await click('#website-save');await waitFor("!document.getElementById('website-error').hidden&&!document.getElementById('website-save').disabled");assert.equal(await evaluate("document.getElementById('website-description').value"),'Keep this failed edit');await send('Network.setBlockedURLs',{urls:[]});await click('#website-reopen');await waitFor("document.getElementById('website-description').value!=='Keep this failed edit'&&!document.getElementById('website-save').disabled");
  await click('#website-unpublish');await waitFor("document.getElementById('website-status').textContent.startsWith('Invitation unpublished')&&!document.getElementById('website-save').disabled");assert.equal(await evaluate(`fetch('${publicAPI}').then(r=>r.status)`),404);assert.equal(await evaluate(`fetch('${path}').then(r=>r.status)`),404);
  await click('#website-save');await waitFor("document.getElementById('website-status').textContent.includes('Website version')&&!document.getElementById('website-save').disabled");await click('#website-preview');await waitFor("document.getElementById('website-status').textContent.startsWith('Preview ready')&&!document.getElementById('website-preview').disabled");await click('#website-publication-approval');await click('#website-publish');await waitFor("document.getElementById('website-status').textContent.startsWith('Invitation published')&&!document.getElementById('website-save').disabled");
  const final=await metadata(),ledger=await savedEvent(id);assert.equal(final.public_path,path);
  for(const width of [1440,768,390,320]){await viewport(width,960);assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),`Editor overflow at ${width}`);}
  await restart();await open();assert.deepEqual(await metadata(),final);assert.deepEqual(await savedEvent(id),ledger);
  await values({'website-description':'Unsaved private invitation text'});await evaluate('window.confirm=()=>true');await click('#mobile-menu');await click('#new-event-btn');await waitFor("!document.getElementById('creation-view').hidden");assert.equal(await evaluate("document.getElementById('website-description').value"),'');
  await send('Network.setBlockedURLs',{urls:[]});
  console.log('PASS invitation four-theme preview/CSP, offline copy, explicit publication, isolated draft/update/unpublish/republish, anonymous public RSVP → existing Guest Manager, private-data/budget isolation, print CSS, widths 320–1440 and browser/server restart');
}
