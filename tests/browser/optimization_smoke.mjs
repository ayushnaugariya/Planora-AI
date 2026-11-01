import assert from 'node:assert/strict';

export async function checkWizardKeyboard({evaluate,send,waitFor,click,values}) {
  const position=()=>evaluate("document.getElementById('wizard-position').textContent");
  async function enter() {
    await send('Input.dispatchKeyEvent',{
      type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'
    });
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
  }
  await click('#wizard-next');
  await evaluate("document.getElementById('wizard-back').focus()");
  await enter();
  assert.equal(await position(),'1 / 5','Enter on Back must move backward');
  assert(await evaluate("document.activeElement.matches('.wizard-stage:not([hidden]) h2')"),
    'Returning to step one must focus its visible heading');
  // An IME confirmation must not advance the form while text is being composed.
  await evaluate("document.getElementById('title').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true,cancelable:true}))");
  assert.equal(await position(),'1 / 5');
  await evaluate("document.getElementById('title').focus()");
  await enter();
  assert.equal(await position(),'2 / 5','Enter in a text field still advances');
  const date=await evaluate("document.getElementById('event_date').value");
  await values({event_date:''});await click('#wizard-next');
  assert.equal(await evaluate('document.activeElement.id'),'event_date');
  const invalid=await evaluate(`(()=>{
    const input=document.getElementById('event_date'),error=document.getElementById('form-error');
    return {invalid:input.getAttribute('aria-invalid'),message:input.validationMessage,
      errorText:error.textContent,errorVisible:!error.hidden,
      describesError:input.ariaDescribedByElements?.includes(error)};
  })()`);
  assert.equal(invalid.invalid,'true');
  assert(invalid.message,'The empty required date has a native validation error');
  assert(invalid.errorVisible&&invalid.describesError,'The invalid date refers to the visible error');
  assert.equal(invalid.errorText,invalid.message,'The error matches this date field validation failure');
  const field=(await send('Runtime.evaluate',{expression:"document.getElementById('event_date')"})).result;
  const {node}=await send('DOM.describeNode',{objectId:field.objectId});
  const tree=await send('Accessibility.getPartialAXTree',{
    objectId:field.objectId,fetchRelatives:false
  });
  const fieldNode=tree.nodes.find(item=>item.backendDOMNodeId===node.backendNodeId);
  assert(fieldNode&&!fieldNode.ignored,'The actual date field is exposed in the accessibility tree');
  assert.equal(fieldNode.description?.value,invalid.message,'The date field exposes its specific error');
  assert.equal(fieldNode.properties.find(item=>item.name==='invalid')?.value.value,'true');
  await values({event_date:date});
  assert(await evaluate("!document.getElementById('event_date').hasAttribute('aria-invalid')&&!document.getElementById('form-error').textContent"),
    'Correcting the input clears stale validation');
  await click('#wizard-back');
  assert.equal(await position(),'1 / 5');
  console.log('PASS wizard keyboard Back/implicit Enter/IME, visible step focus, associated validation in the browser accessibility tree and correction');
}

export async function checkVendorFocus({evaluate,send,waitFor,click,values,savedEvent,id}) {
  await click('#tab-vendors');
  await waitFor("!document.getElementById('panel-vendors').hidden");
  const before=await savedEvent(id),vendorIds=before.vendors.map(vendor=>vendor.id);
  assert(vendorIds.length>=2,'The regression must exercise the actual second vendor');
  for(const [index,vendorId] of vendorIds.entries()) {
    const editSelector=`#vendor-list [data-vendor-id="${vendorId}"]`;
    const section=`document.querySelector(${JSON.stringify(editSelector)}).closest('details')`;
    const summary=`${section}.querySelector('summary')`;
    // Establish the expected vendor and element before the save replaces the DOM.
    const expectedFocus=index===0?`document.querySelector(${JSON.stringify(editSelector)})`:summary;
    if(!await evaluate(`${section}.open`)) {
      await evaluate(`${summary}.focus()`);
      await send('Input.dispatchKeyEvent',{
        type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'
      });
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    }
    await click(editSelector);
    assert(await evaluate("document.getElementById('vendor-dialog').open"));
    const name=index===0?'Test garden venue':index===1?'Test catering contact':`Test vendor ${index+1}`;
    const contact=index===0?'venue@example.test':`vendor${index+1}@example.test`;
    await values({'vendor-edit-name':name,'vendor-edit-contact':contact,'vendor-edit-status':'booked'});
    await click('#vendor-edit-save');
    await waitFor("!document.getElementById('vendor-dialog').open&&!document.getElementById('submit-btn').disabled");
    await waitFor(`document.activeElement===${expectedFocus}`);
    assert(await evaluate(`document.activeElement!==document.body&&${expectedFocus}.isConnected&&
      ${expectedFocus}.matches('button,summary')&&${expectedFocus}.tabIndex>=0&&
      ${expectedFocus}.getClientRects().length>0`),'Focus is on the expected visible keyboard control');
    assert.equal(await evaluate(`${section}.open`),index===0,
      'Saving the second vendor closes its section while its summary remains focusable');
    const saved=(await savedEvent(id)).vendors.find(vendor=>vendor.id===vendorId);
    assert.equal(saved.name,name);assert.equal(saved.contact,contact);assert.equal(saved.booking_status,'booked');

    if(index!==0)await evaluate(`${summary}.click()`);
    await click(editSelector);
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await waitFor(`!document.getElementById('vendor-dialog').open&&document.activeElement===document.querySelector(${JSON.stringify(editSelector)})`);
    await click(editSelector);await click('#vendor-dialog-close');
    await waitFor(`!document.getElementById('vendor-dialog').open&&document.activeElement===document.querySelector(${JSON.stringify(editSelector)})`);
  }

  const editSelector=`#vendor-list [data-vendor-id="${vendorIds[1]}"]`;
  const summary=`document.querySelector(${JSON.stringify(editSelector)}).closest('details').querySelector('summary')`;
  if(!await evaluate(`document.querySelector(${JSON.stringify(editSelector)}).closest('details').open`)) {
    await evaluate(`${summary}.click()`);
  }
  // Re-edit a populated vendor as well as initially recording the contact details above.
  await click(editSelector);
  await values({'vendor-edit-contact':'updated-catering@example.test'});
  await click('#vendor-edit-save');
  await waitFor(`!document.getElementById('vendor-dialog').open&&!document.getElementById('submit-btn').disabled&&document.activeElement===${summary}`);
  assert.equal((await savedEvent(id)).vendors.find(vendor=>vendor.id===vendorIds[1]).contact,
    'updated-catering@example.test');
  assert.equal(await evaluate(`document.querySelector(${JSON.stringify(editSelector)}).closest('details').open`),false);
  await evaluate(`${summary}.click()`);
  await click(editSelector);
  await evaluate(`document.querySelector(${JSON.stringify(editSelector)}).hidden=true`);
  await click('#vendor-dialog-close');
  await waitFor(`!document.getElementById('vendor-dialog').open&&document.activeElement===${summary}`);
  await evaluate(`document.querySelector(${JSON.stringify(editSelector)}).hidden=false`);
  // If the opener has gone completely, the labelled tab panel is the deliberate fallback.
  const expectedFallback="document.getElementById('panel-vendors')";
  await click(editSelector);
  await evaluate(`document.querySelector(${JSON.stringify(editSelector)}).remove()`);
  await click('#vendor-dialog-close');
  await waitFor(`!document.getElementById('vendor-dialog').open&&document.activeElement===${expectedFallback}`);
  assert(await evaluate(`${expectedFallback}.getClientRects().length>0&&${expectedFallback}.tabIndex===0`));
  const after=await savedEvent(id);
  assert.deepEqual(after.details,before.details);assert.deepEqual(after.budget_summary,before.budget_summary);
  assert.deepEqual(after.tasks,before.tasks);
  // Restore the test-only DOM removal from authoritative saved data.
  await send('Page.reload');
  await waitFor("document.getElementById('workspace-status')?.textContent.startsWith('Opened saved event')&&!document.getElementById('submit-btn').disabled");
  await waitFor("!document.getElementById('panel-vendors').hidden");
  console.log(`PASS first/second/all ${vendorIds.length} vendor saves restore predetermined visible targets, closed-section summary, exact saved/re-edited data, Escape/Close and hidden/removed-opener fallbacks`);
}
