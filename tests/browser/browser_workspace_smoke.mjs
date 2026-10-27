// Optional real-browser integration test. No npm packages or development data.
// node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe [browser binary]
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, unlinkSync } from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import {runProductSmoke} from './planora_product_smoke.mjs';

const python = process.argv[2] || "python";
const binary = process.argv[3] || process.env.EVENTRA_BROWSER_BINARY || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
assert(existsSync(binary), "Set EVENTRA_BROWSER_BINARY to a Chrome/Edge executable");
const root = mkdtempSync(path.join(os.tmpdir(), "eventra-workspace-smoke-"));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function freePort() {
  const server = net.createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return port;
}
const port = await freePort();
const debugPort = await freePort();
const origin = `http://127.0.0.1:${port}`;
let server, browser, ws;
let serverLog = "";
let browserLog = "";
let nextId = 0;
let pending = new Map();
let runtimeErrors = [];

async function startServer() {
  server = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(port), "--no-proxy-headers"], {
    windowsHide: true, env: { ...process.env, EVENTRA_DB_PATH: path.join(root, "events.sqlite3"),
      GEMINI_API_KEY: "", GOOGLE_API_KEY: "", RATE_LIMIT: "200", RATE_MAX_CLIENTS: "1000",
      TRUST_PROXY: "0", TRUSTED_PROXY_CIDRS: "", K_SERVICE: "" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  server.stdout.on("data", (data) => { serverLog += data; });
  server.stderr.on("data", (data) => { serverLog += data; });
  for (let i = 0; i < 100; i++) {
    try { if ((await fetch(origin + "/healthz", { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* starting */ }
    assert(server.exitCode === null, "Uvicorn exited: " + serverLog);
    await sleep(100);
  }
  throw new Error("Uvicorn startup timeout");
}

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error("CDP timeout: " + method)); }, 5000);
    pending.set(id, { resolve: (value) => { clearTimeout(timer); resolve(value); }, reject: (error) => { clearTimeout(timer); reject(error); } });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  assert(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function waitFor(expression) {
  for (let i = 0; i < 100; i++) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw new Error("Browser wait timed out: " + expression + "\n" + await evaluate(
    "JSON.stringify({status:document.getElementById('workspace-status')?.textContent,error:document.getElementById('workspace-error')?.textContent,form:document.getElementById('form-error')?.textContent})"));
}

async function startBrowser() {
  browserLog = "";
  browser = spawn(binary, ["--headless=new", "--disable-gpu", "--disable-background-mode", "--disable-extensions", "--no-first-run", "--no-default-browser-check",
    `--remote-debugging-port=${debugPort}`, `--user-data-dir=${path.join(root, "profile")}`, "about:blank"],
  { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
  const capture = (chunk) => { browserLog = (browserLog + chunk).slice(-4000); };
  browser.stdout.on("data", capture);
  browser.stderr.on("data", capture);
  let tabs;
  for (let i = 0; i < 100; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`, { signal: AbortSignal.timeout(1000) });
      const candidates = await response.json();
      // Edge can answer HTTP before its initial page target exists, especially
      // after reopening a profile. Wait for the same target required below.
      if (response.ok && Array.isArray(candidates) && candidates.some((tab) => tab.type === "page" && tab.webSocketDebuggerUrl)) {
        tabs = candidates;
        break;
      }
    } catch {}
    await sleep(100);
  }
  assert(tabs?.some((tab) => tab.type === "page"), `Browser debugging did not start (exit ${browser.exitCode})\n${browserLog}`);
  ws = new WebSocket(tabs.find((tab) => tab.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.addEventListener("open", resolve, { once: true }); ws.addEventListener("error", reject, { once: true }); });
  pending = new Map();
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const request = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) request?.reject(message.error); else request?.resolve(message.result);
    } else if (message.method === "Runtime.exceptionThrown") {
      runtimeErrors.push(message.params.exceptionDetails);
    }
  });
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Page.navigate", { url: origin });
  await waitFor("document.getElementById('event_date')?.value && document.getElementById('workspace-status').textContent !== 'Loading saved events…' && !document.getElementById('submit-btn').disabled");
}

async function stop(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  const running = () => {
    try { process.kill(child.pid, 0); return true; }
    catch (error) { if (error.code === "ESRCH") return false; throw error; }
  };
  const exited = new Promise((resolve) => child.once("exit", resolve));
  let details = "";
  if (process.platform === "win32") {
    // The venv executable may be a launcher with a child Python process.
    // Terminate only the process tree this test spawned.
    const killer = spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    killer.stdout.on("data", (chunk) => { details = (details + chunk).slice(-2000); });
    killer.stderr.on("data", (chunk) => { details = (details + chunk).slice(-2000); });
    await new Promise((resolve) => killer.once("close", resolve));
  } else child.kill();
  await Promise.race([exited, sleep(3000)]);
  // taskkill can race graceful exit or fail to terminate the root. Verify the
  // actual owned ChildProcess, and use its native termination handle if needed.
  if (running()) {
    child.kill();
    await Promise.race([exited, sleep(3000)]);
  }
  assert(!running(), `Could not stop owned test process ${child.pid}: ${details}`);
}

async function closeBrowser() {
  const closed = new Promise((resolve) => {
    if (!browser || browser.exitCode !== null || browser.signalCode !== null) resolve();
    else browser.once("close", resolve);
  });
  if (ws?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    ws.close();
  }
  // Allow graceful profile/cookie flush before considering forced termination.
  await Promise.race([closed, sleep(3000)]);
  await stop(browser);
  if (process.platform === "win32") {
    const lock = path.join(root, "profile", "lockfile");
    for (let i = 0; i < 100 && existsSync(lock); i++) {
      // stop() verified the owned browser is gone. Remove only its stale lock;
      // Windows refuses unlink while a remaining process still holds it.
      try { unlinkSync(lock); } catch { await sleep(100); }
    }
    assert(!existsSync(lock), "Test browser did not release its profile lock");
  }
}

const selectedId = () => evaluate("JSON.parse(localStorage.getItem('eventra:selected-event'))");
const savedEvent = (id) => evaluate(`fetch('/api/events/${id}').then(r=>r.json())`);
async function selectEvent(id) {
  await evaluate(`document.getElementById('saved-event-select').value='${id}';document.getElementById('saved-event-select').dispatchEvent(new Event('change'));`);
  await waitFor(`document.getElementById('workspace-status').textContent.startsWith('Opened saved event') && !document.getElementById('submit-btn').disabled`);
}

try {
  await startServer();
  await startBrowser();
  await evaluate(`document.getElementById('title').value='Garden party';document.getElementById('venue_preferences').value='Garden';document.getElementById('accessibility_requirements').value='Step-free';document.getElementById('plan-form').requestSubmit();`);
  await waitFor("document.getElementById('workspace-status').textContent==='Event and plan saved.' && !document.getElementById('submit-btn').disabled");
  const firstId = await selectedId();
  assert(firstId);
  await evaluate("document.getElementById('tab-timeline').click();document.querySelector('#timeline-list input').click();");
  await waitFor("document.getElementById('workspace-status').textContent==='Checklist saved.' && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('tab-timeline').getAttribute('aria-selected')"), "true");
  await evaluate("document.getElementById('tab-vendors').click();document.querySelector('#vendor-list input').click();");
  await waitFor("document.getElementById('workspace-status').textContent==='Checklist saved.' && !document.getElementById('submit-btn').disabled");
  await evaluate("document.getElementById('tab-ask').click();document.getElementById('chat-input').value='Where can I save money?';document.getElementById('chat-form').requestSubmit();");
  await waitFor("document.getElementById('workspace-status').textContent==='Conversation saved.' && !document.getElementById('submit-btn').disabled");
  await evaluate("document.getElementById('title').value='Renamed garden party';document.getElementById('rename-event-btn').click();");
  await waitFor("document.getElementById('workspace-status').textContent==='Event name saved.' && !document.getElementById('submit-btn').disabled");
  const beforeReload = await savedEvent(firstId);
  assert.equal(beforeReload.chat.length, 2);
  assert(beforeReload.tasks.some((task) => task.completed));
  assert(beforeReload.vendors.some((vendor) => vendor.checklist.some((item) => item.completed)));
  await send("Page.reload");
  await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event') && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('plan-title').textContent"), "Renamed garden party");
  assert.equal(await evaluate("document.getElementById('venue_preferences').value"), "Garden");
  assert.equal(await evaluate("document.getElementById('accessibility_requirements').value"), "Step-free");
  assert.equal(await evaluate("document.querySelector('#timeline-list input').checked"), true);
  assert.equal(await evaluate("document.querySelector('#vendor-list input').checked"), true);
  assert.equal(await evaluate("document.querySelectorAll('#chat-log .msg').length"), 3);
  assert.deepEqual(await savedEvent(firstId), beforeReload);
  console.log("PASS create, progress, chat, rename and refresh reopen");

  await evaluate("document.getElementById('new-event-btn').click();document.getElementById('title').value='Other event';document.getElementById('plan-form').requestSubmit();");
  await waitFor("document.getElementById('workspace-status').textContent==='Event and plan saved.' && !document.getElementById('submit-btn').disabled");
  const secondId = await selectedId();
  assert.notEqual(firstId, secondId);
  await selectEvent(firstId);
  await send("Network.setBlockedURLs", { urls: [`${origin}/api/events/${secondId}`] });
  await evaluate(`document.getElementById('saved-event-select').value='${secondId}';document.getElementById('saved-event-select').dispatchEvent(new Event('change'));`);
  await waitFor("!document.getElementById('workspace-error').hidden && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('saved-event-select').value"), firstId);
  assert.equal(await evaluate("document.getElementById('plan-title').textContent"), "Renamed garden party");
  await send("Network.setBlockedURLs", { urls: [] });
  await evaluate("document.getElementById('budget').value='120001';document.getElementById('guest_count').value='67';document.getElementById('plan-form').requestSubmit();");
  await waitFor("document.getElementById('workspace-status').textContent==='Event and plan saved.' && !document.getElementById('submit-btn').disabled");
  const updated = await savedEvent(firstId);
  assert.equal(updated.plan.budget_lines.reduce((total, line) => total + line.amount, 0), 120001);
  assert.deepEqual(updated.tasks.map((task) => task.id), beforeReload.tasks.map((task) => task.id));
  assert(updated.tasks.some((task) => task.completed));
  assert.equal((await savedEvent(secondId)).plan.title, "Other event");

  await send("Network.setBlockedURLs", { urls: [`${origin}/api/events/${firstId}`] });
  await evaluate("document.getElementById('title').value='Unsaved failed change';document.getElementById('plan-form').requestSubmit();");
  await waitFor("!document.getElementById('form-error').hidden && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("document.getElementById('title').value"), "Unsaved failed change");
  assert.equal(await evaluate("document.getElementById('plan-title').textContent"), "Renamed garden party");
  await send("Network.setBlockedURLs", { urls: [] });
  assert.deepEqual(await savedEvent(firstId), updated);
  await evaluate("document.getElementById('title').value='Renamed garden party';");
  await selectEvent(secondId);
  await evaluate("window.confirm=()=>false;document.getElementById('delete-event-btn').click();");
  assert.equal((await savedEvent(secondId)).id, secondId);
  await evaluate("window.confirm=()=>true;document.getElementById('delete-event-btn').click();");
  await waitFor("document.getElementById('workspace-status').textContent==='Event deleted.' && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate(`fetch('/api/events/${secondId}').then(r=>r.status)`), 404);
  await selectEvent(firstId);
  console.log("PASS second-event isolation, rebuild, failed-save recovery and confirmed delete");

  // Leave the application completely, restart the server against the same DB,
  // and reopen with the same durable browser profile/cookie.
  await closeBrowser();
  await stop(server);
  await startServer();
  await startBrowser();
  await waitFor("document.getElementById('workspace-status').textContent.startsWith('Opened saved event') && !document.getElementById('submit-btn').disabled");
  assert.equal(await selectedId(), firstId);
  assert.deepEqual(await savedEvent(firstId), updated);
  assert.equal(await evaluate("document.querySelector('#timeline-list input').checked"), true);
  assert.equal(await evaluate("document.querySelectorAll('#chat-log .msg').length"), 3);
  console.log("PASS original workspace state after browser/server restart");
  await evaluate("document.getElementById('tab-budget').click();document.getElementById('expense-editor').open=true;document.getElementById('expense-description').value='Venue deposit';document.getElementById('expense-category').value='venue';document.getElementById('expense-quantity').value='2';document.getElementById('expense-unit').value='50.25';document.getElementById('expense-quote').value='120';document.getElementById('expense-commitment').value='110';document.getElementById('expense-paid').value='30';document.getElementById('expense-form').requestSubmit();");
  await waitFor("document.getElementById('budget-status').textContent==='Expense saved and totals reconciled.' && !document.getElementById('expense-save').disabled");
  let financial = await savedEvent(firstId);
  const expenseId = financial.expenses[0].id;
  assert.equal(financial.expenses[0].line_total, "100.50");
  assert.equal(financial.budget_summary.projected_cost, "110.00");
  assert((await evaluate("document.getElementById('metric-actual_spending').textContent")).includes("30.00"));
  await evaluate(`document.querySelector('[data-expense-id="${expenseId}"] button').click();document.getElementById('expense-unit').value='60.255';document.getElementById('expense-paid').value='50';document.getElementById('expense-form').requestSubmit();`);
  await waitFor("document.getElementById('budget-status').textContent==='Expense saved and totals reconciled.' && !document.getElementById('expense-save').disabled");
  financial = await savedEvent(firstId);
  assert.equal(financial.expenses[0].id, expenseId);
  assert.equal(financial.expenses[0].line_total, "120.52");
  assert.equal(financial.budget_summary.actual_spending, "50.00");
  assert((await evaluate("document.getElementById('metric-actual_spending').textContent")).includes("50.00"));
  await send("Network.setBlockedURLs", { urls: [`${origin}/api/events/${firstId}/budget/expenses/${expenseId}`] });
  await evaluate(`document.querySelector('[data-expense-id="${expenseId}"] button').click();document.getElementById('expense-notes').value='Keep this failed edit';document.getElementById('expense-form').requestSubmit();`);
  await waitFor("!document.getElementById('budget-error').hidden && !document.getElementById('expense-save').disabled");
  assert.equal(await evaluate("document.getElementById('expense-notes').value"), "Keep this failed edit");
  assert.deepEqual(await savedEvent(firstId), financial);
  await send("Network.setBlockedURLs", { urls: [] });
  await evaluate("document.getElementById('expense-form').requestSubmit();");
  await waitFor("document.getElementById('budget-status').textContent==='Expense saved and totals reconciled.' && !document.getElementById('expense-save').disabled");
  await evaluate("document.getElementById('expense-description').value='Temporary cost';document.getElementById('expense-category').value='venue';document.getElementById('expense-unit').value='5';document.getElementById('expense-form').requestSubmit();");
  await waitFor("document.getElementById('budget-status').textContent==='Expense saved and totals reconciled.' && !document.getElementById('expense-save').disabled");
  const temporaryId = (await savedEvent(firstId)).expenses.find(item=>item.description==='Temporary cost').id;
  await evaluate(`window.confirm=()=>false;document.querySelector('[data-expense-id="${temporaryId}"] button:last-child').click();`);
  assert((await savedEvent(firstId)).expenses.some(item=>item.id===temporaryId));
  await evaluate(`window.confirm=()=>true;document.querySelector('[data-expense-id="${temporaryId}"] button:last-child').click();`);
  await waitFor("document.getElementById('budget-status').textContent==='Expense deleted and totals reconciled.' && !document.getElementById('expense-save').disabled");
  assert(!(await savedEvent(firstId)).expenses.some(item=>item.id===temporaryId));
  const oldVenueAllocation = (await savedEvent(firstId)).plan.budget_lines.find(line=>line.key==='venue').amount;
  await evaluate(`document.getElementById('allocation-category').value='venue';document.getElementById('allocation-category').dispatchEvent(new Event('change'));document.getElementById('allocation-amount').value='${oldVenueAllocation-1}';document.getElementById('allocation-form').requestSubmit();`);
  await waitFor("document.getElementById('budget-status').textContent==='Category allocation saved; other allocations unchanged.' && !document.getElementById('expense-save').disabled");
  assert.equal((await savedEvent(firstId)).budget_summary.unallocated_funds, "1.00");
  assert.equal(await evaluate("document.getElementById('allocation-amount').value"), String(oldVenueAllocation-1));
  // Explicit fixture prices through normal owned APIs, never direct SQLite:
  // every non-reserve category is priced, so a feasible result is defensible.
  await evaluate(`(async()=>{let e=await fetch('/api/events/${firstId}').then(r=>r.json());for(const line of e.plan.budget_lines){if(line.key==='contingency'||e.expenses.some(x=>x.category_key===line.key))continue;const r=await fetch('/api/events/${firstId}/budget/expenses',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:e.revision,request_id:crypto.randomUUID(),expense:{category_key:line.key,description:'Smoke fixture: confirmed '+line.label,currency:e.details.currency,unit_amount:line.key==='catering'?'2':'0',cost_basis:line.key==='catering'?'per_guest':'fixed'}})});if(!r.ok)throw new Error(await r.text());e=await r.json();}return true;})()`);
  await selectEvent(firstId);
  const beforeScenario = await savedEvent(firstId);
  await evaluate("document.getElementById('tab-scenarios').click();document.getElementById('scenario-type').value='budget_reduction';document.getElementById('scenario-type').dispatchEvent(new Event('change'));document.getElementById('scenario-reduction').value='10';document.getElementById('scenario-form').requestSubmit();");
  await waitFor("document.getElementById('scenario-status').textContent==='Preview saved. Original event unchanged.' && !document.getElementById('scenario-create').disabled");
  assert((await evaluate("document.getElementById('scenario-feasibility').textContent")).startsWith("Infeasible"));
  assert.equal(await evaluate("document.getElementById('scenario-apply').disabled"), true);
  assert.deepEqual(await savedEvent(firstId), beforeScenario);
  await evaluate("document.getElementById('scenario-discard').click();");
  await waitFor("document.getElementById('scenario-status').textContent==='Preview discarded. Saved event unchanged.' && !document.getElementById('scenario-create').disabled");
  assert.deepEqual(await savedEvent(firstId), beforeScenario);
  await evaluate("document.getElementById('scenario-question').value='80 guests';document.getElementById('scenario-interpret-form').requestSubmit();");
  await waitFor("document.getElementById('scenario-status').textContent.startsWith('Built-in fallback:') && !document.getElementById('scenario-create').disabled");
  assert.equal(await evaluate("document.getElementById('scenario-type').value"), "guest_count");
  assert.equal(await evaluate("document.getElementById('scenario-guests').value"), "80");
  await evaluate("document.getElementById('scenario-form').requestSubmit();");
  await waitFor("document.getElementById('scenario-status').textContent==='Preview saved. Original event unchanged.' && !document.getElementById('scenario-create').disabled");
  assert((await evaluate("document.getElementById('scenario-feasibility').textContent")).startsWith("Feasible"));
  const guestRow = await evaluate("[...document.querySelectorAll('#scenario-comparison tr')].find(row=>row.firstChild.textContent==='Guests').textContent");
  assert(guestRow.includes("67") && guestRow.includes("80"));
  assert.deepEqual(await savedEvent(firstId), beforeScenario);
  assert.equal(await evaluate("document.getElementById('scenario-apply').disabled"), true);
  await evaluate("document.getElementById('scenario-approval').click();");
  assert.equal(await evaluate("document.getElementById('scenario-apply').disabled"), false);
  assert.deepEqual(await savedEvent(firstId), beforeScenario);
  await evaluate("document.getElementById('scenario-apply').click();");
  await waitFor("document.getElementById('scenario-status').textContent==='Scenario applied and saved.' && !document.getElementById('scenario-create').disabled");
  const afterFinance = await savedEvent(firstId);
  assert.equal(afterFinance.details.guest_count, 80);
  assert.equal(await evaluate("document.getElementById('guest_count').value"), "80");
  assert.equal(afterFinance.budget_summary.actual_spending, "50.00");
  assert.equal(afterFinance.budget_summary.projected_cost, "270.00");
  assert(afterFinance.tasks.some(task=>task.completed));
  console.log("PASS decimal expense add/edit, actual metrics, failed-input retention and priced scenario isolation/rejection/approval");
  await closeBrowser(); await stop(server); await startServer(); await startBrowser();
  await waitFor("document.getElementById('workspace-status').textContent.startsWith('Opened saved event') && !document.getElementById('submit-btn').disabled");
  assert.deepEqual(await savedEvent(firstId), afterFinance);
  assert.equal(await evaluate("document.getElementById('guest_count').value"), "80");
  assert.equal(await evaluate(`fetch('/api/events/${firstId}/scenarios').then(r=>r.json()).then(items=>items.filter(x=>x.status==='applied').length)`), 1);
  console.log("PASS expense/scenario state persists across another browser/server restart");
  // Migration is opt-in and never deletes the original browser-only data.
  const legacy = { ...beforeReload.details, title: "Browser draft" };
  const legacyKey = `birthday|${legacy.event_date}|Browser draft`;
  await evaluate(`localStorage.setItem('eventra:form',${JSON.stringify(JSON.stringify(legacy))});localStorage.setItem('eventra:done:${legacyKey}','[0]');localStorage.setItem('eventra:vendor:${legacyKey}','["venue:0"]');`);
  await send("Page.reload");
  await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event') && !document.getElementById('submit-btn').disabled");
  assert.equal(await evaluate("fetch('/api/events').then(r=>r.json()).then(events=>events.length)"), 1);
  await evaluate("window.confirm=()=>true;document.getElementById('import-event-btn').click();");
  await waitFor("document.getElementById('workspace-status').textContent==='Browser draft imported. Original browser data kept.' && !document.getElementById('submit-btn').disabled");
  const imported = await savedEvent(await selectedId());
  assert.equal(imported.details.title, "Browser draft");
  assert(imported.tasks[0].completed);
  assert(imported.vendors.some((vendor) => vendor.checklist.some((item) => item.completed)));
  assert.deepEqual(await evaluate("JSON.parse(localStorage.getItem('eventra:form'))"), legacy);
  assert.equal(await evaluate(`localStorage.getItem('eventra:done:${legacyKey}')`), "[0]");
  assert.deepEqual(await savedEvent(firstId), afterFinance);
  assert.deepEqual(runtimeErrors, []);
  console.log("PASS browser close/reopen and Uvicorn process restart preserve complete saved state");
  console.log("PASS explicit legacy import retains original browser data and does not alter saved events");
  await runProductSmoke({evaluate,send,waitFor,savedEvent,restart:async()=>{
    await closeBrowser();await stop(server);await startServer();await startBrowser();
    await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event')&&!document.getElementById('submit-btn').disabled");
  }});
  assert.deepEqual(runtimeErrors, []);
} catch (error) {
  console.error(serverLog.slice(-4000));
  console.error('Browser runtime errors:', JSON.stringify(runtimeErrors));
  console.error('Page state:',await evaluate("JSON.stringify({hash:location.hash,view:document.body.dataset.view,motion:document.getElementById('cinematic-hero')?.dataset.motion,hero:document.getElementById('cinematic-hero')?.getBoundingClientRect().toJSON(),demo:document.getElementById('demo-content')?.textContent})").catch(()=>null));
  throw error;
} finally {
  try { await closeBrowser(); } finally {
    await stop(server);
    // Verify the exact resolved recursive-delete target is our named temp tree.
    const relative = path.relative(path.resolve(os.tmpdir()), path.resolve(root));
    assert(relative.startsWith("eventra-workspace-smoke-") && !relative.includes(path.sep));
    try { rmSync(root, { recursive: true, force: true }); } catch { console.log("Browser files still locked; temporary profile retained at", root); }
  }
}
