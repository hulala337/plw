/* Opt-in, bounded input-area adapter. No global input interception. */
(()=>{
 const pad=document.getElementById('characterPad'),opt=document.getElementById('characterOptIn'),status=document.getElementById('characterStatus');
 if(!Intl.Segmenter){status.textContent='当前浏览器不支持可见字符分段，计数未开启。';opt.disabled=true;return;}
 const segmenter=new Intl.Segmenter(undefined,{granularity:'grapheme'});
 let composing=false,submittedComposition=false,ignored=false,queue=[],sending=false;
 const day=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
 opt.onchange=()=>{pad.disabled=!opt.checked;if(!opt.checked){pad.value='';composing=false;}status.textContent=opt.checked?'只统计本输入区；文本不上传、不保存。':'已关闭，输入区内容已清空。';};
 async function send(){if(sending||!queue.length)return;sending=true;const item=queue[0];try{const r=await fetch('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item),signal:AbortSignal.timeout(8000)});if(!r.ok)throw Error();queue.shift();status.textContent='字符数量已保存；文本未上传。';if(typeof refresh==='function')refresh();}catch{status.textContent='数量尚未保存，请保持页面打开，稍后自动重试。';}finally{sending=false;}}
 function count(text){if(!opt.checked||!text)return;const count=Array.from(segmenter.segment(text)).length;if(count>10000){status.textContent='单次输入超出计数范围，未计入。';return;}queue.push({receipt_id:crypto.randomUUID(),source:'journal_typing_area',day:day(),count});send();}
 pad.addEventListener('compositionstart',()=>{composing=true;submittedComposition=false;});
 pad.addEventListener('compositionend',e=>{composing=false;if(!submittedComposition)count(e.data);submittedComposition=false;});
 pad.addEventListener('beforeinput',e=>{ignored=!['insertText','insertCompositionText','insertFromComposition','insertLineBreak'].includes(e.inputType);});
 pad.addEventListener('input',e=>{if(ignored||!opt.checked)return;if(e.inputType==='insertFromComposition'){count(e.data);submittedComposition=true;return;}if(composing||e.isComposing||e.inputType==='insertCompositionText')return;if(e.inputType==='insertText')count(e.data);else if(e.inputType==='insertLineBreak')count('\n');});
 setInterval(send,3000);
 window.addEventListener('beforeunload',e=>{if(queue.length){e.preventDefault();e.returnValue='';}});
})();
