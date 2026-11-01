import {renderEventSite} from './modules/event-site-renderer.js';
import {api} from './modules/api.js';

const root=document.getElementById('public-event'),
loading=document.getElementById('invitation-loading'),
error=document.getElementById('invitation-error'),
retry=document.getElementById('invitation-retry'),
print=document.getElementById('invitation-print');
const slug=location.pathname.split('/').filter(Boolean).at(-1);
const endpoint=`/api/public/websites/${encodeURIComponent(slug)}`;
let dispose=null,edition=null,busy=false,refreshing=false;
async function submit(body){
  busy=true;
  try{
    return await(
      await api(
        endpoint+'/rsvp',
        body,
        'POST',
        {
          cache:'no-store',
          timeoutMessage:'Your response timed out. Retry with the same details, or contact the host to confirm whether it was received.'
        }
      )
    ).json();
  }finally{busy=false;}
}
async function load(){
  if(refreshing||busy)return;
  refreshing=true;
  try{
    const data=await(
      await api(
        endpoint,
        undefined,
        'GET',
        {
          cache:'no-store',
          timeoutMessage:'This invitation timed out. Displayed details may be out of date; retry before responding.'
        }
      )
    ).json();
    if(edition!==data.edition){
      const updated=edition!==null;
      dispose?.();
      dispose=renderEventSite(root,data,{onRSVP:submit});
      edition=data.edition;
      document.title=`${data.title} · Planora AI`;
      if(updated){
        loading.textContent='The host updated this invitation. Review the new details before responding.';
        loading.hidden=false;
      }else loading.hidden=true;
    }error.hidden=true;
    retry.hidden=true;
    print.hidden=false;
  }catch(ex){
    if(ex.status===404){
      dispose?.();
      dispose=null;
      root.replaceChildren();
      edition=null;
      print.hidden=true;
      document.title='Invitation unavailable · Planora AI';
    }error.textContent=ex.status===404?'This invitation is not currently available. Contact the host.':ex.message;
    error.hidden=false;
    retry.hidden=false;
    if(!edition)loading.hidden=true;
  }finally{refreshing=false;}
}
retry.addEventListener('click',load);print.addEventListener('click',()=>window.print());
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load();});
setInterval(()=>{if(!document.hidden)load();},15000);
load();
