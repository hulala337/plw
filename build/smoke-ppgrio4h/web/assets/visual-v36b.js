/* V3.6-A — asset coordination for the new state/desk art. Presentation only. */
(()=>{
  const scene=document.getElementById('scene'); if(!scene)return;
  const sync=()=>{
    const c=scene.classList;
    const state=c.contains('resting')||c.contains('rest-mode')?'resting':c.contains('tired')?'tired':c.contains('high-intensity')?'busy':c.contains('focus-mode')?'focus':c.contains('working')?'working':'idle';
    scene.dataset.artState=state;
  };
  sync();
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  const replay=document.getElementById('replayScene');
  if(replay){
    const bird=replay.querySelector('.replay-pelican img');
    const time=document.getElementById('replayTime'),cat=document.getElementById('replayCategory');
    const update=()=>{
      const tm=time?.textContent||'00:00', h=Number((tm.match(/\d{1,2}/)||['0'])[0]);
      const c=(cat?.textContent||'').toLowerCase();
      if(bird) bird.src=/休息|idle|待机|暂停/.test(c)?'/assets/illustrations/pelican-v36-resting.svg':/疲劳|tired/.test(c)?'/assets/illustrations/pelican-v36-tired.svg':'/assets/illustrations/pelican-v36-working.svg';
      replay.dataset.artPhase=(h>=19||h<5)?'night':(h>=17?'dusk':'day');
    };
    update();
    new MutationObserver(update).observe(replay,{subtree:true,childList:true,characterData:true});
  }
})();
