/* V3.6-D — restrained motion director. No business state is mutated. */
(()=>{
  const scene=document.getElementById('scene');
  if(!scene)return;
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const setState=()=>{
    const c=scene.classList;
    scene.dataset.artEnvironment=c.contains('resting')||c.contains('rest-mode')?'rest':c.contains('tired')?'tired':c.contains('high-intensity')?'active':c.contains('focus-mode')?'focus':c.contains('working')?'work':'idle';
  };
  setState();
  new MutationObserver(setState).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']});
  if(reduced)return;

  const root=document.documentElement;
  let raf=0,start=performance.now();
  const tick=(now)=>{
    const t=(now-start)/1000;
    const state=scene.dataset.artEnvironment||'idle';
    const intensity=state==='active'?1.35:state==='focus'?1.0:state==='work'?.72:state==='rest'?.42:.28;
    const slow=Math.sin(t*.43)*.55;
    const slow2=Math.sin(t*.31+1.7)*.45;
    const shimmer=(Math.sin(t*.62+2.1)+1)/2;
    scene.style.setProperty('--v36d-decor-x',`${(slow*.42*intensity).toFixed(3)}px`);
    scene.style.setProperty('--v36d-decor-y',`${(-Math.abs(slow2)*.26*intensity).toFixed(3)}px`);
    scene.style.setProperty('--v36d-lamp-x',`${(slow2*.18).toFixed(3)}px`);
    scene.style.setProperty('--v36d-lamp-y',`${(-Math.abs(slow)*.12).toFixed(3)}px`);
    scene.style.setProperty('--v36d-glass-x',`${(Math.sin(t*.12)*1.2).toFixed(3)}px`);
    scene.style.setProperty('--v36d-screen-opacity',(0.68+shimmer*0.16).toFixed(3));
    scene.style.setProperty('--v36d-cup',`${(Math.sin(t*.36+1.1)*.12).toFixed(3)}deg`);
    scene.style.setProperty('--v36d-cup-y',`${(-Math.max(0,Math.sin(t*.36+1.1))*.25).toFixed(3)}px`);
    raf=requestAnimationFrame(tick);
  };
  raf=requestAnimationFrame(tick);
  window.addEventListener('pagehide',()=>cancelAnimationFrame(raf),{once:true});
})();
