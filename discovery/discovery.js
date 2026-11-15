(() => {
  'use strict';
  const root = document.createElement('section'); root.id = 'discovery-feature'; document.body.append(root);
  const sources = ['https://spinoff.nasa.gov/Spinoff2020/ip_5.html','https://www.nasa.gov/missions/station/studying-combustion-and-fire-safety/','https://spinoff.nasa.gov/node/9407','https://spinoff.nasa.gov/node/9918','https://spinoff.nasa.gov/node/9582'];
  const objects = [
    {name:'Extinguisher',color:'#ed997e',shape:'<rect x="25" y="29" width="29" height="47" rx="10"/><path d="M33 29V17h17M37 17l15-6M50 20q19 0 17 22l-4 14M28 43h23M34 52h11M36 59h7"/>',facts:[
      ['No up. No down. Still a mist.','NASA and ADA Technologies developed a fine-water-mist extinguisher design that can discharge in any orientation in microgravity.','Spacecraft equipment must work without relying on gravity.',0,'NASA Spinoff · 2020'],
      ['A tiny valve, an Earth connection','The spacecraft extinguisher project adapted an existing zero-leak valve. NASA’s Spinoff account describes its wider industrial applications.','The Earth connection includes component improvements—not the invention of all water-mist extinguishers.',0,'NASA Spinoff · 2020'],
      ['Reach behind the rack','The design described in NASA’s 2020 account includes a wand extension for reaching fires behind instrument racks or walls.','Equipment layout matters when engineers design suppression tools.',0,'NASA Spinoff · 2020']]},
    {name:'Microgravity flame',color:'#8cd7f7',shape:'<circle cx="44" cy="45" r="27"/><path d="M30 52c-8-16 15-24 16-33 19 19 18 43-2 46-9 1-16-4-14-13Z"/><path d="M39 54q-2-10 7-16 10 17-2 21"/>',facts:[
      ['A rounder kind of flame','In microgravity, flames can become spherical instead of taking the familiar candle-like shape seen on Earth.','Removing buoyancy helps scientists isolate other influences on combustion.',1,'NASA · Combustion and fire safety'],
      ['Fire is a research tool','NASA studies combustion aboard the station to understand burning and improve fire safety in space.','Controlled experiments help researchers build better physical models.',1,'NASA · Combustion and fire safety']]},
    {name:'Smoke detector',color:'#c9b4ff',shape:'<ellipse cx="44" cy="31" rx="30" ry="14"/><path d="M14 31v17c0 22 60 22 60 0V31M27 49h6m6 3h10m6-3h6"/><circle cx="44" cy="31" r="4"/>',facts:[
      ['Dust is not a fire','NASA’s 1978 Spinoff account describes a detector that distinguished combustion particles from dust to reduce false alarms.','Detection is also about recognizing what is not a fire.',2,'NASA Spinoff · 1978 · Historical'],
      ['A network that locates trouble','The same 1978 account describes connecting multiple sensors to a central display to locate an emerging fire in a large area.','Sensors become more useful when their locations are part of the information.',2,'NASA Spinoff · 1978 · Historical']]},
    {name:'Protective clothing',color:'#e9c57a',shape:'<path d="m28 19 10-5h12l10 5 16 22-12 9-6-9v35H29V41l-6 9-12-9Z"/><path d="m38 14 6 12 6-12M44 26v50M29 57h29M29 63h29"/>',facts:[
      ['Apollo ideas, firefighter gear','Project FIRES applied Apollo-derived materials and design concepts to firefighter protective equipment. NASA described the work in 1982.','Space technology can inform protective clothing on Earth.',3,'NASA Spinoff · 1982 · Historical'],
      ['Protection, tested in the field','NASA’s 1982 account describes fourteen municipal fire departments participating in evaluations of the FIRES ensemble.','Real-world evaluation connects materials research with the needs of firefighters.',3,'NASA Spinoff · 1982 · Historical']]},
    {name:'Air tank',color:'#91dbb8',shape:'<rect x="28" y="23" width="31" height="54" rx="13"/><path d="M38 23V12h12v11M34 12h20M28 40h31M28 60h31M59 33q14 0 12 22l-5 8"/>',facts:[
      ['Less weight on their shoulders','NASA’s 1976 account describes a firefighter air-supply backpack developed with Johnson Space Center that weighed 13 pounds less than conventional equipment of that era.','Lower equipment weight was a concrete benefit of this historical collaboration.',4,'NASA Spinoff · 1976 · Historical'],
      ['A tank with a layered structure','The 1976 design used an aluminum liner wrapped in resin-impregnated glass fibers.','Composite construction helped lighten the air tank.',4,'NASA Spinoff · 1976 · Historical']]},
    {name:'Engine & energy',color:'#edb1d4',shape:'<path d="M20 29h41v38H20zM28 29V18h22v11M61 40h12v20H61M11 38h9M11 56h9"/><circle cx="41" cy="48" r="10"/><path d="m43 36-7 14h9l-6 12"/>',facts:[
      ['Space research, Earth questions','NASA links combustion research in space with efforts to improve combustion efficiency and reduce pollutants on Earth.','The benefit is better understanding for future technology—not a measured energy saving from this app.',1,'NASA · Combustion and fire safety'],
      ['A laboratory without the usual rise','Microgravity gives researchers a different environment for studying combustion processes.','Comparing behavior across environments can help refine combustion models.',1,'NASA · Combustion and fire safety']]}
  ];
  const icon = o => `<svg viewBox="0 0 88 88" aria-hidden="true" fill="${o.color}22" stroke="${o.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">${o.shape}</svg>`;
  root.innerHTML = `<details class="df-test"><summary>Discovery prototype <span id="df-status">Waiting · 10s</span></summary><p>Dashboard test controls</p><label><input id="df-sim" type="checkbox"> Simulation running</label><button id="df-reset">Replay 10-second arrival</button><small>Dashboard content is a copy of the existing static mockup.</small></details><button class="df-discover" id="df-discover">✧ Discover <span>Space → Earth</span></button><aside id="df-prompt" hidden aria-label="Discover a space science fact"><span class="df-eyebrow">A little space knowledge</span><button id="df-object"></button><button id="df-dismiss" aria-label="Dismiss discovery prompt" hidden>×</button><span class="df-hint">Click to discover</span></aside><dialog id="df-dialog" aria-labelledby="df-title"><button id="df-close" aria-label="Close discoveries">×</button><div class="df-heading"><span class="df-eyebrow">GHOSTFLAME / DISCOVER</span><h2 id="df-title">Small discoveries.<br>Earth-sized possibilities.</h2><p>Pick an object. Find a new connection.</p></div><div id="df-tray" role="group" aria-label="Discovery topics"></div><article id="df-card" aria-live="polite"></article><footer>Curated facts · Official sources · Illustrations, not a simulation</footer></dialog>`;
  const el = id => document.getElementById('df-'+id);
  let progress={};try {progress=JSON.parse(localStorage.getItem('gf-discovery-v1')||'{}')||{};}catch{}
  let remaining=10000,sim=false,shown=false,dismissed=false,active=0,lastTick=performance.now(),jiggleTimer;
  try{dismissed=sessionStorage.getItem('gf-discovery-dismissed')==='1';}catch{}
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function nextFact(i){
    const n=objects[i].facts.length; let p=progress[i];
    if(!p||!Array.isArray(p.bag)||p.bag.some(x=>!Number.isInteger(x)||x<0||x>=n))p={bag:[],last:-1};
    if(!p.bag.length){p.bag=Array.from({length:n},(_,j)=>j);for(let j=n-1;j>0;j--){const k=Math.floor(Math.random()*(j+1));[p.bag[j],p.bag[k]]=[p.bag[k],p.bag[j]];}if(p.bag[0]===p.last)[p.bag[0],p.bag[1]]=[p.bag[1],p.bag[0]];}
    const index=p.bag.shift();p.last=index;progress[i]=p;try{localStorage.setItem('gf-discovery-v1',JSON.stringify(progress));}catch{}return index;
  }
  function fact(i){active=i;const o=objects[i],index=nextFact(i),f=o.facts[index];
    el('card').innerHTML=`<div class="df-art" style="--object-color:${o.color}">${icon(o)}<span>${o.name}</span></div><div class="df-copy"><span class="df-eyebrow">${o.name} · Fact ${index+1} of ${o.facts.length}</span><h3>${f[0]}</h3><p>${f[1]}</p><div class="df-why"><b>Why it matters</b><p>${f[2]}</p></div><a href="${sources[f[3]]}" target="_blank" rel="noopener noreferrer">${f[4]} ↗</a><button id="df-next">Another discovery →</button></div>`;
    el('next').onclick=()=>fact(active);el('tray').querySelectorAll('button').forEach((b,j)=>b.setAttribute('aria-pressed',j===i));
  }
  el('tray').innerHTML=objects.map((o,i)=>`<button data-topic="${i}" aria-pressed="false">${icon(o)}<span>${o.name}</span></button>`).join('');
  el('tray').onclick=e=>{const b=e.target.closest('[data-topic]');if(b)fact(+b.dataset.topic);};
  function open(){if(sim)return;fact(active);el('dialog').showModal();}
  el('discover').onclick=open;el('object').onclick=open;el('close').onclick=()=>el('dialog').close();
  el('dialog').onclick=e=>{if(e.target===el('dialog')){const r=el('dialog').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)el('dialog').close();}};
  function reveal(){shown=true;active=Math.floor(Math.random()*objects.length);el('object').innerHTML=icon(objects[active]);el('object').setAttribute('aria-label','Discover: '+objects[active].name);el('prompt').hidden=false;el('dismiss').hidden=!reduced.matches;el('object').classList.toggle('df-jiggle',!reduced.matches);clearTimeout(jiggleTimer);jiggleTimer=setTimeout(()=>{el('dismiss').hidden=false;el('object').classList.remove('df-jiggle');},reduced.matches?0:1800);}
  el('dismiss').onclick=()=>{dismissed=true;el('prompt').hidden=true;try{sessionStorage.setItem('gf-discovery-dismissed','1');}catch{}};
  function setSimulationRunning(value){sim=!!value;el('sim').checked=sim;el('discover').disabled=sim;if(sim){el('prompt').hidden=true;el('dialog').close();}else if(shown&&!dismissed){el('prompt').hidden=false;el('dismiss').hidden=false;}lastTick=performance.now();}
  el('sim').onchange=e=>setSimulationRunning(e.target.checked);
  el('reset').onclick=()=>{remaining=10000;shown=false;dismissed=false;el('prompt').hidden=true;clearTimeout(jiggleTimer);el('object').classList.remove('df-jiggle');try{sessionStorage.removeItem('gf-discovery-dismissed');}catch{}lastTick=performance.now();};
  document.addEventListener('visibilitychange',()=>{lastTick=performance.now();});
  setInterval(()=>{const now=performance.now(),dt=now-lastTick;lastTick=now;if(!sim&&!document.hidden&&!shown&&!dismissed&&!el('dialog').open){remaining=Math.max(0,remaining-dt);if(remaining===0)reveal();}el('status').textContent=sim?'Paused · simulation':dismissed?'Dismissed for this visit':shown?'Discovery ready':`Waiting · ${Math.ceil(remaining/1000)}s`;},100);
  window.ghostflameDiscovery={setSimulationRunning};
  window.addEventListener('ghostflame:simulation',e=>setSimulationRunning(e.detail?.running));
})();
