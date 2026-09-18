/* V3.6-C — environment asset director. It observes existing scene state only. */
(()=>{
  const scene=document.getElementById('scene'); if(!scene)return;
  const sync=()=>{
    const c=scene.classList;
    scene.dataset.artEnvironment=c.contains('resting')||c.contains('rest-mode')?'rest':c.contains('tired')?'tired':c.contains('high-intensity')?'active':c.contains('focus-mode')?'focus':c.contains('working')?'work':'idle';
  };
  sync();
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
})();
