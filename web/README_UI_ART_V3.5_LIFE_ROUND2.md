# Pelican Workbench V3.5 Life Round 2

本轮继续 V3.5 美术资产改造，主题为「角色 ↔ 工作空间关系」。

## 新增
- pelican-desk-life.svg：桌面纸张、键盘微光、屏幕环境光、任务完成提示等独立美术资产
- visual-v35-life.js：仅监听既有 TODO DOM 与场景 class，不改变业务状态
- visual-v35-life.css：桌面交互动画、白板注意力、任务完成庆祝微动画

## 设计原则
- 不修改 TODO CRUD、统计、API、回放及数据逻辑
- CSS 不绘制角色；动画主要作用于独立插画资产
- 动画低幅、随机感强，避免机械循环
- prefers-reduced-motion 下自动降级
