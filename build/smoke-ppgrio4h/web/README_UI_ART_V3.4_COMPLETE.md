# Pelican Workbench V3.4 — Complete Art Stage

在 Stage 2 基础上一次完成剩余美术表现层：

4. 工作状态动画：工作/高强度/专注/Idle 微动作
5. TODO/DONE：完成微动画
6. 双显示器：读取现有 displayInfo，仅切换场景构图
7. Replay：复用同一办公室与鹈鹕资产，按回放时间切换昼夜/角色状态
8. 数据可视化微交互：时间轴、分析卡片的轻量动效

原则：不改 API、数据库、统计算法、TODO CRUD、回放控制等业务功能。新增 JS 只读取已有 DOM 状态，CSS 只负责表现。

安装：将 web 目录覆盖到现有项目的 web 目录。建议先保留原目录备份。
