# Pelican Workbench V3.6-E — 局部角色动画精修

本轮只处理美术表现层，不修改业务状态、TODO、统计、Replay、API 或数据逻辑。

## 本轮目标
- 将鹈鹕从“整只角色切换姿态”进一步推进到局部微动画。
- 让眼神、视线与工作动作具有连续的小幅变化。
- 保留既有工作 / 专注 / 高强度 / 思考 / 喝咖啡 / 疲劳 / 休息状态。

## 新增资产
- `illustrations/pelican-eye-whites-v36.svg`：覆盖原角色瞳孔区域的独立眼白层。
- `illustrations/pelican-pupil-left-v36.svg`
- `illustrations/pelican-pupil-right-v36.svg`
- `illustrations/pelican-pupil-think-left-v36.svg`
- `illustrations/pelican-pupil-think-right-v36.svg`
- `illustrations/pelican-typing-marks-v36.svg`

## 新增表现控制
- `assets/visual-v36e.css`
- `assets/visual-v36e.js`

### 视线规则
- 阅读白板：视线轻微向左上。
- 思考：视线轻微向右上。
- 打字 / 高强度：视线略向下并有轻微游移。
- 喝咖啡：视线轻微偏移。
- 空闲：缓慢、随机的小幅视线游移。
- 疲劳 / 休息：回到中性位置并隐藏工作眼球层。

## 兼容性
- `prefers-reduced-motion` 下停止局部动画。
- 业务状态仍由原有 DOM / class 决定；V3.6-E 仅读取状态并更新 CSS 表现变量。
