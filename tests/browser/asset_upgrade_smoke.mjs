// Real HTTP-cache upgrade regression plus a read-only check of the running site.
// node tests/browser/asset_upgrade_smoke.mjs http://127.0.0.1:8000
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';

const upstream=process.argv[2]||'http://127.0.0.1:8000';
const html=await(await fetch(upstream)).text();
assert(html.includes('id="scroll-journey"'));
const legacy=html.replace(/(\/static\/(?:app\.js|style\.css))\?v=[^"']+/g,'$1').replace('class="scroll-journey" hidden','class="scroll-journey"');
const root=mkdtempSync(path.join(os.tmpdir(),'planora-cache-smoke-'));
const artifacts=path.resolve('.artifacts/asset-upgrade');mkdirSync(artifacts,{recursive:true});
let oldRequests=0;
const proxy=http.createServer(async(req,res)=>{
  try{
    if(req.url==='/seed'){res.setHeader('Content-Type','text/html');res.end('<link rel="stylesheet" href="/static/style.css"><script type="module" src="/static/app.js"></script>');return;}
    if(req.url==='/legacy'){res.setHeader('Content-Type','text/html');res.end(legacy);return;}
    if(req.url==='/static/style.css'||req.url==='/static/app.js'){
      oldRequests++;const js=req.url.endsWith('.js');
      res.setHeader('Content-Type',js?'text/javascript':'text/css');res.setHeader('Cache-Control','public, max-age=86400');
      res.end(js?'window.__legacyEntry=true;':'body{background:#fbf8f2;color:#243149}');return;
    }
    assert.equal(req.method,'GET','Verification must not mutate application state');
    const response=await fetch(upstream+req.url,{headers:req.headers.cookie?{cookie:req.headers.cookie}:{}});
    res.statusCode=response.status;for(const [name,value] of response.headers)if(!['content-encoding','content-length','transfer-encoding'].includes(name))res.setHeader(name,value);
    res.end(Buffer.from(await response.arrayBuffer()));
  }catch(error){res.statusCode=500;res.end(String(error));}
});
await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));const origin=`http://127.0.0.1:${proxy.address().port}`;
const debug=http.createServer();await new Promise(resolve=>debug.listen(0,'127.0.0.1',resolve));const debugPort=debug.address().port;await new Promise(resolve=>debug.close(resolve));
const browser=spawn(process.env.EVENTRA_BROWSER_BINARY||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--disable-gpu','--disable-extensions','--no-first-run','--no-default-browser-check',`--remote-debugging-port=${debugPort}`,`--user-data-dir=${root}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));let ws,id=0;const pending=new Map();
function send(method,params={}){return new Promise((resolve,reject)=>{const key=++id,timer=setTimeout(()=>{pending.delete(key);reject(Error(`CDP timeout ${method}`));},10000);pending.set(key,{resolve:v=>{clearTimeout(timer);resolve(v);},reject});ws.send(JSON.stringify({id:key,method,params}));});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;}
async function waitFor(expression){for(let i=0;i<100;i++){if(await evaluate(expression))return;await sleep(100);}throw Error(`Timed out: ${expression}`);}
async function navigate(url){const old=await evaluate('performance.timeOrigin');await send('Page.navigate',{url});await waitFor(`performance.timeOrigin!==${old}`);}
async function capture(name){await sleep(700);const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(path.join(artifacts,name+'.png'),Buffer.from(shot.data,'base64'));}
try{
  let tab;for(let i=0;i<100;i++){try{tab=(await(await fetch(`http://127.0.0.1:${debugPort}/json/list`)).json()).find(t=>t.type==='page');if(tab)break;}catch{}await sleep(100);}
  assert(tab,'Owned test browser did not start');ws=new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const errors=[];ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const request=pending.get(message.id);pending.delete(message.id);if(message.error)request?.reject(message.error);else request?.resolve(message.result);}else if(message.method==='Runtime.exceptionThrown')errors.push(message.params);};
  await send('Runtime.enable');await send('Page.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});
  await navigate(origin+'/seed');await waitFor('window.__legacyEntry===true');assert.equal(oldRequests,2);
  await navigate(origin+'/legacy');await waitFor('window.__legacyEntry===true');
  assert.equal(oldRequests,2,'Old root assets must actually come from the HTTP cache');
  assert.notEqual(await evaluate("getComputedStyle(document.getElementById('scroll-journey')).backgroundColor"),'rgb(23, 35, 44)');
  assert.equal(await evaluate("document.getElementById('scroll-journey').dataset.enhanced"),undefined);
  await capture('reproduced-stale-assets');
  await navigate(origin+'/');await waitFor("document.getElementById('scroll-journey')?.dataset.enhanced==='true'");
  assert.equal(await evaluate("getComputedStyle(document.getElementById('scroll-journey')).backgroundColor"),'rgb(23, 35, 44)');
  assert.equal(oldRequests,2,'Versioned entrypoints must escape the cached old roots');
  assert.equal(await evaluate('window.__legacyEntry'),undefined);
  console.log('PASS reproduced warm-cache broken upgrade; versioned roots recover without clearing browser cache');
  await navigate(upstream+'/');await waitFor("document.getElementById('scroll-journey')?.dataset.enhanced==='true'");
  assert.equal(await evaluate("getComputedStyle(document.getElementById('scroll-journey')).backgroundColor"),'rgb(23, 35, 44)');
  const transforms=[];for(const p of [.12,.6]){await evaluate(`(()=>{const r=document.getElementById('scroll-journey').getBoundingClientRect();scrollTo({top:scrollY+r.top+(r.height-innerHeight)*${p},behavior:'instant'})})()`);await sleep(200);transforms.push(await evaluate("getComputedStyle(document.querySelector('.journey-world')).transform"));}
  assert.notEqual(...transforms);assert.equal(await evaluate("getComputedStyle(document.querySelector('.journey-sticky')).position"),'sticky');
  await capture('live-homepage-fixed');assert.deepEqual(errors,[]);
  console.log('PASS actual running homepage: correct computed styling, sticky scene, distinct real scroll transforms, zero runtime errors; no writes');
  await send('Network.setBlockedURLs',{urls:['*/static/styles/scroll-story.css*']});await send('Network.setCacheDisabled',{cacheDisabled:true});
  await navigate(upstream+'/');await waitFor("document.body.dataset.view==='landing-view'");
  assert(await evaluate("document.getElementById('scroll-journey').hidden"));
  assert.equal(await evaluate("getComputedStyle(document.getElementById('scroll-journey')).display"),'none');
  assert(await evaluate("document.querySelector('.hero-actions .primary').getClientRects().length>0"));
  await send('Network.setBlockedURLs',{urls:[]});await send('Network.setCacheDisabled',{cacheDisabled:false});
  await navigate(upstream+'/');await waitFor("document.getElementById('scroll-journey')?.dataset.enhanced==='true'");
  assert.deepEqual(errors,[]);console.log('PASS stylesheet failure keeps the optional story hidden and primary planning link available');
}finally{
  const exited=new Promise(resolve=>{if(browser.exitCode!==null)resolve();else browser.once('exit',resolve);});
  if(ws?.readyState===WebSocket.OPEN){await send('Browser.close').catch(()=>{});ws.close();}
  await Promise.race([exited,sleep(3000)]);
  if(browser.exitCode===null){
    if(process.platform==='win32'){const killer=spawn('taskkill',['/PID',String(browser.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});await new Promise(resolve=>killer.once('close',resolve));}
    else browser.kill();
  }
  await new Promise(resolve=>proxy.close(resolve));
  const relative=path.relative(os.tmpdir(),root);assert(relative.startsWith('planora-cache-smoke-')&&!relative.includes(path.sep));
  for(let attempt=0;attempt<8;attempt++){try{rmSync(root,{recursive:true,force:true});break;}catch{if(attempt===7)console.log('Owned temporary browser profile still locked:',root);else await sleep(500);}}
}
