# Pelican Workbench V3.6-D — Visual Quality Refinement

本阶段只处理视觉表现，不修改业务/API/数据库/TODO/统计/Replay 数据逻辑。

## 本轮目标
- 解决环境分层后的“SVG 拼贴感”
- 增强窗玻璃、显示器玻璃、桌面漆面等材质高光
- 增加显示器/白板/桌面物件的接触阴影，建立共同空间
- 白板保留真实 DOM 内容，同时使用独立纸张纹理资产
- 缩小并重新校正键盘、鼠标、咖啡、笔记本比例
- 增加低幅度、不同相位的环境微运动，避免整场景机械同步
- 保留 prefers-reduced-motion

## 新增资产
- `office-glass-v36d.svg`
- `office-contact-shadows-v36d.svg`
- `office-board-paper-v36d.svg`
- `office-screen-reflection-v36d.svg`

## 重要实现
- `office-board-v36.svg` 不再叠加到主场景，避免与交互式 `.board` 产生双白板。
- `.board` 的文字/checkbox/计数仍来自原业务 DOM；本阶段只改变其纸张材质与视觉层次。
- `visual-v36d.js` 仅读取现有 scene class/data-time/data-weather，不写入业务状态。
