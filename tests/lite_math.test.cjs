const assert=require('node:assert/strict');
const {stories}=require('../web/assets/lite-math.js');
assert.deepEqual(stories({}),{pages:0,bookPercent:0,meters:0,focusBlocks:0});
const source={text_chars:100000,cursor_distance_px:96000,active_seconds:3000};
const result=stories(source);assert.equal(result.pages,200);assert.equal(result.bookPercent,100);assert.ok(Math.abs(result.meters-25.4)<1e-9);assert.equal(result.focusBlocks,2);assert.equal(source.cursor_distance_px,96000);
assert.equal(stories({text_chars:-1}).pages,0);
console.log('Story conversions: PASS');
