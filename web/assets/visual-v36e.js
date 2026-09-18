/* V3.6-E — gaze director. Tiny local eye movement only; business state remains authoritative. */
(()=>{
  const scene=document.getElementById('scene');
  if(!scene)return;
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if(reduced){scene.style.setProperty('--v36e-gaze-x','0px');scene.style.setProperty('--v36e-gaze-y','0px');return;}
  let gx=0,gy=0,tx=0,ty=0,next=performance.now()+1800;
  const choose=()=>{
    const c=scene.classList;
    if(c.contains('behavior-read-board')){tx=-1.8;ty=-.8;}
    else if(c.contains('behavior-think')){tx=1.9;ty=-1.4;}
    else if(c.contains('behavior-type')||c.contains('high-intensity')){tx=(Math.random()-.5)*1.2;ty=.9+Math.random()*.7;}
    else if(c.contains('behavior-coffee')){tx=.7;ty=.5;}
    else {tx=(Math.random()-.5)*2.2;ty=(Math.random()-.5)*1.2;}
    next=performance.now()+2200+Math.random()*3200;
  };
  const tick=(now)=>{
    const c=scene.classList;
    if(now>=next)choose();
    if(c.contains('tired')||c.contains('resting')||c.contains('rest-mode')){tx=0;ty=0;}
    gx+=(tx-gx)*.045; gy+=(ty-gy)*.045;
    scene.style.setProperty('--v36e-gaze-x',gx.toFixed(3)+'px');
    scene.style.setProperty('--v36e-gaze-y',gy.toFixed(3)+'px');
    requestAnimationFrame(tick);
  };
  choose();requestAnimationFrame(tick);
})();
