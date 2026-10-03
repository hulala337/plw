/* V3.5 — presentation-only refinement. No business/API changes. */
(()=>{
 const scene=document.getElementById('scene'); if(!scene)return;
 const cursor=scene.querySelector('.cursor-trail'), ribbon=scene.querySelector('.scene-status-ribbon');
 let mx=0,my=0,tx=0,ty=0;
 window.addEventListener('mousemove',e=>{const r=scene.getBoundingClientRect();mx=((e.clientX-r.left)/r.width-.5);my=((e.clientY-r.top)/r.height-.5);if(cursor){cursor.style.left=(e.clientX-r.left)+'px';cursor.style.top=(e.clientY-r.top)+'px';cursor.style.opacity='1'}} ,{passive:true});
 window.addEventListener('mouseout',()=>{if(cursor)cursor.style.opacity='0'},{passive:true});
 function frame(){tx+=(mx*.7-tx)*.045;ty+=(my*.45-ty)*.045;const art=scene.querySelector('.scene-art-day img');const night=scene.querySelector('.scene-art-night img');[art,night].forEach((el,i)=>{if(el)el.style.transform=`translate3d(${tx*(i?-.7:-1)}%,${ty*(i?-.45:-.7)}%,0) scale(1.012)`});requestAnimationFrame(frame)} frame();
 function sync(){if(ribbon){const s=(document.getElementById('liveStatus')?.textContent||'').trim();ribbon.textContent=s||'准备中'} const pel=document.getElementById('pelican'); if(pel){pel.setAttribute('data-motion',scene.className)}}
 new MutationObserver(sync).observe(scene,{attributes:true,attributeFilter:['class','data-time','data-weather']}); setInterval(sync,1800); sync();
})();
