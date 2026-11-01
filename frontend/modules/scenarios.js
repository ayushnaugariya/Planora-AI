import {state} from './state.js';
import {$,h,clear,store,fmtDate,money,financialMoney} from './helpers.js';
export function mountScenarios({api,applyWorkspace,setWorkspaceBusy,hasUnsavedDetails,resetExpenseForm}) {
function scenarioMessage(message, error = "") {
    $("scenario-status").textContent = message;
    $("scenario-error").textContent = error;
    $("scenario-error").hidden = !error;
    document.dispatchEvent(new CustomEvent('planora:status',{detail:{message,error,origin:'scenario'}}));
  }

  function resetScenarios() {
    state.selectedScenario = null; state.scenarioDirty = false; state.scenarioFetchToken++;
    $("scenario-form").reset(); $("scenario-approval").checked = false;
    clear($("scenario-allocation-lines")); clear($("scenario-saved"));
    $("scenario-preview").hidden = true; scenarioMessage("");
    showScenarioFields();
  }

  function showScenarioFields() {
    document.querySelectorAll('[data-scenario-kind]').forEach(
      (el) => { el.hidden = el.dataset.scenarioKind !== $("scenario-type").value; }
    );
  }

  function renderScenarioChoices() {
    if (!state.workspace) return;
    const choices = { "scenario-vendor": state.workspace.vendors.map(
      (v) => [v.id, state.workspace.plan.vendors[v.group_index].label]
    ),
      "scenario-function-category": state.workspace.plan.budget_lines.map((line) => [line.key, line.label]) };
    for (const [id, options] of Object.entries(choices)) {
      const select = $(id), previous = select.value; clear(select);
      for (const [value, label] of options) select.append(h("option", { value, text: label }));
      if ([...select.options].some((option) => option.value === previous)) select.value = previous;
    }
    if (!$("scenario-allocation-lines").children.length || (!state.scenarioDirty && !state.selectedScenario)) {
      const root = $("scenario-allocation-lines"); clear(root);
      for (const line of state.workspace.plan.budget_lines) {
        const id = "scenario-allocation-" + line.key;
        root.append(h("div", { class: "field" }, h("label", { htmlFor: id, text: line.label }),
          h(
            "input",
            {
              id,
              type: "number",
              min: "0",
              max: "100000000",
              step: "1",
              value: line.amount,
              "data-allocation-key": line.key,
              "data-allocation-label": line.label
            }
          )));
      }
    }
    fillScenarioExpenseChoices(); showScenarioFields(); renderScenarioPreview();
  }

  function fillScenarioExpenseChoices() {
    if (!state.workspace) return;
    const select = $("scenario-cost-expense"), previous = select.value; clear(select);
    select.append(h("option", { value: "", text: "Infer only when zero or one record exists" }));
    for (
      const expense of state.workspace.expenses.filter(
        (item) => item.category_key === $("scenario-cost-category").value && !item.cancelled
      )
    ) select.append(h("option", { value: expense.id, text: expense.description }));
    if ([...select.options].some((option) => option.value === previous)) select.value = previous;
  }

  async function refreshScenarios() {
    if (!state.workspace) return;
    const token = ++state.scenarioFetchToken,
    eventId = state.workspace.id,
    revision = state.workspace.revision;
    try {
      const res = await api(`/api/events/${eventId}/scenarios`, undefined, "GET");
      const list = await res.json();
      if (
        token !== state.scenarioFetchToken || state.workspace?.id !== eventId || state.workspace.revision !== revision
      ) return;
      document.dispatchEvent(new CustomEvent('planora:scenarios',{detail:list}));
      const select = $("scenario-saved"); clear(select);
      select.append(
        h("option", { value: "", text: list.length ? "Choose a saved preview" : "No saved previews yet" })
      );
      for (const item of list) select.append(
        h(
          "option",
          {
            value: item.id,
            text: `${item.parameters.type.replaceAll("_", " ")} · ${item.feasibility} · ${item.status}${item.stale ? " · stale" : ""}`
          }
        )
      );
      if (state.selectedScenario) state.selectedScenario = list.find(
        (item) => item.id === state.selectedScenario.id
      ) || state.selectedScenario;
      select.value = state.selectedScenario?.id || ""; renderScenarioPreview();
    } catch (err) {
      if (state.workspace?.id === eventId && token === state.scenarioFetchToken) scenarioMessage(
        "Saved previews could not be loaded.", err.message
      );
    }
  }

  function updateScenarioApproval() {
    const ready = state.selectedScenario && state.selectedScenario.status === "pending" && state.selectedScenario.feasibility === "feasible"
      && !state.selectedScenario.stale && state.selectedScenario.base_revision === state.workspace?.revision && !state.scenarioDirty;
    $("scenario-apply").disabled = state.workspaceBusy || !ready || !$("scenario-approval").checked;
    $("scenario-approval").disabled = state.workspaceBusy || !ready;
    $("scenario-discard").disabled = state.workspaceBusy || !state.selectedScenario || state.selectedScenario.status !== "pending";
  }

  function renderScenarioPreview() {
    $("scenario-preview").hidden = !state.selectedScenario;
    if (!state.selectedScenario || !state.workspace) { updateScenarioApproval(); return; }
    const item = state.selectedScenario;
    const labels = {
      feasible: "Feasible under known recorded constraints",
      infeasible: "Infeasible under known constraints",
      indeterminate: "Indeterminate: essential information is missing"
    };
    $("scenario-feasibility").textContent = labels[item.feasibility];
    const stale = item.stale || item.base_revision !== state.workspace.revision;
    $("scenario-preview-meta").textContent = `Saved preview from revision ${item.base_revision} · ${item.status}. ${stale ? "Event or evaluation date changed: create a fresh preview before applying." : "Original values are the saved snapshot at preview time."} ${state.scenarioDirty ? "Inputs changed: create a new preview." : ""}`;
    const rows = $("scenario-comparison"); clear(rows);
    const metrics = {
      total_budget: "Total budget",
      planned_allocation: "Planned allocation",
      projected_cost: "Projected cost",
      committed_spending: "Committed",
      actual_spending: "Paid",
      remaining_funds: "Remaining funds",
      contingency_remaining: "Protected reserve"
    };
    for (const [key, label] of Object.entries(metrics)) rows.append(
      h(
        "tr",
        {},
        h("th", { scope: "row", text: label }),
        h("td", { text: financialMoney(item.original_budget[key]) }),
        h("td", { text: financialMoney(item.proposed_budget[key]) })
      )
    );
    for (const [key, label] of [["guest_count", "Guests"], ["event_date", "Event date"]]) rows.append(
      h(
        "tr",
        {},
        h("th", { scope: "row", text: label }),
        h("td", { text: item.original_values[key] }),
        h("td", { text: item.proposed_values[key] })
      )
    );
    for (const [key, amount] of Object.entries(item.proposed_values.allocations)) if (
      amount !== item.original_values.allocations[key]
    ) rows.append(
      h(
        "tr",
        {},
        h("th", { scope: "row", text: "Allocation: " + key }),
        h("td", { text: financialMoney(item.original_values.allocations[key] ?? 0) }),
        h("td", { text: financialMoney(amount) })
      )
    );
    for (const [id, status] of Object.entries(item.proposed_values.vendors)) if (
      status !== item.original_values.vendors[id]
    ) {
      const vendor = state.workspace.vendors.find((v) => v.id === id);
      rows.append(
        h(
          "tr",
          {},
          h(
            "th",
            {
              scope: "row",
              text: vendor ? state.workspace.plan.vendors[vendor.group_index].label : "Vendor record"
            }
          ),
          h("td", { text: item.original_values.vendors[id] }),
          h("td", { text: status })
        )
      );
    }
    clear($("scenario-expense-changes"));
    for (const change of item.expense_changes) {
      const describe = (value) => value ? `quantity ${value.quantity}; estimate ${financialMoney(value.estimate)}; quote ${financialMoney(value.quoted_amount)}; committed ${financialMoney(value.committed_amount)}; paid ${financialMoney(value.paid_amount)}${value.cancelled ? "; cancelled" : ""}` : "New record";
      $("scenario-expense-changes").append(
        h(
          "li",
          {
            text: `${change.after?.description || change.before.description}: ${describe(change.before)} → ${describe(change.after)}`
          }
        )
      );
    }
    if (!item.expense_changes.length) $("scenario-expense-changes").append(
      h("li", { text: "No expense records change." })
    );
    clear($("scenario-task-changes"));
    for (const task of item.affected_tasks) $("scenario-task-changes").append(
      h(
        "li",
        {
          text: `${task.title}: ${fmtDate(task.original_due)} → ${fmtDate(task.proposed_due)}. ${task.completed ? "Completion kept." : "Open task."} ${task.dependencies.length} prerequisite(s).`
        }
      )
    );
    if (!item.affected_tasks.length) $("scenario-task-changes").append(
      h("li", { text: "No task deadlines or vendor dependencies change." })
    );
    clear($("scenario-risks"));
    for (const warning of [...new Set([...item.reasons, ...item.warnings])]) $("scenario-risks").append(
      h("li", { text: warning })
    );
    updateScenarioApproval();
  }

  function scenarioParameters() {
    const type = $("scenario-type").value;
    const optional = (id) => $(id).value.trim() || null;
    if (type === "budget_reduction") {
      const result = { type, [$("scenario-reduction-mode").value]: $("scenario-reduction").value };
      if ($("scenario-adjust-allocations").checked) result.allocations = [
        ...document.querySelectorAll('[data-allocation-key]')
      ].map(
        (input) => (
          {
            key: input.dataset.allocationKey,
            label: input.dataset.allocationLabel,
            amount: Number(input.value)
          }
        )
      );
      return result;
    }
    if (type === "guest_count") return { type, guest_count: Number($("scenario-guests").value) };
    if (type === "event_date") return { type, event_date: $("scenario-date").value };
    if (type === "vendor_cancellation") return {
      type,
      vendor_id: $("scenario-vendor").value,
      cancellation_fee: optional("scenario-cancel-fee"),
      replacement_cost: optional("scenario-replacement"),
      replacement_confirmed: $("scenario-replacement-confirmed").checked
    };
    if (type === "category_cost") return {
      type,
      category_key: $("scenario-cost-category").value,
      amount: $("scenario-cost").value,
      expense_id: optional("scenario-cost-expense")
    };
    return {
      type,
      name: $("scenario-function-name").value,
      category_key: $("scenario-function-category").value,
      estimated_cost: optional("scenario-function-cost")
    };
  }

  function fillScenarioInputs(params) {
    $("scenario-form").reset(); $("scenario-type").value = params.type;
    for (const line of state.workspace.plan.budget_lines) {
      const input = $("scenario-allocation-" + line.key); if (input) input.value = line.amount;
    }
    if (params.type === "budget_reduction") {
      $("scenario-reduction-mode").value = params.percent != null ? "percent" : "amount";
      $("scenario-reduction").value = params.percent ?? params.amount;
      $("scenario-adjust-allocations").checked = params.allocations != null;
      for (const allocation of params.allocations || []) {
        const input = $("scenario-allocation-" + allocation.key); if (input) input.value = allocation.amount;
      }
    } else if (params.type === "guest_count") $("scenario-guests").value = params.guest_count;
    else if (params.type === "event_date") $("scenario-date").value = params.event_date;
    else if (params.type === "vendor_cancellation") {
      $("scenario-vendor").value = params.vendor_id;
      $("scenario-cancel-fee").value = params.cancellation_fee ?? "";
      $("scenario-replacement").value = params.replacement_cost ?? "";
      $("scenario-replacement-confirmed").checked = params.replacement_confirmed;
    } else if (params.type === "category_cost") {
      $("scenario-cost-category").value = params.category_key; fillScenarioExpenseChoices();
      $("scenario-cost-expense").value = params.expense_id || ""; $("scenario-cost").value = params.amount;
    } else {
      $("scenario-function-name").value = params.name;
      $("scenario-function-category").value = params.category_key;
      $("scenario-function-cost").value = params.estimated_cost ?? "";
    }
    showScenarioFields(); $("scenario-approval").checked = false;
  }

  async function scenarioAction(action) {
    if (state.workspaceBusy) return;
    setWorkspaceBusy(true); scenarioMessage("Working on preview…");
    try { await action(); } catch (err) {
      scenarioMessage(
        "Action was not confirmed. Reopen the event before retrying; your inputs were kept.", err.message
      );
    }
    finally { setWorkspaceBusy(false); }
  }
  $("scenario-type").addEventListener("change", showScenarioFields);
  const clearInputs=h('button',{type:'button',class:'ghost',text:'Clear unsaved inputs'});
  clearInputs.addEventListener('click',()=>{
    if(
      state.workspaceBusy||state.scenarioDirty&&!confirm(
        'Clear unsaved scenario inputs? Saved previews are kept.'
      )
    )return;
    state.scenarioDirty=false;
    state.selectedScenario=null;
    $('scenario-form').reset();
    $('scenario-approval').checked=false;
    renderScenarioChoices();
    scenarioMessage('Inputs reset. Saved previews and the event are unchanged.');
    refreshScenarios();
  });
  $('scenario-form').append(clearInputs);
  $("scenario-cost-category").addEventListener("change", fillScenarioExpenseChoices);
  $("scenario-form").addEventListener(
    "input",
    () => { state.scenarioDirty = true; $("scenario-approval").checked = false; renderScenarioPreview(); }
  );
  $("scenario-approval").addEventListener("change", updateScenarioApproval);
  $("scenario-form").addEventListener("submit", (event) => {
    event.preventDefault();
    scenarioAction(async () => {
      const res = await api(
        `/api/events/${state.workspace.id}/scenarios`,
        { revision: state.workspace.revision, parameters: scenarioParameters() }
      );
      state.selectedScenario = await res.json();
      state.scenarioDirty = false;
      fillScenarioInputs(state.selectedScenario.parameters);
      renderScenarioPreview();
      scenarioMessage("Preview saved. Original event unchanged.");
      refreshScenarios();
    });
  });
  $("scenario-saved").addEventListener("change", () => {
    const id = $("scenario-saved").value; if (!id) return;
    if (state.scenarioDirty && !confirm("Discard unsaved what-if inputs and open this preview?")) {
      $("scenario-saved").value = state.selectedScenario?.id || ""; return;
    }
    scenarioAction(async () => {
      const res = await api(`/api/events/${state.workspace.id}/scenarios/${id}`, undefined, "GET");
      state.selectedScenario = await res.json();
      state.scenarioDirty = false;
      fillScenarioInputs(state.selectedScenario.parameters);
      renderScenarioPreview(); scenarioMessage("Saved preview opened. Original event unchanged.");
    });
  });
  $("scenario-discard").addEventListener("click", () => scenarioAction(async () => {
    const res = await api(
      `/api/events/${state.workspace.id}/scenarios/${state.selectedScenario.id}/discard`, {}
    );
    state.selectedScenario = await res.json(); $("scenario-approval").checked = false;
    renderScenarioPreview(); scenarioMessage("Preview discarded. Saved event unchanged."); refreshScenarios();
  }));
  $("scenario-apply").addEventListener("click", () => {
    if (!$("scenario-approval").checked || $("scenario-apply").disabled) return;
    if (
      hasUnsavedDetails() && !confirm(
        "Applying this preview replaces unsaved event and expense inputs. Continue?"
      )
    ) return;
    scenarioAction(async () => {
      const res = await api(
        `/api/events/${state.workspace.id}/scenarios/${state.selectedScenario.id}/apply`,
        { revision: state.workspace.revision, approved: true }
      );
      const saved = await res.json(); state.selectedScenario.status = "applied"; state.scenarioDirty = false;
      $("scenario-approval").checked = false;
      resetExpenseForm();
      $("allocation-form").reset();
      state.allocationDirty = false;
      applyWorkspace(saved, true, false);
      scenarioMessage("Scenario applied and saved.");
    });
  });
  $("scenario-interpret-form").addEventListener("submit", (event) => {
    event.preventDefault();
    scenarioAction(async () => {
      const res = await api(
        `/api/events/${state.workspace.id}/scenarios/interpret`,
        { revision: state.workspace.revision, question: $("scenario-question").value.trim() }
      );
      const suggestion = await res.json();
      if (suggestion.parameters) {
        state.selectedScenario = null;
        fillScenarioInputs(suggestion.parameters);
        state.scenarioDirty = true;
        renderScenarioPreview();
      }
      scenarioMessage(
        `${suggestion.source === "gemini" ? "Gemini suggestion" : "Built-in fallback"}: ${suggestion.explanation}`
      );
    });
  });

  
return {
  scenarioMessage,
  resetScenarios,
  showScenarioFields,
  renderScenarioChoices,
  renderScenarioPreview,
  updateScenarioApproval,
  refreshScenarios,
  fillScenarioInputs
};
}
