(function(root){
  const nonnegative=v=>Math.max(0,Number(v)||0);
  function stories(s){return {pages:nonnegative(s.text_chars)/500,bookPercent:nonnegative(s.text_chars)/100000*100,meters:nonnegative(s.cursor_distance_px)*0.0254/96,focusBlocks:nonnegative(s.active_seconds)/1500};}
  const api={stories,nonnegative};root.LiteMath=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
