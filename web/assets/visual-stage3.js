/* Pelican Workbench V3.4 — Living Office visual layer
   Presentation-only: reads existing DOM values and user activity. No API, DB, or business logic changes. */
(function(){
  const scene=document.getElementById('scene');
  if(!scene) return;
  const q=id=>document.getElementById(id);
  const num=id=>{ const t=q(id)?.textContent||''; const m=t.replace(/,/g,'').match(/-?\d+(?:\.\d+)?/); return m?Number(m[0]):0; };
  const text=id=>(q(id)?.textContent||'').trim();

  // Ambient layers: created once; these are visual-only.
  const dust=document.createElement('div'); dust.className='ambient-dust';
  for(let i=0;i<7;i++){const s=document.createElement('i'); s.style.setProperty('--i',i); dust.appendChild(s);} scene.appendChild(dust);
  const cursor=document.createElement('div'); cursor.className='cursor-trail'; scene.appendChild(cursor);
  const status=document.createElement('div'); status.className='scene-status-ribbon'; scene.appendChild(status);

  let lastKeys=num('keys'), lastMouse=num('cursorDistance'), lastTick=Date.now(), idleTimer, idle=true;
  function activity(){
    idle=false; scene.classList.remove('is-idle'); clearTimeout(idleTimer);
    idleTimer=setTimeout(()=>{idle=true;scene.classList.add('is-idle');},90000);
  }
  ['mousemove','mousedown','keydown','wheel','touchstart'].forEach(e=>window.addEventListener(e,activity,{passive:true}));
  activity();

  function state(){
    const focus=text('focusStatus').toLowerCase();
    const hint=text('focusHint').toLowerCase();
    const active=text('liveStatus').toLowerCase();
    scene.classList.toggle('focus-mode', /专注|focus/.test(focus+hint));
    scene.classList.toggle('listening', /监听|working|工作/.test(active));
    scene.classList.toggle('high-intensity', (num('keys')-lastKeys)>80 || (num('ops')>0 && /工作|监听/.test(active)));
    scene.classList.toggle('rest-mode', idle || /休息|待命|暂停/.test(focus));
    const wx=document.documentElement.dataset.officeWeather||scene.dataset.weather||'';
    scene.classList.toggle('weather-rain',wx==='rain');
    scene.classList.toggle('weather-cloud',wx==='cloud');
    scene.classList.toggle('weather-mist',wx==='mist');
    scene.classList.toggle('weather-snow',wx==='snow');
    scene.classList.toggle('weather-clear',wx==='clear');

    // Existing display-info text is only used to choose the artwork layout.
    const di=text('displayInfo');
    const dual=/\b2\b|双屏|两个|2\s*屏/.test(di);
    scene.classList.toggle('dual-monitor',dual);
    scene.classList.toggle('single-monitor',!dual);

    const now=Date.now();
    if(now-lastTick>8000){
      const kd=Math.max(0,num('keys')-lastKeys), md=Math.max(0,num('cursorDistance')-lastMouse);
      if(kd>0 || md>0) activity();
      lastKeys=num('keys'); lastMouse=num('cursorDistance'); lastTick=now;
    }

    const label=q('pelicanState');
    const bubble=q('sceneBubble');
    if(label){
      if(idle){label.textContent='休息一下'; if(bubble) bubble.textContent='我先陪你看看窗外。';}
      else if(scene.classList.contains('focus-mode')){label.textContent='专注中'; if(bubble) bubble.textContent='戴好耳机，继续专注。';}
      else if(scene.classList.contains('high-intensity')){label.textContent='忙碌中'; if(bubble) bubble.textContent='键盘今天很忙。';}
      else {label.textContent='准备开工'; if(bubble) bubble.textContent='小鹈鹕，准备好了吗？';}
    }
  }
  setInterval(state,2500); state();

  // TODO completion micro-animation; does not alter checkbox behavior.
  const board=q('boardTodos');
  if(board){
    new MutationObserver(()=>{
      board.querySelectorAll('input[type=checkbox]').forEach(input=>{
        if(input.checked && !input.dataset.fx){
          input.dataset.fx='1';
          const item=input.closest('.todo')||input.parentElement;
          item?.classList.add('todo-just-done');
          setTimeout(()=>item?.classList.remove('todo-just-done'),1100);
        }
      });
    }).observe(board,{subtree:true,childList:true,attributes:true,attributeFilter:['checked']});
  }
  const rail=q('todos');
  if(rail){
    new MutationObserver(()=>rail.querySelectorAll('input[type=checkbox]').forEach(i=>{
      if(i.checked && !i.dataset.fx){i.dataset.fx='1'; (i.closest('.todo')||i.parentElement)?.classList.add('todo-just-done');}
    })).observe(rail,{subtree:true,childList:true,attributes:true,attributeFilter:['checked']});
  }

  // Replay: existing replay controls remain authoritative. We only decorate their scene.
  const replay=q('replayScene'), start=q('startReplay');
  if(replay){
    const art=replay.querySelector('.replay-office-art'), bird=replay.querySelector('.replay-pelican img');
    const time=q('replayTime'), cat=q('replayCategory');
    function syncReplay(){
      const tm=time?.textContent||'00:00', h=Number((tm.match(/\d{1,2}/)||['0'])[0]);
      replay.dataset.phase=(h>=19||h<5)?'night':(h>=17?'dusk':'day');
      if(art) art.src=(replay.dataset.phase==='night')?'/assets/illustrations/office-night.svg':'/assets/illustrations/office-day.svg';
      const c=(cat?.textContent||'').toLowerCase();
      if(bird) bird.src=/休息|idle|待机|暂停/.test(c)?'/assets/illustrations/pelican-v36-resting.svg':/疲劳|休息|tired/.test(c)?'/assets/illustrations/pelican-v36-tired.svg':'/assets/illustrations/pelican-v36-working.svg';
    }
    start?.addEventListener('click',()=>replay.classList.add('is-playing'));
    setInterval(syncReplay,1000); new MutationObserver(syncReplay).observe(replay,{subtree:true,childList:true,characterData:true}); syncReplay();
  }
})();
