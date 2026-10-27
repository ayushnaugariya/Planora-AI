import {state} from './state.js';
  const $ = (id) => document.getElementById(id);

  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k in el && k !== "list") el[k] = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) {
      if (kid === null || kid === undefined || kid === false) continue;
      el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    }
    return el;
  }

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ }
    },
  };

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function isoLocal(d) {
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }
  function parseDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  function fmtDate(iso) {
    return parseDate(iso).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  }
  let money = (n) => String(n);
  function setCurrency(code) {
    try {
      const f = new Intl.NumberFormat(undefined, { style: "currency", currency: code, maximumFractionDigits: 0 });
      money = (n) => f.format(n);
    } catch { money = (n) => `${code} ${Math.round(n)}`; }
  }
  function financialMoney(value, currency = state.workspace.details.currency) {
    if (value === null || value === undefined) return "Unknown";
    const text = String(value), negative = text.startsWith("-");
    const [whole, fraction = ""] = (negative ? text.slice(1) : text).split(".");
    const units = BigInt(whole);
    const negativeFraction = negative && units === 0n;
    const formatter = new Intl.NumberFormat(undefined, { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return formatter.formatToParts(negativeFraction ? -1n : negative ? -units : units).map((part) => {
      if (part.type === "fraction") return fraction.padEnd(2, "0").slice(0, 2);
      if (part.type === "integer" && negativeFraction) return "0";
      return part.value;
    }).join("");
  }
export {$,h,clear,store,reduceMotion,isoLocal,parseDate,fmtDate,money,setCurrency,financialMoney};
