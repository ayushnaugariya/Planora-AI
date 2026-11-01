import {mountWebsiteEditor} from '/static/modules/website-editor.js';
import {mountCommandCenter} from '/static/modules/command-center.js';
import {mountNegotiation} from '/static/modules/negotiation.js';
import {mountGuests} from '/static/modules/guests.js';
import {mountEventPortal} from '/static/modules/event-portal.js';
import {state} from '/static/modules/state.js';
import {$,h,clear,store,reduceMotion,isoLocal,fmtDate,money,setCurrency,financialMoney} from '/static/modules/helpers.js';
import {api} from '/static/modules/api.js';
import {mountPlanViews} from '/static/modules/plan-views.js';
import {mountBudget} from '/static/modules/budget.js';
import {mountScenarios} from '/static/modules/scenarios.js';
import {mountWizard} from '/static/modules/wizard.js';
import {mountShell} from '/static/modules/shell.js';
import {mountCoordination} from '/static/modules/coordination.js';
import {mountRescue} from '/static/modules/rescue.js';
import {mountMotion} from '/static/modules/motion.js';
import {mountDemo} from '/static/modules/demo.js';
import {mountCopilot} from '/static/modules/copilot.js';
import {mountCinematic} from '/static/modules/cinematic.js';
import {mountQuoteComparison} from '/static/modules/quote-comparison.js';
import {mountPortal} from '/static/modules/portal.js';
import {mountIntelligence} from '/static/modules/intelligence.js';
import {mountDecisionComparison} from '/static/modules/decision-comparison.js';
import {mountScrollStory} from '/static/modules/scroll-story.js';
import {mountSignatureIntelligence} from '/static/modules/signature-intelligence.js';
import {mountReadiness} from '/static/modules/readiness.js';
const {renderHealth,renderWarnings,renderBudget,renderTimeline,renderVendors,renderIdeas} = mountPlanViews(
  {saveProgress}
);
const {budgetMessage,resetExpenseForm,renderGuardian,fillAllocation} = mountBudget(
  {api,applyWorkspace,setWorkspaceBusy}
);
const {
  scenarioMessage,
  resetScenarios,
  showScenarioFields,
  renderScenarioChoices,
  renderScenarioPreview,
  updateScenarioApproval,
  refreshScenarios,
  fillScenarioInputs
} = mountScenarios({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails,resetExpenseForm});
"use strict";

  // ---------- helpers ----------
  

  // ---------- state ----------
  
  
  
  
  
  
  
  
  
  
  

  // ---------- init ----------
  const form = $("plan-form");
  let newDraftDirty = false;
  form.addEventListener('input',()=>{if(!state.workspace)newDraftDirty=true;});

  const dateInput = $("event_date");
  const today = new Date();
  dateInput.min = isoLocal(today);
  const def = new Date(today); def.setDate(def.getDate() + 120);
  dateInput.value = isoLocal(def);

  const legacyValue = store.get("eventra:form", null);
  const saved = legacyValue && typeof legacyValue === "object" && !Array.isArray(legacyValue) ? legacyValue : null;
  if (saved) restoreForm(saved);

  function restoreForm(s) {
    for (
      const key of [
        "title",
        "event_date",
        "guest_count",
        "budget",
        "currency",
        "formality",
        "theme",
        "interests",
        "city",
        "notes",
        "venue_preferences",
        "cultural_requirements",
        "accessibility_requirements",
        "assumptions",
        "unresolved_decisions"
      ]
    ) {
      if (s[key] !== undefined && form.elements[key]) form.elements[key].value = s[key];
    }
    if (s.event_date && s.event_date < dateInput.min) dateInput.value = isoLocal(def);
    if (s.event_type) {
      const r = form.querySelector(`input[name="event_type"][value="${CSS.escape(s.event_type)}"]`);
      if (r) r.checked = true;
    }
    for (const name of ["priorities", "dietary"]) {
      const set = new Set(Array.isArray(s[name]) ? s[name] : []);
      form.querySelectorAll(`input[name="${name}"]`).forEach((c) => { c.checked = set.has(c.value); });
    }
  }

  // limit priorities to 3
  const prioBoxes = [...form.querySelectorAll('input[name="priorities"]')];
  function syncPriorityLimit() {
    const n = prioBoxes.filter((b) => b.checked).length;
    prioBoxes.forEach((b) => { b.disabled = n >= 3 && !b.checked; });
  }
  prioBoxes.forEach((b) => b.addEventListener("change", syncPriorityLimit));
  syncPriorityLimit();

  function readForm() {
    const f = form.elements;
    const checked = (name) => [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((c) => c.value);
    return {
      event_type: form.querySelector('input[name="event_type"]:checked').value,
      title: f.title.value.trim(),
      event_date: f.event_date.value,
      guest_count: Number(f.guest_count.value),
      budget: Number(f.budget.value),
      currency: f.currency.value,
      formality: f.formality.value,
      priorities: checked("priorities"),
      dietary: checked("dietary"),
      theme: f.theme.value.trim(),
      interests: f.interests.value.trim(),
      city: f.city.value.trim(),
      notes: f.notes.value.trim(),
      venue_preferences: f.venue_preferences.value.trim(),
      cultural_requirements: f.cultural_requirements.value.trim(),
      accessibility_requirements: f.accessibility_requirements.value.trim(),
      assumptions: f.assumptions.value.trim(),
      unresolved_decisions: f.unresolved_decisions.value.trim(),
    };
  }

  function validate(p) {
    if (!p.event_date) return "Choose the event date.";
    if (p.event_date < dateInput.min) return "The event date can't be in the past.";
    if (!Number.isInteger(p.guest_count) || p.guest_count < 2 || p.guest_count > 5000) return "Guests must be a whole number between 2 and 5,000.";
    if (!Number.isFinite(p.budget) || p.budget < 1000 || p.budget > 100000000) return "Budget must be between 1,000 and 100,000,000.";
    return "";
  }

  function showFormError(msg) {
    const el = $("form-error");
    el.textContent = msg;
    el.hidden = !msg;
  }

  

  // ---------- submit ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (state.workspaceBusy) return;
    const payload = readForm();
    const problem = validate(payload);
    showFormError(problem);
    if (problem) return;
    const btn = $("submit-btn");
    btn.disabled = true;
    btn.textContent = "Building your plan...";
    setWorkspaceBusy(true);
    workspaceStatus("Saving event and building plan…");
    try {
      const path = state.workspace ? `/api/events/${state.workspace.id}` : "/api/events";
      const body = state.workspace ? { revision: state.workspace.revision, details: payload } : {
        details: payload
      };
      const res = await api(path, body, state.workspace ? "PATCH" : "POST");
      applyWorkspace(await res.json());
      workspaceStatus("Event and plan saved.");
      await refreshAfterSave();
    } catch (err) {
      showFormError(err.message);
      workspaceStatus("Save did not complete. Your changes are still in the form.");
    } finally {
      setWorkspaceBusy(false);
      btn.textContent = "Save and build my plan";
    }
  });

  // ---------- rendering ----------
  function render(plan, preserveView = false) {
    const activeTab = document.querySelector('#tablist [aria-selected="true"]').id;
    setCurrency(plan.currency);
    $("empty").hidden = true;
    $("plan").hidden = false;

    $("plan-title").textContent = plan.title;
    const when = plan.days_until === 0 ? "today" : plan.days_until === 1 ? "tomorrow" : `in ${plan.days_until} days`;
    $("plan-meta").textContent = `${fmtDate(plan.event_date)} (${when}) · ${plan.guest_count} guests · ${money(plan.budget)}`;
    $("plan-summary").textContent = plan.summary;
    $("source-note").textContent = plan.ai_source === "gemini"
      ? "Ideas and tips were written by Gemini for your event. Budget and dates are calculated by Planora AI."
      : "Ideas and tips use Planora AI's built-in planner. Saved budget figures and dates are calculated by Planora AI.";

    renderHealth(plan);
    renderWarnings(plan.warnings);
    renderBudget(plan);
    renderGuardian();
    renderScenarioChoices();
    renderTimeline(plan);
    renderVendors(plan);
    renderIdeas(plan);
    resetChat();
    selectTab(preserveView ? activeTab : "tab-overview", false, false);

    const results = $("results");
    if (!preserveView) {
      results.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      results.focus({ preventScroll: true });
    }
  }

  

  // ---------- tabs ----------
  const tabs = [...document.querySelectorAll('#tablist [role="tab"]')];
  function selectTab(id, focus, navigate = true) {
    for (const t of tabs) {
      const on = t.id === id;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      $(t.getAttribute("aria-controls")).hidden = !on;
      if (on && focus) t.focus();
    }
    if (navigate) document.dispatchEvent(new CustomEvent('planora:tab', {detail:id}));
  }
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => selectTab(t.id, false));
    t.addEventListener("keydown", (e) => {
      let n = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") n = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") n = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") n = 0;
      else if (e.key === "End") n = tabs.length - 1;
      if (n !== null) { e.preventDefault(); selectTab(tabs[n].id, true); }
    });
  });

  // ---------- actions ----------
  $("print-btn").addEventListener("click", () => window.print());

  $("ics-btn").addEventListener("click", async () => {
    if (!state.lastRequest) return;
    const btn = $("ics-btn");
    btn.disabled = true;
    try {
      const res = state.workspace ? await api(`/api/events/${state.workspace.id}/ics`, undefined, "GET") : await api(
        "/api/ics", state.lastRequest
      );
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = h("a", { href: url, download: "eventra-timeline.ics" });
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      alert(err.message);
    } finally {
      btn.disabled = false;
    }
  });

  // Saved workspaces are authoritative; localStorage holds only a selection
  // pointer and untouched legacy data offered through an explicit import.
  function workspaceStatus(message, error = "") {
    $("workspace-status").textContent = message;
    $("workspace-error").textContent = error;
    $("workspace-error").hidden = !error;
    document.dispatchEvent(new CustomEvent('planora:status',{detail:{message,error}}));
  }

  function setWorkspaceBusy(busy) {
    state.workspaceBusy = busy;
    document.querySelectorAll(
      '[data-workspace-control], #plan-form input, #plan-form select, #plan-form textarea, #submit-btn, #chat-btn, #timeline-list input, #vendor-list input, .guardian input, .guardian select, .guardian textarea, .guardian button, [data-budget-action], .scenario-tool input, .scenario-tool select, .scenario-tool textarea, .scenario-tool button, .signature-tool input, .signature-tool select, .signature-tool textarea, .signature-tool button'
    ).forEach((el) => { el.disabled = busy; });
    if (!busy) {
      syncPriorityLimit();
      $("rename-event-btn").disabled = !state.workspace;
      $("delete-event-btn").disabled = !state.workspace;
      updateScenarioApproval();
    }
      document.dispatchEvent(new CustomEvent('planora:busy',{detail:busy}));
  }

  function applyWorkspace(savedWorkspace, preserveView = false, preserveForm = false) {
    newDraftDirty = false;
    if (state.workspace && state.workspace.id !== savedWorkspace.id) {
      resetExpenseForm(); $("allocation-form").reset(); state.allocationDirty = false; resetScenarios();
    }
    state.workspace = savedWorkspace;
    state.lastRequest = savedWorkspace.details;
    state.lastPlan = savedWorkspace.plan;
    store.set("eventra:selected-event", savedWorkspace.id);
    if (!preserveForm) {
      restoreForm(savedWorkspace.details);
      // Reopening a historical event must not silently replace its date.
      dateInput.value = savedWorkspace.details.event_date;
    }
    $("saved-event-select").value = savedWorkspace.id;
    render(savedWorkspace.plan, preserveView);
    $("results").setAttribute("aria-labelledby", "plan-title");
    refreshScenarios();
    document.dispatchEvent(new CustomEvent('planora:workspace',{detail:{preserveView}}));
  }

  async function refreshEvents() {
    const res = await api("/api/events", undefined, "GET");
    const events = await res.json();
    state.events = events;
    const select = $("saved-event-select");
    clear(select);
    select.append(
      h("option", { value: "", text: events.length ? "Choose a saved event" : "No saved events yet" })
    );
    for (const event of events) select.append(
      h("option", { value: event.id, text: `${event.title} · ${fmtDate(event.event_date)}` })
    );
    select.value = state.workspace ? state.workspace.id : "";
    document.dispatchEvent(new Event('planora:events'));
    return events;
  }

  async function refreshAfterSave() {
    try { await refreshEvents(); } catch (err) {
      workspaceStatus("Your change was saved. The event list could not refresh.", err.message);
    }
  }

  function hasUnsavedDetails(
    ignoreQuoteDraft = false,
    ignoreGuestDraft = false,
    ignoreNegotiationDraft = false,
    ignoreCommandDraft = false,
    ignoreWebsiteDraft = false
  ) {
    if (!ignoreWebsiteDraft && state.websiteDirty) return true;
    if (!ignoreCommandDraft && state.commandDirty) return true;
    if ((!ignoreGuestDraft && state.guestDirty) || (!ignoreNegotiationDraft && state.negotiationDirty)) return true;
    if (
      state.expenseDirty || state.allocationDirty || state.scenarioDirty || state.quoteDirty && !ignoreQuoteDraft
    ) return true;
    if (!state.workspace) return newDraftDirty;
    const details = readForm();
    return Object.keys(details).some(
      (key) => JSON.stringify(details[key]) !== JSON.stringify(state.workspace.details[key])
    );
  }

  async function workspaceAction(action) {
    if (state.workspaceBusy) return;
    setWorkspaceBusy(true);
    try { await action(); } catch (err) {
      $("saved-event-select").value = state.workspace ? state.workspace.id : "";
      workspaceStatus("Action did not complete.", err.message);
    }
    finally { setWorkspaceBusy(false); }
  }

  async function openWorkspace(id) {
    workspaceStatus("Opening saved event…");
    const res = await api(`/api/events/${encodeURIComponent(id)}`, undefined, "GET");
    applyWorkspace(await res.json());
    workspaceStatus(
      `Opened saved event, revision ${state.workspace.revision}. Plan last built ${new Date(state.workspace.generated_at).toLocaleString()}.`
    );
  }

  $("saved-event-select").addEventListener("change", () => {
    const id = $("saved-event-select").value;
    if (!id) { $("saved-event-select").value = state.workspace ? state.workspace.id : ""; return; }
    if (hasUnsavedDetails() && !confirm("Discard unsaved form changes and open this event?")) {
      $("saved-event-select").value = state.workspace?.id || ""; return;
    }
    workspaceAction(() => openWorkspace(id));
  });

  $("refresh-events-btn").addEventListener("click", () => workspaceAction(async () => {
    const events = await refreshEvents();
    workspaceStatus(
      events.length ? "Saved-event list refreshed." : "No saved events yet. Fill in the form to create one."
    );
  }));

  $("new-event-btn").addEventListener("click", () => {
    if (hasUnsavedDetails() && !confirm("Discard unsaved form changes and create another event?")) return;
    state.workspace = state.lastRequest = state.lastPlan = null;
    newDraftDirty = false;
    resetExpenseForm();
    $("allocation-form").reset(); state.allocationDirty = false;
    resetScenarios();
    store.set("eventra:selected-event", null);
    form.reset(); dateInput.value = isoLocal(def);
    $("plan").hidden = true; $("empty").hidden = false;
    $("results").setAttribute("aria-labelledby", "results-title");
    $("saved-event-select").value = "";
    showFormError(""); setWorkspaceBusy(false);
    workspaceStatus("New event. Your other saved events are unchanged.");
  });

  $("rename-event-btn").addEventListener("click", () => workspaceAction(async () => {
    const res = await api(
      `/api/events/${state.workspace.id}`,
      { revision: state.workspace.revision, title: form.elements.title.value.trim() },
      "PATCH"
    );
    applyWorkspace(await res.json(), true, true);
    form.elements.title.value = state.workspace.details.title;
    workspaceStatus("Event name saved."); await refreshAfterSave();
  }));

  $("delete-event-btn").addEventListener("click", () => {
    if (
      !state.workspace || !confirm(
        `Permanently delete '${state.workspace.plan.title}' and all its saved planning data?`
      )
    ) return;
    workspaceAction(async () => {
      await api(
        `/api/events/${state.workspace.id}`,
        { revision: state.workspace.revision, confirm_id: state.workspace.id },
        "DELETE"
      );
      state.workspace = state.lastRequest = state.lastPlan = null;
      resetExpenseForm();
      $("allocation-form").reset(); state.allocationDirty = false;
      resetScenarios();
      store.set("eventra:selected-event", null);
      form.reset(); dateInput.value = isoLocal(def);
      $("plan").hidden = true; $("empty").hidden = false;
      $("results").setAttribute("aria-labelledby", "results-title");
      workspaceStatus("Event deleted."); await refreshAfterSave();
    });
  });

  async function saveProgress(checkbox, id, isTask) {
    const previous = !checkbox.checked;
    if (state.workspaceBusy) { checkbox.checked = previous; return; }
    const tasks = new Set(
      state.workspace.tasks.filter(
        (t) => t.completed && state.workspace.plan.timeline[t.milestone_index].category !== "event"
      ).map((t) => t.id)
    );
    const checks = new Set(
      state.workspace.vendors.flatMap((v) => v.checklist.filter((c) => c.completed).map((c) => c.id))
    );
    const selected = isTask ? tasks : checks;
    if (checkbox.checked) selected.add(id); else selected.delete(id);
    setWorkspaceBusy(true); workspaceStatus("Saving checklist…");
    try {
      const res = await api(
        `/api/events/${state.workspace.id}`,
        {
          revision: state.workspace.revision,
          progress: { completed_tasks: [...tasks], completed_checks: [...checks] }
        },
        "PATCH"
      );
      applyWorkspace(await res.json(), true, true);
      workspaceStatus("Checklist saved.");
    } catch (err) {
      checkbox.checked = previous;
      workspaceStatus("Checklist change was not saved.", err.message);
    } finally { setWorkspaceBusy(false); }
  }

  $("import-event-btn").hidden = !saved;
  $("import-event-btn").addEventListener("click", () => {
    if (
      !confirm(
        "Import the last browser draft and matching checklist progress as a new saved event? Existing browser data will be kept. Unsaved form changes will be replaced."
      )
    ) return;
    workspaceAction(async () => {
      const name = saved.title || saved.event_type.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
      const key = `${saved.event_type}|${saved.event_date}|${name}`;
      const timeline = store.get("eventra:done:" + key, []);
      const vendors = store.get("eventra:vendor:" + key, []);
      if (!Array.isArray(timeline) || !Array.isArray(vendors)) throw new Error(
        "Browser progress is damaged. The original data has been kept."
      );
      const res = await api("/api/events", { details: saved, legacy_progress: { timeline, vendors } });
      applyWorkspace(await res.json());
      workspaceStatus("Browser draft imported. Original browser data kept.");
      await refreshAfterSave();
    });
  });

  

  state.booting = true;
  const wizard = mountWizard({readForm,showFormError});
  const shell = mountShell({wizard,selectTab,openWorkspace,workspaceAction,hasUnsavedDetails});
  mountIntelligence(
    {
      api,
      restoreForm,
      wizard,
      applyWorkspace,
      refreshAfterSave,
      setWorkspaceBusy,
      hasUnsavedDetails,
      workspaceStatus,
      go:shell.go
    }
  );
  mountDecisionComparison();
  const {resetChat} = mountCopilot({api,applyWorkspace,setWorkspaceBusy,workspaceStatus});
  mountCoordination({api,applyWorkspace,setWorkspaceBusy,saveProgress,go:shell.go,hasUnsavedDetails});
  mountRescue(
    {api,setWorkspaceBusy,hasUnsavedDetails,fillScenarioInputs,renderScenarioPreview,refreshScenarios}
  );
  mountQuoteComparison(
    {api,setWorkspaceBusy,hasUnsavedDetails,fillScenarioInputs,renderScenarioPreview,refreshScenarios}
  );
  mountSignatureIntelligence(
    {
      api,
      applyWorkspace,
      setWorkspaceBusy,
      hasUnsavedDetails,
      fillScenarioInputs,
      renderScenarioPreview,
      refreshScenarios,
      go:shell.go
    }
  );
  mountReadiness({api});
  mountMotion();
  mountDemo();
  mountCinematic();
  mountPortal();
  mountScrollStory();
  workspaceAction(async () => {
    const selected = location.hash.match(/^#\/event\/([a-f0-9-]{36})\//i)?.[1] || store.get(
      "eventra:selected-event", null
    );
    const events = await refreshEvents();
    if (selected && events.some((event) => event.id === selected)) await openWorkspace(selected);
    else workspaceStatus(
      events.length ? "Choose an event to continue planning." : "No saved events yet. Save your first plan below."
    );
  }).finally(()=>{state.booting=false;shell.route();});

mountEventPortal();

mountGuests({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails});

mountNegotiation({api,setWorkspaceBusy,hasUnsavedDetails});
mountCommandCenter({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails});
mountWebsiteEditor({api,setWorkspaceBusy,hasUnsavedDetails});
