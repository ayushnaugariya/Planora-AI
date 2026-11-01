async function api(path, body, method = "POST", options = {}) {
    let res;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000);
    try {
      res = await fetch(
        path,
        {
          method,
          signal:controller.signal,
          cache:options.cache,
          headers: { "Content-Type": "application/json" },
          body: body === undefined ? undefined : JSON.stringify(body)
        }
      );
    } catch {
      if (controller.signal.aborted) throw new Error(
        options.timeoutMessage || "The server took too long. Reopen the event to confirm whether changes were saved before retrying."
      );
      throw new Error("Can't reach the server. Check your connection and try again.");
    } finally { clearTimeout(timeout); }
    if (res.ok) return res;
    let msg = "Something went wrong. Please try again.";
    if (res.status === 429) {
      msg = `Too many requests. Try again in ${res.headers.get("Retry-After") || "a few"} seconds.`;
    } else if (res.status === 422) {
      try {
        const data = await res.json();
        msg = (data.details || []).map((d) => `${d.field}: ${d.message}`).join(". ") || data.detail || data.error || "Some details need fixing.";
      } catch { /* keep default */ }
    } else if (res.status === 413) {
      msg = "That request is too large. Shorten your notes.";
    } else {
      try { const data = await res.json(); msg = data.error || data.detail || msg; } catch { /* keep default */ }
    }
    const error = new Error(msg); error.status = res.status; throw error;
  }
export {api};
