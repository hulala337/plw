/* V3.5 Life Round 3 — behavioral director. Visual-only; business state remains authoritative. */
(()=>{
  const scene=document.getElementById('scene'), pelican=document.getElementById('pelican');
  if(!scene||!pelican)return;
  const make=(cls,tag='div')=>{const n=document.createElement(tag);n.className=cls;return n};
  if(!pelican.querySelector('.pelican-life-director')){
    const d=make('pelican-life-director');
    d.append(make('gaze'),make('paper-cue'),make('coffee-cue'),make('completion-ring'),make('status-whisper'));
    pelican.appendChild(d);
  }
  const director=pelican.querySelector('.pelican-life-director'), whisper=director.querySelector('.status-whisper');
  const todos=document.getElementById('boardTodos'), done=document.getElementById('boardDone');
  let lastDone=done?.children.length||0, lastKeys=0, lastOps=0, behaviorTimer=0, clearTimer=0;
  let current='idle';
  const text=id=>(document.getElementById(id)?.textContent||'').trim();
  const count=el=>el?.children.length||0;
  const setBehavior=(name,ms=0)=>{
    [...scene.classList].filter(x=>x.startsWith('behavior-')).forEach(x=>scene.classList.remove(x));
    current=name; scene.classList.add('behavior-'+name);
    if(ms){clearTimeout(clearTimer);clearTimer=setTimeout(()=>{scene.classList.remove('behavior-'+name);current='idle'},ms)}
  };
  const mode=()=>{
    if(scene.classList.contains('resting')||scene.classList.contains('rest-mode'))return 'rest';
    if(scene.classList.contains('tired'))return 'tired';
    if(scene.classList.contains('high-intensity'))return 'busy';
    if(scene.classList.contains('focus-mode'))return 'focus';
    if(scene.classList.contains('working-at-desk'))return 'work';
    return 'idle';
  };
  function direct(){
    const m=mode(), active=count(todos), status=text('liveStatus').toLowerCase();
    if(whisper) whisper.textContent=m==='rest'?'先歇一会儿':m==='tired'?'今天也辛苦了':m==='busy'?'再冲一会儿':m==='focus'?'别被打扰':'我在这里';
    if(m==='rest'){setBehavior(Math.random()<.55?'coffee':'rest',2600);return}
    if(m==='tired'){setBehavior('idle');return}
    if(active>0 && m!=='idle' && Math.random()<.48){setBehavior('read-board',1900);return}
    if(m==='busy'){setBehavior('type',2200);return}
    if(m==='focus'){setBehavior('think',1700);return}
    if(/监听|工作|working/.test(status)&&Math.random()<.55){setBehavior('type',2000);return}
    setBehavior('idle');
  }
  function sync(){
    const keys=Number((text('keys').replace(/,/g,'').match(/\d+/)||[0])[0]);
    const ops=Number((text('ops').replace(/,/g,'').match(/\d+/)||[0])[0]);
    const completed=count(done);
    if(completed>lastDone){setBehavior('complete',1500);if(whisper)whisper.textContent='这一项，完成。';}
    else if(keys-lastKeys>60||ops-lastOps>4){setBehavior('type',1700)}
    lastDone=completed;lastKeys=keys;lastOps=ops;
  }
  function schedule(){
    if(document.hidden)return;
    if(current==='complete')return;
    if(current==='coffee')return;
    const delay=5200+Math.random()*5200;
    clearTimeout(behaviorTimer);behaviorTimer=setTimeout(()=>{direct();schedule()},delay);
  }
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  if(todos)new MutationObserver(sync).observe(todos,{subtree:true,childList:true,characterData:true});
  if(done)new MutationObserver(sync).observe(done,{subtree:true,childList:true,characterData:true});
  sync();direct();schedule();
})();
