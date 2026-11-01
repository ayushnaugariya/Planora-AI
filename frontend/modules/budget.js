import {state} from './state.js';
import {$,h,clear,store,fmtDate,money,financialMoney} from './helpers.js';
export function mountBudget({api,applyWorkspace,setWorkspaceBusy}) {
function budgetMessage(message, error = "") {
    $("budget-status").textContent = message;
    $("budget-error").textContent = error;
    $("budget-error").hidden = !error;
  }

  function resetExpenseForm() {
    $("expense-form").reset();
    state.editingExpenseId = state.expenseRequestId = null;
    state.expenseDirty = false;
    $("expense-save").textContent = "Add expense";
  }

  function renderGuardian() {
    if (!state.workspace) return;
    const summary = state.workspace.budget_summary;
    const root = $("budget-metrics"); clear(root);
    const labels = {
      total_budget: "Total budget",
      planned_allocation: "Planned allocation",
      estimated_cost: "Estimated costs",
      quoted_cost: "Quoted costs",
      committed_spending: "Committed",
      actual_spending: "Actual paid",
      projected_cost: "Projected recorded cost",
      remaining_funds: "Remaining (includes reserve)",
      contingency_remaining: "Contingency remaining",
      spendable_remaining: "Spendable after reserve",
      unallocated_funds: "Unallocated",
      outstanding_commitments: "Commitments not yet paid"
    };
    for (const [key, label] of Object.entries(labels)) root.append(
      h(
        "div",
        { class: "budget-metric" },
        h("span", { text: label }),
        h("strong", { id: "metric-" + key, text: financialMoney(summary[key]) })
      )
    );
    clear($("budget-warnings"));
    for (const warning of summary.warnings) $("budget-warnings").append(h("li", { text: warning.message }));
    for (const id of ["expense-category", "allocation-category"]) {
      const select = $(id), previous = select.value;
      clear(select);
      for (const line of state.workspace.plan.budget_lines) select.append(
        h("option", { value: line.key, text: line.label })
      );
      if (id === "allocation-category") select.append(
        h("option", { value: "__new", text: "Create a category" })
      );
      if ([...select.options].some((option) => option.value === previous)) select.value = previous;
    }
    const vendors = $("expense-vendor"), previousVendor = vendors.value; clear(vendors);
    vendors.append(h("option", { value: "", text: "No linked vendor" }));
    for (const vendor of state.workspace.vendors) vendors.append(
      h("option", { value: vendor.id, text: state.workspace.plan.vendors[vendor.group_index].label })
    );
    if ([...vendors.options].some((option) => option.value === previousVendor)) vendors.value = previousVendor;
    const rows = $("expense-rows"); clear(rows);
    for (const expense of state.workspace.expenses) {
      const edit = h(
        "button",
        {
          type: "button",
          class: "ghost",
          text: "Edit",
          "data-budget-action": true,
          "aria-label": `Edit ${expense.description}`
        }
      );
      edit.addEventListener("click", () => {
        if (state.expenseDirty && !confirm("Discard unsaved expense form changes?")) return;
        state.editingExpenseId = expense.id; state.expenseDirty = false;
        const fields = {
          description: "description",
          category: "category_key",
          basis: "cost_basis",
          quantity: "quantity",
          unit: "unit_amount",
          estimate: "estimated_amount",
          tax: "tax",
          fee: "fee",
          quote: "quoted_amount",
          commitment: "committed_amount",
          paid: "paid_amount",
          vendor: "vendor_id",
          notes: "notes"
        };
        for (const [id, key] of Object.entries(fields)) $("expense-" + id).value = expense[key] ?? "";
        $("expense-save").textContent = "Save expense changes";
        $("expense-editor").open = true;
        $("expense-description").focus();
      });
      const remove = h(
        "button",
        {
          type: "button",
          class: "ghost",
          text: "Delete",
          "data-budget-action": true,
          "aria-label": `Delete ${expense.description}`
        }
      );
      remove.addEventListener("click", () => {
        if (
          !confirm(
            `Remove '${expense.description}' and its recorded amounts from current totals? This is not a refund.`
          )
        ) return;
        budgetAction(async () => {
          const res = await api(
            `/api/events/${state.workspace.id}/budget/expenses/${expense.id}`,
            { revision: state.workspace.revision, confirm_id: expense.id },
            "DELETE"
          );
          applyWorkspace(await res.json(), true, true);
          if (state.editingExpenseId === expense.id) resetExpenseForm();
          budgetMessage("Expense deleted and totals reconciled.");
        });
      });
      rows.append(h("tr",
      { "data-expense-id": expense.id },
      h("td", { text: expense.description + (expense.cancelled ? " (cancelled)" : "") }),
      h("td", { text: expense.category_key }),
        ...[expense.estimate, expense.quoted_amount, expense.committed_amount, expense.paid_amount].map(
          (value) => h("td", { class: "num", text: financialMoney(value) })
        ),
        h("td", { text: expense.payment_status }), h("td", { class: "expense-actions" }, edit, remove)));
    }
    if (!state.workspace.expenses.length) rows.append(
      h("tr", {}, h("td", { colSpan: 8, text: "No expense records yet. Missing prices are not zero costs." }))
    );
    if (!state.allocationDirty) fillAllocation();
  }

  async function budgetAction(action) {
    if (state.workspaceBusy) return;
    setWorkspaceBusy(true); budgetMessage("Saving…");
    try { await action(); } catch (err) {
      budgetMessage(
        "Change was not confirmed. Inputs were kept; retry or reopen if the event changed.", err.message
      );
    }
    finally { setWorkspaceBusy(false); }
  }

  $("expense-form").addEventListener("input", () => { state.expenseDirty = true; });
  $("expense-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.workspace) return;
    const optional = (id) => $("expense-" + id).value.trim() || null;
    const expense = { category_key: $("expense-category").value,
    description: $("expense-description").value,
    currency: state.workspace.details.currency,
      quantity: $("expense-quantity").value || "1",
      cost_basis: $("expense-basis").value,
      unit_amount: optional("unit"),
      tax: optional("tax") || "0",
      fee: optional("fee") || "0",
      estimated_amount: optional("estimate"),
      quoted_amount: optional("quote"),
      committed_amount: optional("commitment"),
      paid_amount: optional("paid") || "0",
      vendor_id: optional("vendor"),
      notes: $("expense-notes").value };
    if (!state.editingExpenseId && !state.expenseRequestId) state.expenseRequestId = crypto.randomUUID();
    budgetAction(async () => {
      const path = `/api/events/${state.workspace.id}/budget/expenses` + (
        state.editingExpenseId ? `/${state.editingExpenseId}` : ""
      );
      const body = { revision: state.workspace.revision, expense };
      if (!state.editingExpenseId) body.request_id = state.expenseRequestId;
      const res = await api(path, body, state.editingExpenseId ? "PUT" : "POST");
      applyWorkspace(await res.json(), true, true); resetExpenseForm();
      budgetMessage("Expense saved and totals reconciled.");
    });
  });
  $("expense-cancel").addEventListener("click", () => {
    if (state.expenseDirty && !confirm("Clear unsaved expense inputs?")) return;
    resetExpenseForm(); budgetMessage("Expense form cleared. Saved records are unchanged.");
  });
  function fillAllocation() {
    const line = state.workspace?.plan.budget_lines.find(
      (item) => item.key === $("allocation-category").value
    );
    $("allocation-key").value = line?.key || "";
    $("allocation-label").value = line?.label || "";
    $("allocation-amount").value = line?.amount ?? "";
    state.allocationDirty = false;
  }
  $("allocation-form").addEventListener("input", () => { state.allocationDirty = true; });
  $("allocation-category").addEventListener("change", fillAllocation);
  $("allocation-form").addEventListener("submit", (event) => {
    event.preventDefault();
    budgetAction(async () => {
      const allocation = {
        key: $("allocation-key").value,
        label: $("allocation-label").value,
        amount: Number($("allocation-amount").value)
      };
      const res = await api(
        `/api/events/${state.workspace.id}/budget/allocations`,
        { revision: state.workspace.revision, allocations: [allocation] },
        "PATCH"
      );
      const saved = await res.json(); state.allocationDirty = false;
      applyWorkspace(saved, true, true);
      budgetMessage("Category allocation saved; other allocations unchanged.");
    });
  });

  
return {budgetMessage,resetExpenseForm,renderGuardian,fillAllocation};
}
