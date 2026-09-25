const CAT={document:['文档编辑','#3d8de2'],web:['网页检索','#42b99a'],excel:['Excel','#5dbb71'],ppt:['PPT','#ef9e46'],wechat:['微信','#8a73d7'],meeting:['会议','#dd6e77'],focus:['其他工作','#6ca6bf'],idle:['发呆 / 离开','#b7c2ca']};
const state={data:null,growth:null,range:'today',zoom:1,replayTimer:null,dataRequestId:0,growthRequestId:0,weatherRequestId:0,weatherController:null};
window.state=state;
window.CAT=CAT;
let weatherEnabled=true;
const $=id=>document.getElementById(id);
const fmtSec=s=>{s=Math.max(0,Math.round(s||0));const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return h?`${h}h ${String(m).padStart(2,'0')}m`:`${m}m`;};
const fmtNum=n=>Number(n||0).toLocaleString('en-US');
const clock=()=>{const d=new Date();$('clock').textContent=d.toLocaleTimeString('zh-CN',{hour12:false});$('date').textContent=d.toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'short'});}; setInterval(clock,1000); clock();
async function getData(range='today'){
  const requestId=++state.dataRequestId;
  try{
    const r=await fetch(`/api/dashboard?range=${range}`);
    if(!r.ok)throw new Error(`dashboard ${r.status}`);
    const data=await r.json();
    if(requestId!==state.dataRequestId)return;
    try{const wr=await fetch('/api/world');if(wr.ok)data.world=await wr.json();}catch(_e){}
    if(requestId!==state.dataRequestId)return;
    state.data=data; renderAll();
  }catch(e){if(requestId!==state.dataRequestId)return;const live=$('liveStatus');if(live)live.textContent='数据连接异常';console.error(e);}
}
async function getGrowth(){
  const requestId=++state.growthRequestId;
  try{const r=await fetch('/api/growth');if(!r.ok)throw new Error(`growth ${r.status}`);const data=await r.json();if(requestId!==state.growthRequestId)return;state.growth=data;renderGrowth();}catch(e){if(requestId===state.growthRequestId)console.error(e);}
}
function setView(view){
  const target=$(`view-${view}`);
  if(!target)return;
  document.querySelectorAll('.view').forEach(v=>v.classList.add('hidden'));
  target.classList.remove('hidden');
  document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===view));
  if(view==='timeline')renderBigTimeline();
  window.scrollTo({top:0,behavior:'smooth'});
}
const on=(id,event,fn)=>{const el=$(id);if(el)el.addEventListener(event,fn);return el;};
document.querySelectorAll('.nav[data-view]').forEach(n=>n.addEventListener('click',e=>{e.preventDefault();setView(n.dataset.view);}));
document.querySelectorAll('[data-view-jump]').forEach(n=>n.addEventListener('click',e=>{e.preventDefault();setView(n.dataset.viewJump);}));
function renderMetrics(){const d=state.data||{},s=d.summary||{};$('active').textContent=fmtSec(s.active_seconds);$('keys').textContent=fmtNum(s.keys);$('chars').textContent=fmtNum(s.text_chars);$('cursorDistance').textContent=fmtNum(Math.round(Number(s.cursor_distance_px||0))); if(d.display){const msg=d.display.count<=1?'已识别：单显示器 · 按虚拟桌面坐标统计':`已识别：${d.display.count} 个显示器 · 支持跨屏坐标（虚拟桌面）`;if($('displayInfo'))$('displayInfo').textContent=msg;if($('displayInfoSettings'))$('displayInfoSettings').textContent=msg;}$('ops').textContent=fmtNum((s.keys||0)+(s.left_click||0)+(s.right_click||0)+(s.middle_click||0)+(s.scroll_events||0));$('longest').textContent=fmtSec(d.longest_focus_seconds);$('rhythm').textContent=d.rhythm||0;$('rhythmBar').style.width=(d.rhythm||0)+'%';}
function sceneState(){const d=state.data||{},s=d.summary||{},sess=d.active_session,w=d.world||{},active=Number(s.active_seconds||0),worldState=w.pelican_state||null;let cls='';const time=w.time_phase||(()=>{const h=new Date().getHours();return h>=19||h<6?'night':h>=17?'dusk':h<9?'morning':'day';})();if(time==='night')cls+='night ';let title='准备开工',hint='鹈鹕正在整理桌面。',speech='“今天准备做一件什么小事？”';if(w.work_state==='working'||sess){cls+='working';title='专注中';hint='已经连续工作 '+fmtSec(sess?.live_seconds||0);speech='“看起来状态不错。”';}else if(active>6*3600){cls+='tired';title='今天已经很努力了';hint='鹈鹕偷偷看了一眼空咖啡杯。';speech='“我们去窗边站两分钟？”';}else if(w.work_state==='active'||active>2*3600){cls+='steady';title='工作进行中';hint='鹈鹕的翅膀偶尔敲敲键盘。';speech='“一小段一小段地做，也很好。”';}else if(w.work_state==='resting'||(s.idle_seconds||0)>1800){cls+='resting';title='休息时间';hint='鹈鹕正在看窗外。';speech='“休息也算一天的一部分。”';}const el=$('scene');if(el){['night','working','tired','steady','resting','thinking','focused','celebrating','coffee','scene-dual','scene-sunset','scene-coffee'].forEach(k=>el.classList.remove(k));if(worldState){el.dataset.pelicanState=worldState;if(['thinking','focused','celebrating','coffee'].includes(worldState))cls+=' '+worldState;}else delete el.dataset.pelicanState;cls.trim().split(/\s+/).filter(Boolean).forEach(k=>el.classList.add(k));if(w.scene==='dual_monitor_office')el.classList.add('scene-dual');if(w.scene==='sunset_office')el.classList.add('scene-sunset');if(w.pelican==='coffee_pelican')el.classList.add('scene-coffee');el.dataset.time=time;el.dataset.monitors=String(Math.min(3,Math.max(1,Number(w.display_count||d.display?.count||1))));}if($('pelicanState'))$('pelicanState').textContent=title;if($('sceneHint'))$('sceneHint').textContent=hint;if($('petSpeech'))$('petSpeech').textContent=speech;if($('sceneBubble'))$('sceneBubble').textContent='🐦 '+speech.replaceAll('“','').replaceAll('”','');if($('petState'))$('petState').textContent=sess?'专注中':active>0?'工作过':'待命';if($('sideMood'))$('sideMood').textContent=title;if($('sidePetText'))$('sidePetText').textContent=hint;}
function renderPet(){const l=state.data?.lifetime||{};const petEnabled=state.data?.world?.desktop_pet!==false;const mainPet=$('pelican');if(mainPet)mainPet.style.display=petEnabled?'':'none';const sidePet=document.querySelector('.rail-pet');if(sidePet)sidePet.style.display=petEnabled?'':'none';$('level').textContent=l.level||1;$('streak').textContent=state.data?.streak||0;const pct=Math.min(100,((l.active_hours||0)%20)/20*100);$('levelBar').style.width=pct+'%';$('lifetimeText').textContent=`累计工作 ${fmtSec((l.active_hours||0)*3600)}`;const labels={green_plant:'🌿 植物',lamp:'💡 台灯',coffee_machine:'☕ 咖啡机',fish_tank:'🐠 鱼缸',bookshelf:'📚 书架',sunset_office:'🌇 黄昏工作室',dual_monitor_office:'🖥️ 双屏工作室',coffee_pelican:'🐦 咖啡鹈鹕'};const html=(l.unlocked||[]).map(x=>`<span>${labels[x]||x}</span>`).join('');$('unlocks').innerHTML=html;$('settingsUnlocks').innerHTML=html||'<span>继续真实工作以解锁办公室内容。</span>';$('growthText').textContent=`等级 ${l.level||1} · 累计 ${l.active_hours||0} 小时 · 已解锁 ${(l.unlocked||[]).length} 件内容。`;sceneState();}
function renderSessions(){const list=state.data?.sessions||[];const active=state.data?.active_session;$('focusStatus').textContent=active?'专注中':'待命';$('focusLive').textContent=fmtSec(active?active.live_seconds:(list[0]?.active_seconds||0));$('focusHint').textContent=active?'当前 Session':'最近 Session';$('sessionList').innerHTML=list.slice(-6).reverse().map(x=>`<div class="session"><b>${fmtSec(x.active_seconds)}</b><span>${new Date(x.started_at).toLocaleTimeString('zh-CN',{hour12:false,hour:'2-digit',minute:'2-digit'})} · ${(x.categories||'').split(',').map(k=>CAT[k]?.[0]||k).filter(Boolean).join(' → ')}</span></div>`).join('')||'<div class="empty">今天还没有完整 Session。</div>';}
function mergeTimeline(tl){const events=[];for(const x of tl||[]){const t=x.slice_start;events.push({...x,minute:new Date(t.replace(' ','T')).getHours()*60+new Date(t.replace(' ','T')).getMinutes()});}return events;}
function renderTimeline(){const tl=mergeTimeline(state.data?.timeline||[]), track=$('track'), seg=$('segments');track.style.minWidth=(Math.max(960,960*state.zoom))+'px';$('hours').innerHTML=Array.from({length:25},(_,i)=>`<span>${String(i).padStart(2,'0')}:00</span>`).join('');seg.innerHTML=tl.map(x=>{const left=x.minute/1440*100;const width=Math.max(.25,x.seconds/86400*100);const c=CAT[x.category]?.[1]||'#9aa';return `<div class="seg" data-min="${x.minute}" style="left:${left}%;width:${width}%;background:${c}"></div>`}).join('');$('legend').innerHTML=Object.entries(CAT).filter(([k])=>tl.some(x=>x.category===k)).map(([k,v])=>`<span><i style="background:${v[1]}"></i>${v[0]}</span>`).join('');setupScrubber($('track'),$('scrub'),$('scrubLabel'));}
function setupScrubber(track,scrub,label){let drag=false;const set=x=>{const r=track.getBoundingClientRect();const p=Math.max(0,Math.min(1,(x-r.left)/r.width));scrub.style.left=(p*100)+'%';const m=Math.round(p*1440);label.textContent=String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');const found=(state.data?.timeline||[]).find(x=>{const dt=new Date(x.slice_start.replace(' ','T'));const min=dt.getHours()*60+dt.getMinutes();return m>=min&&m<=min+Math.max(1,x.seconds/60);});$('sceneBubble').textContent=found?`🐦 ${CAT[found.category]?.[0]||found.category} · ${fmtSec(found.seconds)}`:'🐦 这一刻比较安静。';};scrub.onpointerdown=e=>{drag=true;scrub.setPointerCapture(e.pointerId);set(e.clientX)};scrub.onpointermove=e=>{if(drag)set(e.clientX)};scrub.onpointerup=()=>drag=false;set(new Date().getHours()/24*track.clientWidth+track.getBoundingClientRect().left);}
function renderBigTimeline(){const src=$('segments').innerHTML;$('bigSegments').innerHTML=src;$('bigHours').innerHTML=Array.from({length:25},(_,i)=>`<span>${String(i).padStart(2,'0')}</span>`).join('');$('bigTrack').style.minWidth='1440px';setupScrubber($('bigTrack'),$('bigScrub'),$('bigLabel'));const a=state.data?.summary||{};$('timelineSummary').innerHTML=`<div><small>活跃</small><b>${fmtSec(a.active_seconds)}</b></div><div><small>最长专注</small><b>${fmtSec(state.data?.longest_focus_seconds)}</b></div><div><small>主要类型</small><b>${mainCategory()}</b></div><div><small>当前状态</small><b>${state.data?.active_session?'专注中':'待命'}</b></div>`;}
function mainCategory(){return (state.data?.apps||[])[0]?CAT[(state.data.apps[0].category)]?.[0]||state.data.apps[0].category:'—';}
function renderApps(){const apps=state.data?.apps||[],max=Math.max(...apps.map(x=>x.seconds),1);$('apps').innerHTML=Object.entries(CAT).filter(([k])=>apps.some(x=>x.category===k)).map(([k,v])=>{const x=apps.find(x=>x.category===k);return `<div class="app-row"><div><span>${v[0]}</span><b>${fmtSec(x.seconds)}</b></div><div class="bar"><i style="width:${x.seconds/max*100}%;background:${v[1]}"></i></div></div>`}).join('')||'<div class="empty">今天还没有足够的工作活动。</div>';}
function renderTodos(){const t=state.data?.todos||[],done=t.filter(x=>x.done),todo=t.filter(x=>!x.done);$('todoCount').textContent=`${done.length}/${t.length}`;$('todos').innerHTML=todo.map(x=>`<div class="todo-row"><label class="todo"><input type="checkbox" data-id="${x.id}"><span>${esc(x.title)}</span></label><button class="todo-delete" type="button" data-delete-id="${x.id}" aria-label="删除">×</button></div>`).join('')||'<div class="empty">TODO 已清空。</div>';$('doneTodos').innerHTML=done.map(x=>`<div class="todo-row"><div class="todo done">✓ ${esc(x.title)}</div><button class="todo-delete" type="button" data-delete-id="${x.id}" aria-label="删除">×</button></div>`).join('')||'<div class="empty">DONE 还在等着。</div>';$('todoBoardCount').textContent=todo.length;$('boardTodos').innerHTML=todo.slice(0,4).map(x=>`<span>□ ${esc(x.title)}</span>`).join('');$('boardDone').innerHTML=done.slice(0,4).map(x=>`<span>✓ ${esc(x.title)}</span>`).join('');document.querySelectorAll('#todos input').forEach(i=>i.onchange=async()=>{const r=await fetch(`/api/todos/${i.dataset.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({done:i.checked})});if(!r.ok){i.checked=!i.checked;return;}if(i.checked)playUiSound();getData(state.range);});document.querySelectorAll('[data-delete-id]').forEach(b=>b.onclick=async()=>{const r=await fetch(`/api/todos/${b.dataset.deleteId}`,{method:'DELETE'});if(r.ok)getData(state.range);});}
function esc(s){return String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'&#92;','"':'&quot;'}[c]));}
function renderStats(){const s=state.data?.summary||{};const report=$('statsReport')||$('reportGrid');if(report)report.innerHTML=[['工作',fmtSec(s.active_seconds)],['键盘',fmtNum(s.keys)],['输入',fmtNum(s.text_chars)+' 字'],['鼠标',fmtNum(Math.round(s.cursor_distance_px||0))+' px'],['操作',fmtNum((s.keys||0)+(s.left_click||0)+(s.right_click||0)+(s.middle_click||0)+(s.scroll_events||0))],['最长专注',fmtSec(state.data?.longest_focus_seconds)]].map(x=>`<div><small>${x[0]}</small><b>${x[1]}</b></div>`).join('');const trend=$('statsTrend')||$('trendChart');const days=state.data?.days||[];const max=Math.max(...days.map(x=>x.active_seconds),1);if(trend)trend.innerHTML=days.map(x=>`<div class="trend-col"><b>${fmtSec(x.active_seconds)}</b><i style="height:${Math.max(5,x.active_seconds/max*190)}px"></i><small>${x.day.slice(5)}</small></div>`).join('')||'<div class="empty">没有历史数据。</div>';const range=state.range;const csv=$('csv'),xlsx=$('xlsx');if(csv)csv.href=`/api/export/csv?range=${range}`;if(xlsx)xlsx.href=`/api/export/xlsx?range=${range}`;}
let soundsEnabled=false;
async function loadSettings(){const s=await (await fetch('/api/settings')).json();weatherEnabled=!!s.weather_enabled;soundsEnabled=!!s.sounds_enabled;const autostart=$('autostartSettings')||$('autostart');if(autostart)autostart.checked=s.autostart;const desktop=$('desktopPet');if(desktop)desktop.checked=s.desktop_pet;const sound=$('soundsEnabled');if(sound)sound.checked=s.sounds_enabled;const weather=$('weatherEnabled');if(weather)weather.checked=s.weather_enabled;const idle=$('idleSeconds');if(idle)idle.value=s.idle_seconds;}
function playUiSound(){if(!soundsEnabled)return;try{const C=window.AudioContext||window.webkitAudioContext;if(!C)return;const c=new C(),o=c.createOscillator(),g=c.createGain();o.frequency.value=880;g.gain.value=.035;o.connect(g);g.connect(c.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,c.currentTime+.12);o.stop(c.currentTime+.12);o.onended=()=>c.close();}catch(_e){}}
async function patch(key,value){const r=await fetch('/api/settings',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({[key]:value})});if(!r.ok)throw new Error(`settings ${r.status}`);return r.json();}
async function saveSetting(key,value,after){try{await patch(key,value);if(after)await after();}catch(e){console.error(e);await loadSettings();if(key==='weather_enabled')renderWeather();}}
on('autostartSettings','change',e=>saveSetting('autostart',e.target.checked));
on('autostart','change',e=>saveSetting('autostart',e.target.checked));
on('desktopPet','change',e=>saveSetting('desktop_pet',e.target.checked,()=>{if(state.data?.world)state.data.world.desktop_pet=e.target.checked;renderPet();}));
on('soundsEnabled','change',e=>{soundsEnabled=e.target.checked;saveSetting('sounds_enabled',e.target.checked);});
on('weatherEnabled','change',e=>{weatherEnabled=e.target.checked;saveSetting('weather_enabled',e.target.checked,renderWeather);});
on('idleSeconds','change',e=>saveSetting('idle_seconds',Number(e.target.value)));
on('todoForm','submit',async e=>{e.preventDefault();const v=$('todoInput').value.trim();if(!v)return;const r=await fetch('/api/todos',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:v})});if(!r.ok){console.error('todo create failed',r.status);return;}$('todoInput').value='';getData(state.range);});
on('replayBtn','click',()=>setView('replay'));
on('nowBtn','click',()=>{const track=$('track'),scrub=$('scrub');if(!track||!scrub)return;const p=(new Date().getHours()*60+new Date().getMinutes())/1440;scrub.style.left=(p*100)+'%';});
on('zoomPlus','click',()=>{state.zoom=Math.min(2.5,state.zoom+.5);renderTimeline();});
on('zoomMinus','click',()=>{state.zoom=Math.max(1,state.zoom-.5);renderTimeline();});
on('startReplay','click',async()=>{try{const r=await fetch('/api/replay');if(!r.ok)throw new Error(`replay ${r.status}`);const ev=(await r.json()).events||[];if(!ev.length){$('replayCategory').textContent='今天还没有可回放的活动';return;}clearInterval(state.replayTimer);let i=0;$('startReplay').textContent='↻ 重播';state.replayTimer=setInterval(()=>{if(i>=ev.length){clearInterval(state.replayTimer);$('startReplay').textContent='▶ 开始播放';return;}const e=ev[i++],d=new Date(e.slice_start.replace(' ','T'));$('replayTime').textContent=d.toLocaleTimeString('zh-CN',{hour12:false,hour:'2-digit',minute:'2-digit'});$('replayCategory').textContent=CAT[e.category]?.[0]||e.category;$('replayDesc').textContent=`${fmtSec(e.seconds)} · ${e.events||0} 次行为`;$('replayBar').style.width=(i/ev.length*100)+'%';$('replayScene').className='replay-scene '+e.category;},500);}catch(e){console.error(e);$('replayCategory').textContent='回放数据暂时不可用';}});
on('forgetToday','click',async()=>{if(!confirm('删除今天的统计与时间轴？此操作不可恢复。'))return;const r=await fetch('/api/forget-today',{method:'POST'});if(!r.ok){console.error('forget today failed',r.status);return;}getData(state.range);getGrowth();});
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.range=b.dataset.range;getData(state.range);});
function setupDonation(){const modal=$('donateModal'),btn=$('donateBtn'),img=$('wechatQr'),fallback=$('qrFallback'),close=$('donateClose'),backdrop=$('donateBackdrop');if(!modal||!btn)return;if(img)img.onerror=()=>{img.style.display='none';if(fallback)fallback.style.display='block'};btn.addEventListener('click',()=>{modal.classList.remove('hidden');document.body.classList.add('modal-open')});if(close)close.addEventListener('click',()=>{modal.classList.add('hidden');document.body.classList.remove('modal-open')});if(backdrop)backdrop.addEventListener('click',()=>{if(close)close.click();});}
async function renderWeather(){
  const scene=$('scene'), cacheKey='pelican.weather.v1', cacheMaxAge=30*60*1000, requestId=++state.weatherRequestId;
  if(state.weatherController){try{state.weatherController.abort();}catch(_e){}state.weatherController=null;}
  const show=(x,source)=>{
    if(!x)return;
    if($('weather')){$('weather').textContent=x.icon+' '+x.temperature+'°C · '+x.label;$('weather').title=source==='cache'?'使用最近一次天气缓存':'实时天气';}
    if(scene){scene.dataset.weather=x.kind;scene.classList.toggle('raining',x.kind==='rain');}
    document.body.dataset.weather=x.kind;
  };
  if(!weatherEnabled){
    try{localStorage.removeItem('pelican.weather.v1');}catch(_e){}
    if($('weather')){$('weather').textContent='本地天气未启用';$('weather').title='未请求位置或天气服务';}
    if(scene){delete scene.dataset.weather;scene.classList.remove('raining');}
    delete document.body.dataset.weather;
    return;
  }
  let cached=null;
  try{cached=JSON.parse(localStorage.getItem(cacheKey)||'null');}catch(_e){}
  if(cached?.data && cached.savedAt && Date.now()-cached.savedAt<cacheMaxAge){
    show(cached.data,'cache');
    return;
  }
  const map={0:['晴天','☀️','clear'],1:['晴间多云','🌤️','cloud'],2:['多云','⛅','cloud'],3:['阴天','☁️','cloud'],45:['雾','🌫️','mist'],48:['雾','🌫️','mist'],51:['毛毛雨','🌦️','rain'],53:['毛毛雨','🌦️','rain'],55:['毛毛雨','🌦️','rain'],61:['下雨','🌧️','rain'],63:['中雨','🌧️','rain'],65:['大雨','🌧️','rain'],71:['下雪','❄️','snow'],73:['下雪','❄️','snow'],75:['大雪','❄️','snow'],80:['阵雨','🌦️','rain'],81:['阵雨','🌦️','rain'],82:['强阵雨','🌧️','rain'],95:['雷雨','⛈️','rain'],96:['雷雨','⛈️','rain'],99:['雷雨','⛈️','rain']};
  try{
    if(!('geolocation' in navigator))throw new Error('geolocation unavailable');
    navigator.geolocation.getCurrentPosition(async pos=>{
      if(requestId!==state.weatherRequestId||!weatherEnabled)return;
      const controller=new AbortController(); state.weatherController=controller;
      try{
        const timer=setTimeout(()=>controller.abort(),5000);
        try{
          if(requestId!==state.weatherRequestId||!weatherEnabled)return;
          const lat=pos.coords.latitude,lon=pos.coords.longitude;
          const url='https://api.open-meteo.com/v1/forecast?latitude='+lat+'&longitude='+lon+'&current=temperature_2m,weather_code&timezone=auto';
          const r=await fetch(url,{signal:controller.signal});
          if(!r.ok)throw new Error('weather '+r.status);
          const j=await r.json(),c=j.current,x=map[c.weather_code]||['天气','🌤️','clear'];
          const data={temperature:c.temperature_2m,label:x[0],icon:x[1],kind:x[2]};
          show(data,'live');
          try{localStorage.setItem(cacheKey,JSON.stringify({savedAt:Date.now(),data}));}catch(_e){}
        }finally{clearTimeout(timer);}
      }catch(e){if(cached?.data)show(cached.data,'cache');else if($('weather'))$('weather').textContent='天气暂不可用';}
    },()=>{if(cached?.data)show(cached.data,'cache');else if($('weather'))$('weather').textContent='天气暂不可用';},{enableHighAccuracy:false,maximumAge:cacheMaxAge,timeout:5000});
  }catch(e){if(cached?.data)show(cached.data,'cache');else if($('weather'))$('weather').textContent='天气暂不可用';}
}

function renderGrowth(){const g=state.growth||{},p=g.profile||{},pct=Number(p.progress_pct||0),eq=Object.fromEntries((g.equipment||[]).filter(x=>!x.slot.startsWith('decoration:')).map(x=>[x.slot,x.item_id])),decorEq=new Set((g.equipment||[]).filter(x=>x.item_type==='decoration').map(x=>x.item_id));const report=$('growthReport');if(report)report.innerHTML=[['等级',p.level||1],['XP',fmtNum(p.xp||0)],['本级进度',fmtNum(p.xp_into_level||0)+' / '+fmtNum(Math.max(0,(p.next_level_xp||0)-(p.level_xp_start||0)))],['累计工作',fmtSec((p.active_hours||0)*3600)],['已解锁',(g.unlocks||[]).length],['成就',(g.achievements||[]).length]].map(x=>'<div><small>'+x[0]+'</small><b>'+x[1]+'</b></div>').join('')+'<div class="growth-xp"><small>'+(p.level>=12?'最高等级':'距下一级 '+fmtNum(p.xp_to_next_level||0)+' XP')+'</small><i style="width:'+pct+'%"></i></div>';const achLabels={first_session:'第一次 Session',ten_hours:'累计 10 小时',hundred_hours:'累计 100 小时',multi_monitor:'多显示器',seven_day_streak:'连续 7 天'};const ae=$('growthAchievements');if(ae)ae.innerHTML=(g.achievement_catalog||[]).map(x=>'<span>'+(x.unlocked?'🏆 ':'🔒 ')+(achLabels[x.id]||x.id)+(x.unlocked?'':' · '+x.condition)+'</span>').join('')||'<span>暂无成就。</span>';const labels={green_plant:'🌿 植物',lamp:'💡 台灯',coffee_machine:'☕ 咖啡机',fish_tank:'🐠 鱼缸',bookshelf:'📚 书架',dual_monitor_office:'🖥️ 双屏工作室',sunset_office:'🌇 黄昏工作室',coffee_pelican:'🐦 咖啡鹈鹕',coffee_outfit:'🧑‍🍳 咖啡围裙',headphones:'🎧 耳机',focus_sparkles:'✨ 专注星光'};const ue=$('growthUnlocks');if(ue)ue.innerHTML=(g.unlocks||[]).map(x=>'<span>'+(labels[x.item_id]||x.item_id)+'</span>').join('')||'<span>继续真实工作以解锁内容。</span>';[['scenes','growthScenes','scene'],['pelicans','growthPelicans','pelican'],['outfits','growthOutfits','outfit'],['accessories','growthAccessories','accessory'],['decorations','growthDecorations','decoration'],['effects','growthEffects','effect']].forEach(([key,id,slot])=>{const el=$(id);if(!el)return;el.innerHTML=(g.collection?.[key]||[]).map(x=>'<button type="button" class="growth-item '+(x.unlocked?'':'locked')+((slot==='decoration'?decorEq.has(x.id):eq[slot]===x.id)?' equipped':'')+'" data-equip-slot="'+slot+'" data-equip-id="'+x.id+'" '+(x.unlocked?'':'disabled')+'>'+((slot==='decoration'&&decorEq.has(x.id))?'✓ ':((eq[slot]===x.id)?'✓ ':(!x.unlocked?'🔒 ':' ')))+x.name+(x.unlocked?'':' · Lv.'+x.required_level)+'</button>').join('')||'<span>暂无内容。</span>';});document.querySelectorAll('[data-equip-slot]').forEach(b=>b.onclick=async()=>{const r=await fetch('/api/equipment',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({slot:b.dataset.equipSlot,item_id:b.dataset.equipId})});if(!r.ok){console.error('equip failed',r.status);return;}await getGrowth();await getData(state.range);});}
function renderAll(){renderMetrics();renderPet();renderTimeline();renderSessions();renderTodos();renderApps();renderStats();}
function healthLabel(ok){return ok?'正常':'异常';}
function renderHealthPanel(h){
  const box=$('healthChecks');
  if(!box)return;
  const checks=[
    ['键盘监听',h.keyboard_listener],
    ['鼠标监听',h.mouse_listener],
    ['Tracker',h.tracker],
    ['SQLite',h.database],
    ['Web UI',h.web],
    ['显示器检测',h.display]
  ];
  box.innerHTML=checks.map(([name,ok])=>'<span class="'+(ok?'ok':'bad')+'"><i></i>'+name+' · '+healthLabel(ok)+'</span>').join('');
  box.dataset.status=h.status||'degraded';
}
async function refreshHealth(){
  try{
    const h=await (await fetch('/api/health')).json();
    const live=$('liveStatus');
    if(live){
      live.textContent=h.status==='ok'?'监听中':(h.listeners?'监听恢复中':'监听异常');
      live.title=h.listener_error||h.db_error||'';
      live.dataset.health=h.status;
    }
    renderHealthPanel(h);
  }catch(e){
    const live=$('liveStatus');
    if(live)live.textContent='连接异常';
    renderHealthPanel({status:'degraded',keyboard_listener:false,mouse_listener:false,tracker:false,database:false,web:false,display:false});
  }
}
window.patch=patch;
loadSettings().then(renderWeather).catch(()=>{weatherEnabled=false;renderWeather();});getData();getGrowth();refreshHealth();setupDonation();on('healthRefresh','click',refreshHealth);setInterval(()=>{getData(state.range);getGrowth();},15000);setInterval(refreshHealth,5000);
