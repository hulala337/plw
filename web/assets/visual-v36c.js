/* V3.6-C — environment asset director. It observes existing scene state only. */
(()=>{
  const scene=document.getElementById('scene'); if(!scene)return;
  const sync=()=>{
    const c=scene.classList;
    const count=Math.min(3,Math.max(1,Number(scene.dataset.monitors||1)));
    scene.dataset.displayCount=String(count);
    c.toggle('single-monitor',count===1);
    c.toggle('dual-monitor',count===2);
    c.toggle('triple-monitor',count===3);
    scene.dataset.artEnvironment=c.contains('resting')||c.contains('rest-mode')?'rest':c.contains('tired')?'tired':c.contains('high-intensity')?'active':c.contains('focus-mode')?'focus':c.contains('working')?'work':'idle';
  };
  sync();
  new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
})();
