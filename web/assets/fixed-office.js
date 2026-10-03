/* Page construction and data-only widgets. Original office art remains intact. */
function renderDetails(){
 const d=state.data||{},s=d.summary||{},top=d.key_top_today||{keys:[],total:0},c=d.confirmed_characters||{};
 const clicks=(s.left_click||0)+(s.right_click||0)+(s.middle_click||0);
 document.getElementById('clickTotal').textContent=`${fmtNum(clicks)} 次`;
 const entries=[['左键',s.left_click||0],['右键',s.right_click||0],['中键',s.middle_click||0]];
 const box=document.getElementById('clickParts');box.replaceChildren();
 for(const [label,n] of entries){const row=document.createElement('div');row.className='row';row.textContent=`${label}　${fmtNum(n)} 次`;const bar=document.createElement('div');bar.className='bar';const fill=document.createElement('i');fill.style.width=`${clicks?n/clicks*100:0}%`;bar.append(fill);box.append(row,bar);}
 document.getElementById('scrollTotal').textContent=`${fmtNum(s.scroll_events)} 次事件`;
 document.getElementById('scrollUnits').textContent=`累计滚动量 ${fmtNum((s.scroll_distance_px||0)/120)} 驱动单位（历史字段 ÷ 120）。不是圈数、实际像素或米数。`;
 const keys=document.getElementById('keyTop');keys.replaceChildren();for(const k of top.keys){const row=document.createElement('div');row.className='row';row.textContent=`${k.key_name}　${fmtNum(k.count)} 次`;keys.append(row);}if(!top.keys.length)keys.textContent='暂无键位记录';
 document.getElementById('characterCount').replaceChildren();for(const [label,n] of [['总字符',c.count],['中文汉字',c.chinese],['英文字母',c.english],['其他',c.other],['历史未分类',c.unclassified]]){const item=document.createElement('span'),strong=document.createElement('strong');item.textContent=label;strong.textContent=fmtNum(n);item.append(strong);document.getElementById('characterCount').append(item);}
}
function refresh(){return getData(state.range);}
(()=>{
 const root=document.createElement('section');root.className='panel office-data';root.innerHTML=`<div class="panel-head"><div><span class="eyebrow">INPUT DETAILS</span><h2>输入行为 · 各自计数，清楚呈现</h2></div></div><div class="data-grid"><article><h3>鼠标点击</h3><strong id="clickTotal">0 次</strong><div id="clickParts"></div></article><article><h3>滚轮滚动</h3><strong id="scrollTotal">0 次事件</strong><p id="scrollUnits"></p><small>滚轮按下归入中键点击；滚动与点击独立统计。光标距离继续以原始 px 展示，不做固定 96 DPI 米数换算。</small></article><article><h3>今日按键 TOP5</h3><div id="keyTop"></div><small>始终显示今天；包含快捷键和自动重复。只保存每日累计，不保存按键顺序。</small></article></div><h3>已确认字符 · 当前统计范围</h3><div class="character-grid" id="characterCount"></div><p>中文统计汉字，英文统计字母，不是单词数。数字、空白、标点与 emoji 归入其他。</p><small>仅覆盖下面自愿输入区；不覆盖其他软件。粘贴不计数、不读取剪贴板。全局“字符键触发次数”不等于实际输入字数。活跃时间和专注片段按输入间隔规则推断，不衡量工作价值。</small><label><input type="checkbox" id="characterOptIn"> 开启本输入区字符计数</label><textarea disabled id="characterPad" rows="3" spellcheck="false" autocomplete="off" aria-label="字符计数输入区" placeholder="文本只存在本页，刷新即清空；仅上传分类数量。"></textarea><p id="characterStatus" role="status">未开启</p>`;
 document.getElementById('view-stats').append(root);
 // Remove obsolete controls rather than offering settings with no effect.
 for(const id of ['weatherEnabled','desktopPet','growthTextSettings']){const n=document.getElementById(id);if(n)n.closest('.panel.setting')?.remove();}
 document.querySelector('.metrics-title b').textContent='工作数据概览';
 const charMetric=document.getElementById('chars').closest('.metric');charMetric.querySelector('small').textContent='字符键触发';charMetric.querySelector('em').textContent='次';
 document.querySelector('.timeline-card .panel-head p').textContent='拖动时间点，查看记录到的工作分类；场景保持不变。';
 const legacy=document.getElementById('settingsUnlocks');if(legacy)legacy.replaceChildren();
 const distribution=document.createElement('section');distribution.className='panel office-data';const heading=document.createElement('h2');heading.textContent='工作分类分布 · 当前统计范围';distribution.append(heading,document.getElementById('apps'));document.getElementById('view-stats').prepend(distribution);
 const summary=document.getElementById('statsReport');if(summary)summary.style.display='none';
})();
