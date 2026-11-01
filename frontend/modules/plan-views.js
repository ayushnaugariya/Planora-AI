import {state} from './state.js';
import {$,h,clear,store,fmtDate,money,financialMoney} from './helpers.js';
export function mountPlanViews({saveProgress}) {
function renderHealth(plan) {
    const s = plan.health_score;
    const meter = $("health-meter");
    const word = s >= 75 ? "Strong" : s >= 50 ? "Needs attention" : "At risk";
    $("health-value").textContent = `${s}/100 · ${word}`;
    meter.setAttribute("aria-valuenow", String(s));
    meter.setAttribute("aria-valuetext", `${s} out of 100, ${word}`);
    meter.className = "meter" + (s >= 75 ? "" : s >= 50 ? " mid" : " low");
    $("health-fill").style.width = s + "%";
  }

  function renderWarnings(list) {
    const ul = $("warnings");
    clear(ul);
    const label = { info: "Good news:", warn: "Heads up:", risk: "Risk:" };
    for (const w of list) ul.append(h("li", { class: w.level }, h("b", { text: label[w.level] }), w.message));
  }

  function renderBudget(plan) {
    const bunting = $("bunting");
    clear(bunting);
    const body = $("budget-table").tBodies[0];
    clear(body);
    const foot = $("budget-table").tFoot;
    clear(foot);

    plan.budget_lines.forEach((line, i) => {
      const cls = "c" + (i % 10);
      if (line.amount > 0) {
        const p = h("div", { class: "pennant " + cls, title: `${line.label}: ${money(line.amount)}` });
        p.style.flexGrow = String(line.amount);
        if (line.percent >= 9) p.textContent = Math.round(line.percent) + "%";
        bunting.append(p);
      }
      body.append(
        h("tr", {},
          h("td", {},
            h("span", { class: "swatch " + cls, "aria-hidden": "true" }),
            line.label,
            line.priority ? h("span", { class: "badge", text: "Priority" }) : null,
            line.tip ? h("span", { class: "tip", text: line.tip }) : null),
          h("td", { class: "num", text: money(line.amount) }),
          h("td", { class: "num", text: line.percent.toFixed(1) + "%" }),
          h(
            "td",
            {
              class: "num",
              text: financialMoney(
                state.workspace.budget_summary.categories.find((category) => category.key === line.key).per_guest_allocation
              )
            }
          )));
    });
    foot.append(h("tr", {},
      h("td", { text: "Allocated" }),
      h("td", { class: "num", text: money(state.workspace.budget_summary.planned_allocation) }),
      h("td", { class: "num", text: "" }),
      h("td", { class: "num", text: financialMoney(state.workspace.budget_summary.planned_per_guest) })));
  }

  function planKey(plan) { return `${plan.event_type}|${plan.event_date}|${plan.title}`; }

  function renderTimeline(plan) {
    const key = "eventra:done:" + planKey(plan);
    const done = new Set(
      state.workspace ? state.workspace.tasks.filter((t) => t.completed).map((t) => t.milestone_index) : store.get(
        key, []
      )
    );
    const ol = $("timeline-list");
    clear(ol);
    const total = plan.timeline.filter((m) => m.category !== "event").length;

    function updateProgress() {
      const n = [...done].filter((i) => plan.timeline[i] && plan.timeline[i].category !== "event").length;
      $("timeline-progress").textContent = `${n} of ${total} steps done`;
    }

    plan.timeline.forEach((m, i) => {
      const isEvent = m.category === "event";
      const rel = m.days_before_event === 0 ? "Event day" : `${m.days_before_event} day${m.days_before_event === 1 ? "" : "s"} before`;
      const text = [
        h("span", { class: "when", text: `${fmtDate(m.due)} · ${rel}` }),
        h("span", { class: "what", text: m.title }),
        m.note ? h("span", { class: "note", text: m.note }) : null,
      ];
      const li = h("li", { class: (isEvent ? "event " : "") + (done.has(i) ? "done" : "") });
      if (isEvent) {
        li.append(h("div", {}, text));
      } else {
        const cb = h("input", { type: "checkbox", checked: done.has(i) });
        cb.addEventListener("change", async () => {
          if (state.workspace) {
            await saveProgress(cb, state.workspace.tasks.find((t) => t.milestone_index === i).id, true);
            return;
          }
          if (cb.checked) done.add(i); else done.delete(i);
          li.classList.toggle("done", cb.checked);
          store.set(key, [...done]);
          updateProgress();
        });
        li.append(h("label", {}, cb, h("div", {}, text)));
      }
      ol.append(li);
    });
    updateProgress();
  }

  function renderVendors(plan) {
    const root = $("vendor-list");
    clear(root);
    const key = "eventra:vendor:" + planKey(plan);
    const done = new Set(
      state.workspace ? state.workspace.vendors.flatMap(
        (v) => v.checklist.filter((c) => c.completed).map(
          (c) => `${plan.vendors[v.group_index].key}:${c.item_index}`
        )
      ) : store.get(key, [])
    );
    plan.vendors.forEach((v, vi) => {
      const checks = h("ul", { class: "checks" });
      v.checklist.forEach((item, ci) => {
        const id = `${v.key}:${ci}`;
        const cb = h("input", { type: "checkbox", checked: done.has(id) });
        cb.addEventListener("change", async () => {
          if (state.workspace) {
            const vendor = state.workspace.vendors.find((item) => item.group_index === vi);
            await saveProgress(cb, vendor.checklist.find((item) => item.item_index === ci).id, false); return;
          }
          if (cb.checked) done.add(id); else done.delete(id);
          store.set(key, [...done]);
        });
        checks.append(h("li", {}, h("label", {}, cb, h("span", { text: item }))));
      });
      const list = (arr, cls) => h("ul", { class: cls || "" }, arr.map((t) => h("li", { text: t })));
      root.append(
        h("details", { open: vi === 0 },
          h("summary", {},
            h("span", { class: "v-name", text: v.label }),
            h(
              "span",
              {
                class: "badge",
                text: state.workspace?.vendors.find((item) => item.group_index === vi)?.booking_status || "Status not recorded"
              }
            ),
            h("span", { class: "v-by", text: `Book by ${fmtDate(v.book_by)} · budget ${money(v.budget)}` })),
          h("div", { class: "vendor-body" },
            state.workspace ? h('div', {class:'vendor-record'},
              h(
                'p',
                {},
                state.workspace.vendors[vi].name || 'Contact not recorded',
                h(
                  'small',
                  {text:state.workspace.vendors[vi].contact || 'Add contact details and booking status'}
                )
              ),
              h(
                'button',
                {
                  type:'button',
                  class:'ghost',
                  'data-vendor-id':state.workspace.vendors[vi].id,
                  text:'Edit vendor details'
                }
              )) : null,
            h("div", {}, h("h4", { text: "Checklist" }), checks),
            h("div", {},
              h("h4", { text: "Questions to ask" }), list(v.ask),
              h("h4", { text: "Walk away if" }), list(v.red_flags, "flag")))));
    });
  }

  function renderIdeas(plan) {
    const ul = $("idea-list");
    clear(ul);
    for (const idea of plan.ideas) {
      ul.append(
        h(
          "li",
          {},
          h("strong", { text: idea.title }),
          h("span", { text: idea.description }),
          h("span", { class: "cat", text: " " + idea.category })
        )
      );
    }
    const tips = $("tip-list");
    clear(tips);
    for (const t of plan.tips) tips.append(h("li", { text: t }));
  }
return {renderHealth,renderWarnings,renderBudget,renderTimeline,renderVendors,renderIdeas};
}
