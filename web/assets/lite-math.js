(function(root){
  const nonnegative=v=>Number.isFinite(Number(v))?Math.max(0,Number(v)):0;
  function stories(s){return {pages:nonnegative(s.text_chars)/500,bookPercent:nonnegative(s.text_chars)/100000*100,meters:nonnegative(s.cursor_distance_px)*0.0254/96,focusBlocks:nonnegative(s.active_seconds)/1500};}
  function portrait(apps){const active=(apps||[]).filter(x=>x.category!=='idle'&&nonnegative(x.seconds)>0);const total=active.reduce((a,x)=>a+nonnegative(x.seconds),0);const first=[...active].sort((a,b)=>b.seconds-a.seconds)[0];return {category:first?.category||null,share:total?nonnegative(first.seconds)/total:0,total};}
  function hours(events){const bins=Array(24).fill(0);for(const x of events||[]){if(x.category==='idle')continue;const t=new Date(x.slice_start.replace(' ','T'));if(Number.isNaN(t.getTime()))continue;let start=t.getHours()*3600+t.getMinutes()*60+t.getSeconds(),remaining=Math.min(nonnegative(x.seconds),86400-start);while(remaining>0){const h=Math.floor(start/3600),part=Math.min(remaining,3600-start%3600);bins[h]+=part;start+=part;remaining-=part;}}return bins;}
  const api={stories,nonnegative,portrait,hours};root.LiteMath=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
