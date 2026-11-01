const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
const counters=new WeakMap();

export function mountMotion() {
  document.addEventListener('planora:status',event=>{
    if(event.detail.origin!=='scenario')return;
    const status=document.getElementById('rescue-action-status');
    if(status)status.dataset.tone=event.detail.error?'error':event.detail.message==='Scenario applied and saved.'?'success':'neutral';
  });
  if (reduced.matches || !('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) if (entry.isIntersecting) {
      entry.target.classList.add('reveal-in');
      observer.unobserve(entry.target);
    }
  }, {threshold: 0.08});
  document.querySelectorAll('[data-reveal]').forEach((element) => observer.observe(element));
}

export function countTo(element, value, format, {from='0'}={}) {
  cancelAnimationFrame(counters.get(element));
  const target = Number(value);
  const initial=Number(from);
  const finish=()=>{element.textContent=format(value);counters.delete(element);};
  element.setAttribute('aria-label',format(value));
  if (reduced.matches || !Number.isFinite(target)||!Number.isFinite(initial)||target===initial) {
    finish(); return;
  }
  const start = performance.now();
  const tick = (now) => {
    if(!element.isConnected){counters.delete(element);return;}
    if(reduced.matches||document.hidden){finish();return;}
    const progress = Math.min(1, (now - start) / 650);
    element.textContent = progress === 1 ? format(value) : format(
      String(Math.round(initial+(target-initial) * (1 - (1 - progress) ** 3)))
    );
    if (progress < 1) counters.set(element,requestAnimationFrame(tick));
    else counters.delete(element);
  };
  counters.set(element,requestAnimationFrame(tick));
}
