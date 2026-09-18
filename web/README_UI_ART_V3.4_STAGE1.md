# Pelican Workbench V3.4 — 美术系统重构 · 第一阶段

本阶段只修改 UI / 美术层，不修改业务功能、API、数据结构或统计逻辑。

## 已完成：1. 场景插画资产系统
- 主办公室由 CSS 几何绘制改为独立 `SVG` 插画资产。
- 白天 / 夜晚使用两套独立场景资产。
- 雨天增加独立雨景 overlay 资产。
- 保留原有 `#scene` 节点，业务代码仍可继续控制工作状态。

## 已完成：2. 鹈鹕角色资产系统
- 主鹈鹕不再使用 inline SVG / CSS 几何绘制。
- 工作、疲劳、休息使用独立角色资产。
- Sidebar / Right Rail / Replay 统一使用同一角色体系。
- CSS 仅负责资产组合、状态显隐和微动画，不负责绘制角色。

## 本阶段新增资产
`web/assets/illustrations/`
- `office-day.svg`
- `office-night.svg`
- `rain.svg`
- `pelican-working.svg`
- `pelican-tired.svg`
- `pelican-resting.svg`
- `pelican-mini.svg`

## 后续 3—8 阶段
3. 天气 / 昼夜环境系统
4. 工作行为 → 场景微动画
5. Focus / Idle → 角色状态动画
6. TODO → 办公室物件动画
7. 单 / 双显示器场景变化
8. Replay 与时间轴场景化

原则：以上阶段继续保持业务功能不变，只增强已有数据和状态的视觉表达。
