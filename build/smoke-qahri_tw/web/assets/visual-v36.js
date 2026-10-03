/* V3.6 — asset-first presentation director. Business state remains authoritative. */
(()=>{
  const scene=document.getElementById('scene'); if(!scene)return;
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const sync=()=>{
    const c=scene.classList;
    const state=c.contains('celebrating')?'celebrating':c.contains('coffee')?'coffee':c.contains('thinking')?'thinking':c.contains('resting')||c.contains('rest-mode')?'resting':c.contains('tired')?'tired':c.contains('high-intensity')?'busy':c.contains('focus-mode')||c.contains('focused')?'focus':c.contains('working')?'working':'idle';
    scene.dataset.artState=state;
    scene.dataset.artMood=(document.getElementById('sceneHint')?.textContent||'').trim();
  };
  sync();
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  if(!reduced){
    let pulse=0;
    const nudge=()=>{
      const active=scene.dataset.artState;
      scene.style.setProperty('--v36-scene-nudge',active==='busy'?'1px':active==='resting'?'0px':'0.4px');
      pulse=window.setTimeout(nudge,5000+Math.random()*6000);
    };
    nudge();
  }
})();
