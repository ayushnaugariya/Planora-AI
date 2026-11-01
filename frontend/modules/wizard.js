import {$, h, clear, fmtDate} from './helpers.js';
import {state} from './state.js';

export function mountWizard({readForm, showFormError}) {
  const form = $('plan-form');
  const original = [...form.children];
  const steps = ['The occasion', 'When & where', 'The essentials', 'Make it yours', 'Review your event'];
  const groups = steps.map((title, index) => {
    const group = h('section', {class: 'wizard-stage', 'data-step': index, hidden: index !== 0});
    group.append(
      h('p', {class: 'eyebrow', text: `STEP ${index + 1} OF ${steps.length}`}),
      h('h2', {text: title,tabIndex:-1})
    );
    form.append(group);
    return group;
  });
  for (const child of original) {
    if (child.id === 'form-error' || child.id === 'submit-btn') continue;
    let index = 3;
    if (child.querySelector('[name="event_type"]') || child.querySelector('#title')) index = 0;
    else if (child.querySelector('#event_date') || child.querySelector('#city')) index = 1;
    else if (
      child.querySelector('#budget') || child.querySelector('#formality') || child.querySelector(
        '[name="priorities"]'
      )
    ) index = 2;
    groups[index].append(child);
  }
  const review = h('dl', {class: 'review-grid', id: 'wizard-review'});
  groups[4].append(review);
  const back = h('button', {type: 'button', class: 'ghost', id: 'wizard-back', text: 'Back'});
  const next = h('button', {type: 'button', class: 'primary', id: 'wizard-next', text: 'Continue'});
  const footer = h('div', {class: 'wizard-actions'}, back, next, $('submit-btn'));
  form.append($('form-error'), footer);
  $('budget').step = '1';
  const maximum = new Date(); maximum.setDate(maximum.getDate() + 1095);
  $('event_date').max = [
    maximum.getFullYear(),
    String(maximum.getMonth()+1).padStart(2,'0'),
    String(maximum.getDate()).padStart(2,'0')
  ].join('-');
  let active = 0, invalidInput = null, previousDescription = null;
  function clearValidation() {
    if (invalidInput) {
      invalidInput.removeAttribute('aria-invalid');
      if (previousDescription === null) invalidInput.removeAttribute('aria-describedby');
      else invalidInput.setAttribute('aria-describedby', previousDescription);
      invalidInput = null;
    }
    showFormError('');
  }
  function clearCorrectedField(event) {
    if (event.target === invalidInput && invalidInput.checkValidity()) clearValidation();
  }
  form.addEventListener('input', clearCorrectedField);
  form.addEventListener('change', clearCorrectedField);
  function render() {
    groups.forEach((group, index) => { group.hidden = index !== active; });
    back.hidden = active === 0;
    next.hidden = active === 4;
    $('submit-btn').hidden = active !== 4;
    $('wizard-progress').value = active + 1;
    $('wizard-position').textContent = `${active + 1} / ${steps.length}`;
    $('wizard-mode').textContent = state.workspace ? 'Refine your saved event' : 'A little detail. A remarkable day.';
    if (active === 4) {
      const data = readForm(); clear(review);
      for (
        const [label, value] of [
          ['Occasion', data.title || data.event_type.replaceAll('_',' ')],
          ['When', data.event_date ? fmtDate(data.event_date) : 'Choose a date'],
          ['Where', data.city || 'Location to confirm'],
          ['Guests', String(data.guest_count)],
          ['Budget', `${data.budget.toLocaleString()} ${data.currency}`],
          ['Priorities', data.priorities.join(', ') || 'Balanced allocation'],
          ['Theme', data.theme || 'Your own style']
        ]
      ) review.append(h('div', {}, h('dt',{text:label}), h('dd',{text:value})));
    }
  }
  function valid() {
    clearValidation();
    for (const input of groups[active].querySelectorAll('input,select,textarea')) {
      if (!input.disabled && !input.checkValidity()) {
        invalidInput = input;
        previousDescription = input.getAttribute('aria-describedby');
        const descriptions = new Set((previousDescription || '').split(/\s+/).filter(Boolean));
        descriptions.add('form-error');
        input.setAttribute('aria-describedby', [...descriptions].join(' '));
        showFormError(input.validationMessage || 'Please check this field.');
        input.setAttribute('aria-invalid', 'true'); input.focus(); return false;
      }
      input.removeAttribute('aria-invalid');
    }
    return true;
  }
  function moveTo(index) {
    clearValidation();
    active = index;
    render();
    groups[active].querySelector('h2').focus();
  }
  next.addEventListener(
    'click',
    () => {
      if (valid()) {
        moveTo(Math.min(4, active + 1));
      }
    }
  );
  back.addEventListener('click', () => moveTo(Math.max(0, active - 1)));
  form.addEventListener('keydown', (event) => {
    if (
      event.key === 'Enter' && !event.isComposing && !event.defaultPrevented && active < 4 &&
      event.target.matches('input') && [
        'text','search','email','url','tel','password','number','date','time','datetime-local','month','week'
      ].includes(event.target.type)
    ) {
      event.preventDefault(); next.click();
    }
  });
  render();
  return {
    open() {clearValidation(); active = 0; render();},
    review() {clearValidation(); active = 4; render();}
  };
}
