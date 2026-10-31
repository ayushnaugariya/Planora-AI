import {h,clear} from './helpers.js';

export const artwork={botanical:'/static/assets/botanical.svg',celebration:'/static/assets/celebration.svg',venue:'/static/assets/venue-lattice.svg'};
export const themeNames={ethereal:'Ethereal',modern_minimal:'Modern Minimal',celebration:'Celebration',editorial_luxe:'Editorial Luxe'};

export function renderEventSite(root,data,{preview=false,onRSVP=null}={}){
  clear(root);root.className='event-site';root.dataset.theme=data.theme;
  const accent=/^#[0-9a-f]{6}$/i.test(data.accent)?data.accent:'#7863b4';
  const rgb=[1,3,5].map(i=>parseInt(accent.slice(i,i+2),16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);
  const light=rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
  // Validated color tokens through CSSOM, no HTML/style template interpolation.
  root.style.setProperty('--invite-accent',accent);root.style.setProperty('--invite-on-accent',light>.179?'#000000':'#ffffff');
  const date=iso=>{const [y,m,d]=iso.split('-').map(Number);return new Date(y,m-1,d).toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long',year:'numeric'});};
  const when=iso=>new Intl.DateTimeFormat(undefined,{dateStyle:'long',timeStyle:'short',timeZone:data.timezone}).format(new Date(iso));
  const hero=h('header',{class:'invite-hero'},h('div',{class:'invite-monogram','aria-hidden':'true',text:'✦'}),h('p',{class:'invite-eyebrow',text:data.welcome}),h('h1',{text:data.title}),data.subtitle?h('p',{class:'invite-subtitle',text:data.subtitle}):null,h('p',{class:'invite-date',text:data.start_at?`${when(data.start_at)} · ${data.timezone}`:date(data.event_date)}));
  if(artwork[data.cover])hero.append(h('img',{class:'invite-cover',src:artwork[data.cover],alt:'Decorative event illustration',width:960,height:640}));
  const countdown=h('p',{class:'invite-countdown',role:'timer','aria-label':'Time until the event'});
  hero.append(countdown);root.append(hero);
  const contents=h('main',{class:'invite-content'});
  const section=(title,...kids)=>h('section',{class:'invite-section'},h('p',{class:'invite-eyebrow',text:title}),...kids);
  contents.append(section('The invitation',h('h2',{text:'A moment worth sharing.'}),h('p',{class:'invite-message',text:data.invitation}),data.description?h('p',{text:data.description}):null));
  if(data.hosts)contents.append(section('Your hosts',h('h2',{text:data.hosts})));
  if(data.venue){const v=data.venue;contents.append(section('The setting',h('h2',{text:v.name||'Venue details'}),h('p',{text:[v.address,v.city].filter(Boolean).join(' · ')||'The host has not added an address.'})));}
  if(data.schedule.length){const list=h('ol',{class:'invite-schedule'});for(const item of data.schedule)list.append(h('li',{},h('time',{dateTime:item.start_at||item.date,text:item.start_at?when(item.start_at):date(item.date)}),h('h3',{text:item.title})));contents.append(section('The occasion, unfolding',h('h2',{text:'A little plan for the day.'}),list));}
  if(data.dress_code)contents.append(section('What to wear',h('h2',{text:'Come as the occasion calls.'}),h('p',{text:data.dress_code})));
  if(data.gallery.length){const gallery=h('div',{class:'invite-gallery'});for(const key of data.gallery)if(artwork[key])gallery.append(h('img',{src:artwork[key],alt:`${key} event illustration`,loading:'lazy',width:480,height:360}));contents.append(section('A little inspiration',h('h2',{text:'The feeling of the day.'}),gallery));}
  if(data.rsvp.enabled){
    const field=(text,input)=>h('label',{class:'invite-field',htmlFor:input.id},h('span',{text}),input);
    const name=h('input',{id:'invite-name',name:'name',maxLength:100,required:true,autocomplete:'name'}),email=h('input',{id:'invite-email',name:'email',type:'email',maxLength:254,required:data.rsvp.email_required,autocomplete:'email'});
    const rsvp=h('select',{id:'invite-response',name:'rsvp'},['confirmed','declined','maybe','pending'].map(value=>h('option',{value,text:{confirmed:'Joyfully attending',declined:'Unable to attend',maybe:'Still deciding',pending:'Response pending'}[value]})));
    const count=h('input',{id:'invite-attendees',name:'attendees',type:'number',min:1,max:data.rsvp.max_attendees,step:1,value:1,required:true}),diet=h('textarea',{id:'invite-dietary',name:'dietary',maxLength:300,rows:2}),message=h('textarea',{id:'invite-message',name:'message',maxLength:400,rows:2});
    const submit=h('button',{type:'submit',class:'invite-button',text:preview?'RSVP preview — not submitted':'Send my response'});
    const status=h('p',{id:'invite-response-status',role:'status'}),error=h('p',{id:'invite-response-error',class:'invite-error',role:'alert',hidden:true});
    const fields=h('fieldset',{disabled:preview},h('legend',{class:'invite-sr',text:'Your response'}),h('div',{class:'invite-fields'},field('Your name',name),field(data.rsvp.email_required?'Email (required)':'Email (optional)',email),field('Your response',rsvp),field(`Party size including you (1–${data.rsvp.max_attendees})`,count)),field('Dietary requirements (optional)',diet),field('Message to the host (optional)',message),submit);
    const form=h('form',{id:'invite-rsvp-form'},fields,status,error);
    let requestId=null;
    form.addEventListener('input',()=>{requestId=null;});
    form.addEventListener('submit',async event=>{event.preventDefault();if(preview||!onRSVP)return;error.hidden=true;fields.disabled=true;submit.textContent='Sending…';
      const body={request_id:requestId||(requestId=crypto.randomUUID()),edition:data.edition,name:name.value,email:email.value,rsvp:rsvp.value,attendees:Number(count.value),dietary:diet.value,message:message.value};
      try{const result=await onRSVP(body);status.textContent=result.message;submit.textContent='Response received';}
      catch(ex){error.textContent=ex.message;error.hidden=false;fields.disabled=false;submit.textContent='Try sending again';}
    });
    contents.append(section('We saved you a little space',h('h2',{text:'Will you join us?'}),h('p',{text:data.rsvp.instructions}),h('p',{class:'invite-note',text:'Your response is private to the host. Party size includes you, even for a declined invitation. This form cannot change an earlier response; contact the host for corrections.'}),form));
  }
  root.append(contents,h('footer',{class:'invite-footer'},h('span',{text:'Thoughtfully brought together with Planora AI'}),h('a',{href:'/',text:'Plan your own occasion →'})));
  function tick(){if(!data.start_at){countdown.textContent='Save the date · The host has not specified a start time.';return;}const remaining=new Date(data.start_at).getTime()-Date.now();if(remaining<=0){countdown.textContent='The occasion has begun · We hope it is a wonderful day.';return;}const seconds=Math.floor(remaining/1000);countdown.textContent=`${Math.floor(seconds/86400)} days · ${Math.floor(seconds/3600)%24} hours · ${Math.floor(seconds/60)%60} minutes to go`;}
  tick();const timer=data.start_at?setInterval(()=>{if(!document.hidden)tick();},1000):null;
  return ()=>{if(timer)clearInterval(timer);};
}
