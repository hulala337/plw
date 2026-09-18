/* V3.5 Life Layer — visual-only. Existing application state remains authoritative. */
(()=>{
  const scene=document.getElementById('scene');
  const pelican=document.getElementById('pelican');
  if(!scene||!pelican)return;

  if(!pelican.querySelector('.pelican-life-layer')){
    const img=document.createElement('img');
    img.className='pelican-life-layer';
    img.src='/assets/illustrations/pelican-life-overlay.svg';
    img.alt=''; img.setAttribute('aria-hidden','true'); img.draggable=false;
    pelican.appendChild(img);
  }
  if(!pelican.querySelector('.pelican-life-badge')){
    const badge=document.createElement('div');
    badge.className='pelican-life-badge';
    badge.textContent='正在思考…';
    pelican.appendChild(badge);
  }

  const badge=pelican.querySelector('.pelican-life-badge');
  let timer=null;
  const thoughts=['正在思考…','让我再确认一下','这个任务可以解决','先把这一项做好'];
  let thoughtIndex=0;

  function sceneMode(){
    const c=scene.classList;
    if(c.contains('tired'))return 'tired';
    if(c.contains('resting')||c.contains('rest-mode'))return 'resting';
    if(c.contains('high-intensity'))return 'busy';
    if(c.contains('focus-mode')||c.contains('working'))return 'working';
    return 'idle';
  }
  function think(){
    if(sceneMode()!=='working')return;
    scene.classList.add('pelican-thinking');
    if(badge){badge.textContent=thoughts[thoughtIndex++%thoughts.length]}
    window.clearTimeout(timer);
    timer=window.setTimeout(()=>scene.classList.remove('pelican-thinking'),1200+Math.random()*1100);
  }
  function sync(){
    const mode=sceneMode();
    pelican.dataset.life=mode;
    if(mode!=='working')scene.classList.remove('pelican-thinking');
  }
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  sync();
  window.setInterval(()=>{
    if(document.hidden)return;
    if(Math.random()<.42)think();
  },5200);
})();

/* Round 2: choreograph the character against existing workspace DOM. */
(()=>{
  const scene=document.getElementById('scene'), pelican=document.getElementById('pelican');
  if(!scene||!pelican)return;
  if(!pelican.querySelector('.pelican-desk-life')){
    const img=document.createElement('img'); img.className='pelican-desk-life';
    img.src='/assets/illustrations/pelican-desk-life.svg'; img.alt=''; img.setAttribute('aria-hidden','true'); img.draggable=false;
    pelican.appendChild(img);
  }
  const todos=document.getElementById('boardTodos'), done=document.getElementById('boardDone');
  let celebrateTimer=0;
  let lastDone=done?done.children.length:0;
  function count(el){return el?el.children.length:0}
  function sync(){
    const active=count(todos), completed=count(done);
    const working=scene.classList.contains('working')||scene.classList.contains('focus-mode')||scene.classList.contains('high-intensity');
    scene.classList.toggle('working-at-desk',working && !scene.classList.contains('resting'));
    scene.classList.toggle('board-focus',active>0 && !scene.classList.contains('resting') && !scene.classList.contains('tired'));
    if(completed>lastDone){
      scene.classList.remove('task-celebrate'); void scene.offsetWidth; scene.classList.add('task-celebrate');
      window.clearTimeout(celebrateTimer); celebrateTimer=window.setTimeout(()=>scene.classList.remove('task-celebrate'),1600);
    }
    lastDone=completed;
  }
  if(todos)new MutationObserver(sync).observe(todos,{subtree:true,childList:true,characterData:true,attributes:true});
  if(done)new MutationObserver(sync).observe(done,{subtree:true,childList:true,characterData:true,attributes:true});
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  sync();
})();
