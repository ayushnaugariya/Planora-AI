import assert from 'node:assert/strict';

export async function checkAuditNavigation({evaluate,send,waitFor,click,viewport}){
  await viewport(1440,960);await evaluate("location.hash='#/';scrollTo({top:0,behavior:'instant'})");
  await waitFor("!document.getElementById('landing-view').hidden");
  await evaluate("document.querySelector('.site-links a').focus()");
  const focused=await evaluate("document.activeElement.outerHTML");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
  assert.equal(await evaluate("document.activeElement.outerHTML"),focused,'Escape with no open menu must preserve focus');
  await viewport(390,844);await click('.public-menu-toggle');
  assert.equal(await evaluate("document.querySelector('.public-menu-toggle').getAttribute('aria-expanded')"),'true');
  await evaluate("document.querySelector('.site-links a').focus()");
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
  assert.equal(await evaluate("document.querySelector('.public-menu-toggle').getAttribute('aria-expanded')"),'false','Escape closes public navigation');
  assert.equal(await evaluate("document.activeElement.classList.contains('public-menu-toggle')"),true);
  const eventId=await evaluate("fetch('/api/events').then(r=>r.json()).then(rows=>rows[0]?.id)");
  if(eventId){
    await evaluate(`location.hash='#/event/${eventId}/overview'`);
    await waitFor("!document.getElementById('panel-overview').hidden&&!document.getElementById('readiness-refresh').disabled");
    await evaluate("document.getElementById('readiness-refresh').focus()");
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});
    assert.equal(await evaluate("document.activeElement.id"),'readiness-refresh','Closed sidebar must not steal studio focus');
  }
  console.log('PASS Escape preserves unrelated focus and closes mobile public navigation with focus restoration');
}


export async function checkAuditDocs({evaluate,send,waitFor,click,viewport}){
  await viewport(1440,960);
  const origin=await evaluate('location.origin');await send('Page.enable');
  const init=await send('Page.addScriptToEvaluateOnNewDocument',{source:"window.__docsCSP=[];document.addEventListener('securitypolicyviolation',e=>window.__docsCSP.push(e.violatedDirective))"});
  await send('Network.enable');await send('Network.setBlockedURLs',{urls:['https://*']});
  try{
    await send('Page.navigate',{url:origin+'/api/docs'});
    await waitFor("Boolean(window.ui)&&document.querySelectorAll('.swagger-ui .opblock').length>10");
    assert.deepEqual(await evaluate('window.__docsCSP'),[],'Docs must work without CSP violations');
    assert(await evaluate("performance.getEntriesByType('resource').every(r=>new URL(r.name).origin===location.origin)"),'No external docs resources');
    await click('.swagger-ui .opblock-get .opblock-summary');
    assert(await evaluate("Boolean(document.querySelector('.swagger-ui .opblock.is-open .opblock-body'))"));
    assert.equal(await evaluate('window.ui.getConfigs().validatorUrl'),null,'Private schemas must not go to an external validator');
    console.log('PASS self-hosted Swagger renders and expands real API operations with HTTPS/CDNs blocked and zero CSP violations');
  }finally{
    await send('Network.setBlockedURLs',{urls:[]});await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:init.identifier});
  }
}
