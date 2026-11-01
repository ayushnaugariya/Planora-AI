import {state} from './state.js';
import {$,h,clear,financialMoney} from './helpers.js';

export function mountCopilot({api,applyWorkspace,setWorkspaceBusy,workspaceStatus}) {
  const context=h('section',{class:'copilot-context','aria-label':'Saved planning context'});
  $('chat-log').before(context);
  // ---------- chat ----------
  function resetChat() {
    clear(context);
    if(state.workspace){
      const event=state.workspace,summary=event.budget_summary;
      context.append(
        h(
          'div',
          {},
          h('span',{class:'eyebrow',text:'SAVED FACTS / GENERATED GUIDANCE'}),
          h('h3',{text:'A second opinion, grounded in your plan.'}),
          h(
            'p',
            {
              text:`${event.details.guest_count} guests · ${financialMoney(summary.projected_cost)} projected recorded cost. ${summary.missing_categories.length||summary.unknown_expenses.length?'Pricing is incomplete.':'Prices are recorded assumptions, not verified market data.'}`
            }
          )
        ),
        h('span',{class:'badge',text:'ADVICE NEVER APPLIES CHANGES'})
      );
    }
    const log = $("chat-log");
    clear(log);
    log.append(
      h(
        "div",
        {
          class: "msg ai",
          text: "Ask me anything about this plan, like where to save money, what to book first, or how to handle RSVPs."
        }
      )
    );
    if (state.workspace) for (const entry of state.workspace.chat) log.append(h("div",
    { class: entry.role === "user" ? "msg me" : "msg ai" },
    entry.text,
      entry.role === "assistant" ? h(
        "small", { class: "chat-source", text: entry.source === "gemini" ? "Gemini" : "Built-in planner" }
      ) : null));
    $("chat-error").hidden = true;
  }

  $("chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("chat-input");
    const q = input.value.trim();
    if (q.length < 2 || !state.lastRequest || state.workspaceBusy) return;
    const log = $("chat-log");
    const err = $("chat-error");
    err.hidden = true;
    const btn = $("chat-btn");
    btn.disabled = true;
    btn.textContent = "Thinking...";
    setWorkspaceBusy(true);
    try {
      const res = await api(
        `/api/events/${state.workspace.id}/chat`, { question: q, revision: state.workspace.revision }
      );
      applyWorkspace(await res.json(), true, true);
      input.value = "";
      workspaceStatus("Conversation saved.");
    } catch (ex) {
      err.textContent = ex.message;
      err.hidden = false;
    } finally {
      setWorkspaceBusy(false);
      btn.textContent = "Ask";
      input.focus();
    }
  });


return {resetChat};
}
