# Pelican Workbench 工作台产品架构与功能基线

> 文档性质：产品架构基线（Product Architecture Baseline）
>
> 版本基线：V3.6.0 → 下一阶段架构按 V4 产品结构演进
>
> 用途：本文件是 Pelican Workbench 后续产品设计、代码开发、功能验收、视觉重构和发布检查的长期对照标准。任何新增功能或重构，都应先判断其属于哪个产品域，并检查是否破坏本文定义的核心链路。

---

## 1. 产品定位

**Pelican Workbench（鹈鹕工作台）**不是单纯的电脑使用时间统计工具，而是：

> **一个会随着用户真实工作而成长的个人工作空间。**

产品由四个相互连接的层组成：

1. **工作数据层**：真实记录时间、鼠标、键盘、显示器和工作 Session。
2. **工作分析层**：Today、Timeline、Stats、Replay。
3. **成长系统**：XP、Level、Achievement、Unlock、Collection。
4. **世界层**：Scene、Pelican、Decoration、Weather、Environment。

核心闭环：

```
真实工作
  ↓
Mouse / Keyboard / Time / Display
  ↓
Tracker
  ↓
SQLite
  ↓
Analytics
  ↓
XP / Level / Achievement
  ↓
Unlock
  ↓
Scene / Pelican / Decoration
  ↓
越来越丰富的工作室
```

---

## 2. 一级产品结构

主导航建议保持少而清晰，避免把所有功能平铺：

### 🏠 工作台（Today）

软件默认入口，负责实时工作状态：

- 当前工作 / 空闲状态
- 今日有效工作时间
- 当前 Session
- 鼠标移动距离（px）
- 鼠标点击
- 键盘按键 / 字符统计
- 当前显示器
- 显示器数量
- Timeline 摘要
- Todo
- 当前场景
- 当前鹈鹕状态
- 快速操作

Today 的定位是**“我的工作室现在发生了什么”**，而不是单纯数字仪表盘。

### 📈 数据（Analytics）

统一承载：

- Timeline
- Stats
- Replay

用于理解“今天/这一段时间是怎样工作的”。

### 🐦 成长（Growth）

统一承载：

- Overview
- XP / Level
- Pelican
- Scenes
- Collection
- Achievements
- Unlocks

这是产品长期使用和内容成长的核心模块。

### 🛠️ 工具（Tools）

统一承载：

- Todo
- Export
- Health
- Self Test

### ⚙️ 设置（Settings）

统一承载：

- Tracker
- Idle
- 开机自启动
- 数据
- 外观
- 通知
- 系统行为

---

## 3. 核心工作数据系统

### 3.1 鼠标

必须真实监听并实时进入数据链路：

- 鼠标移动距离
- 鼠标点击
- 最后鼠标位置
- 当前显示器
- 显示器切换

鼠标距离统一使用 **px（像素）**，不使用 km 等不适合桌面输入设备的物理距离单位。

### 3.2 键盘

只统计行为，不保存实际输入内容：

- 总按键次数
- 字符数量
- Backspace
- Delete
- Enter
- Space
- 其他按键

**隐私原则：不保存用户实际键盘输入文本。**

### 3.3 工作 / 空闲

记录：

- 最后输入时间
- 当前状态
- idle threshold
- 工作 Session
- 空闲时段
- Session 开始/结束

必须避免重复计算 idle 时间。

### 3.4 Session

每个有效工作 Session 应记录：

- 开始时间
- 结束时间
- 持续时间
- 活动数据
- 显示器信息（必要时）
- 跨午夜 Session

### 3.5 多显示器

自动识别：

- 1 / 2 / 3+ 显示器
- 每块显示器位置
- 尺寸
- 虚拟桌面坐标
- 当前鼠标所在显示器
- 显示器拓扑变化

必须正确支持：

- 左侧显示器负坐标
- 不同分辨率
- 不同 DPI / 缩放
- 跨屏鼠标移动

DPI awareness 应在监听器启动前正确建立。

---

## 4. 数据持久化

核心数据使用 SQLite。

原则：

- 应用重启后数据仍存在
- SQLite WAL
- busy_timeout
- foreign keys
- pending 数据可靠落盘
- 只有数据库提交成功后才能减少 pending
- 数据库异常不能直接杀死 Tracker
- Forget Today 必须同时清理相关状态

建议的数据域：

```
Core
├── daily_stats
├── input_events
├── sessions
└── monitor_layouts

Progress
├── profile
├── xp
├── levels
├── achievements
├── unlocks
└── equipment

World
├── scenes
├── decorations
├── pelicans
└── outfits
```

---

## 5. Analytics

### Today

实时状态和当日概览。

### Timeline

显示一天中：

- 工作
- 空闲
- Session
- 重要状态变化

### Stats

支持按时间范围分析：

- 工作时间
- 空闲时间
- 鼠标活动
- 键盘活动
- Session
- 趋势

### Replay

根据记录的数据重新表现工作活动。

Replay **不是屏幕录像**，不保存网页、聊天或文档内容。

---

## 6. Growth：成长系统

成长系统是 Pelican Workbench 的核心产品能力之一。

### 6.1 XP

XP 应主要来自真实有效使用：

- 有效工作时间
- 有效工作 Session
- 完成 Todo
- 连续使用
- 成就
- 特殊里程碑

不能设计成简单挂机刷经验机制。

### 6.2 Level

等级必须对应真实内容变化，例如：

- 新桌面物件
- 新鹈鹕动作
- 新装饰
- 新场景组件
- 新外观
- 新特殊环境

等级不是单纯的数字。

### 6.3 Achievement

成就用于记录长期里程碑和发现隐藏内容，例如：

- First Session
- Night Worker
- Multi Monitor
- 10 / 100 Hours
- 7 Day Streak
- Long Haul

完成成就可以触发 XP 或内容解锁。

### 6.4 Unlock

解锁对象包括：

- 场景
- 场景组件
- 鹈鹕形态
- 服装
- 配饰
- 动作
- 装饰
- 特殊环境
- 特殊效果

### 6.5 Collection

统一展示：

- 已拥有
- 未拥有
- 当前装备

分类：

- Pelicans
- Outfits
- Accessories
- Scenes
- Decorations
- Effects
- Achievements

---

## 7. Scene：动态工作世界

场景不应设计成一张不可组合的背景图片。

Scene 是由多个组件组成的数据对象：

```
Scene
├── Base
├── Environment
├── Weather
├── Time
├── Desk
├── Monitors
├── Decorations
├── Lighting
└── Special Effects
```

因此可以组合：

```
Office
+ Night
+ Rain
+ Triple Monitor
+ Plant
+ Coffee
= Rainy Night Office
```

### 时间状态

至少：

- Day
- Dusk
- Night

### 天气状态

至少：

- Clear
- Cloud
- Rain
- Snow
- Mist

未来可扩展特殊天气，但必须把：

**真实天气状态**

与

**可收藏/可选择的游戏内容**

区分开。

---

## 8. 多显示器与场景联动

显示器识别不仅是统计功能，也应成为世界系统输入。

例如：

- 单屏 → Single Monitor Scene
- 双屏 → Dual Monitor Scene
- 三屏 → Triple Monitor Scene

首次检测双屏/三屏还可以触发相关 Achievement / Unlock。

视觉表现必须与实际显示器数量一致。

---

## 9. Pelican：鹈鹕系统

鹈鹕是产品核心 IP，不是一个静态图片。

建议拆成：

```
Pelican
├── Body
├── Outfit
├── Accessory
├── Expression
├── Animation
├── Interaction
└── Personality
```

### 基础状态

- Working
- Focused
- Thinking
- Resting
- Tired
- Coffee
- Happy
- Sleepy

### 动态表现

可以包含：

- 眼睛
- 瞳孔
- 眨眼
- 思考眼神
- 打字动作
- 微动作
- 休息
- 喝咖啡
- 看窗外
- 庆祝

这些状态应尽可能由真实工作状态驱动，而不是随机播放。

---

## 10. 鹈鹕成长与解锁

鹈鹕应该拥有自己的成长体系：

```
Level
  ↓
新形态 / 新动作 / 新装备
  ↓
新的互动表现
```

可解锁内容包括：

- 新鹈鹕形态
- 工作主题鹈鹕
- 学习主题鹈鹕
- 特殊主题鹈鹕
- Outfit
- Accessory
- 特殊动作
- 特殊表情

长期目标是让用户感觉：

> **这是“我的鹈鹕”，而不是软件里的一个固定角色。**

---

## 11. Scene 与 Pelican 联动

场景和鹈鹕应该互相影响。

例如：

- 夜间 + 夜间主题鹈鹕
- 雨天 + 咖啡互动
- 长时间工作 + Tired
- 完成任务 + Celebration
- 空闲 + Resting
- 多显示器 + 特殊工作姿态

目标是形成：

**环境、角色、真实工作状态三者统一的实时世界。**

---

## 12. Todo

Todo 是轻量工作辅助功能：

- 添加
- 完成
- 持久化
- 与成长系统联动

完成 Todo 可以成为 XP / Achievement 的来源，但不能喧宾夺主。

---

## 13. Health / Self Test

### Health

必须反映真实运行状态：

- Tracker
- Keyboard Listener
- Mouse Listener
- Database
- API
- Last Event

不能把“程序窗口还开着”误认为所有功能健康。

### Self Test

必须验证真实链路：

```
真实 Hook
 ↓
Tracker
 ↓
Pending
 ↓
SQLite
 ↓
API
```

自检应在结束后清理测试数据。

---

## 14. 前端交互可靠性

这是 P0 基础要求。

所有主导航和二级页面必须：

- 可以点击
- 可以切换
- 可以返回
- 控件存在时正常绑定
- 控件不存在时不能因为 null DOM 操作导致整个 JS 初始化失败

装饰性 SVG / 场景图层必须：

```
pointer-events: none
```

真正的按钮和交互层必须处于可点击层级。

**任何一个不存在的 DOM 元素都不能让整个前端事件系统崩溃。**

---

## 15. 视觉系统原则

产品视觉不是“统计软件 + 背景图”。

核心视觉目标：

- 温暖
- 可爱
- 有空间感
- 有层次
- 有生活感
- 鹈鹕是角色主体
- 工作室是长期成长的世界

视觉系统必须逐步向最初的设计参考稿统一。

技术上应避免继续无序叠加大量临时 CSS / JS 层。

最终应逐渐收敛为：

```
World Renderer
Pelican Renderer
UI Components
Theme / Environment
Animation
```

而不是多个互相覆盖的 V3.x 视觉补丁。

---

## 16. 技术架构

建议明确划分 Domain：

```
pelican_workbench/
│
├── core/
│   ├── tracker
│   ├── sessions
│   ├── input
│   └── monitors
│
├── analytics/
│   ├── dashboard
│   ├── timeline
│   ├── stats
│   └── replay
│
├── progression/
│   ├── xp
│   ├── levels
│   ├── achievements
│   └── unlocks
│
├── world/
│   ├── scenes
│   ├── decorations
│   ├── weather
│   └── environments
│
├── pelican/
│   ├── characters
│   ├── outfits
│   ├── expressions
│   └── animations
│
└── infrastructure/
    ├── database
    ├── api
    ├── health
    └── self_test
```

原则：

> **数据层、成长层、世界层、渲染层解耦。**

Tracker 不直接操作 SVG。

数据库不直接决定 CSS。

这样未来更换美术资源不会破坏统计系统。

---

## 17. 隐私边界

程序可以记录：

- 按键数量
- 字符数量
- 鼠标移动距离
- 鼠标点击
- 时间
- Session
- 显示器信息

程序不应记录：

- 实际键盘输入文本
- 聊天正文
- 网页正文
- 文档正文
- 屏幕录像

---

## 18. 发布标准

发布链路必须保持一致：

```
GitHub main
 ↓
build_release.bat
 ↓
repair / validation
 ↓
PyInstaller
 ↓
Inno Setup
 ↓
安装包
 ↓
安装
 ↓
启动
 ↓
Self Test
```

版本、源码、构建脚本、安装包说明必须保持一致。

发布前至少检查：

1. 能启动
2. 主导航可点击
3. 二级页面可点击
4. Tracker 正常
5. Mouse 正常
6. Keyboard 正常
7. SQLite 正常
8. Dashboard 正常
9. 多显示器识别正常
10. Self Test 正常
11. Progress 数据不会丢失
12. 安装包可以正常启动

---

## 19. 当前开发优先级

### P0：功能可靠性

- 主导航
- 二级页面
- API
- Tracker
- 鼠标
- 键盘
- SQLite
- Session
- 多显示器
- Self Test
- 发布链路

### P1：产品架构

- Growth
- XP
- Level
- Achievement
- Unlock
- Collection
- Scene 数据模型
- Pelican 数据模型

### P2：世界内容

- 场景升级
- 鹈鹕升级
- 装饰
- Outfit
- Animation
- Weather
- Scene / Pelican 联动

### P3：视觉精修

- 恢复最初设计语言
- 场景空间感
- 光影
- 动画
- 细节
- 美术资产统一

**原则：P0 未稳定之前，不应继续用视觉开发掩盖功能问题。**

---

## 20. 产品成功标准

最终版本应该让用户获得这样的体验：

> 我打开的是一个属于我的工作室。

> 我开始工作，鹈鹕开始工作。

> 我的真实工作会被记录，但不会记录我的私人内容。

> 工作越久、使用越久，我的鹈鹕和工作室就越丰富。

> 今天的数据告诉我“我做了什么”。

> Timeline / Stats 告诉我“我是怎样工作的”。

> Growth 告诉我“我成长了什么”。

> Scene / Pelican 告诉我“我的工作世界变成了什么”。

最终目标：

**让真实工作行为 → 数据 → 成长 → 内容解锁 → 工作世界变化，形成长期闭环。**

---

## 21. 架构变更规则

以后每加入一个功能，至少回答：

1. 它属于哪个 Domain？
2. 它的数据从哪里来？
3. 它是否需要持久化？
4. 它是否影响 XP / Unlock？
5. 它是否影响 Scene？
6. 它是否影响 Pelican？
7. 它是否需要 API？
8. 它是否需要 Self Test？
9. 它是否破坏隐私边界？
10. 它是否影响发布链路？

如果一个功能无法回答这些问题，不应直接堆进现有页面。

---

**本文件是 Pelican Workbench 后续开发的产品架构基线。**

开发代码、UI、数据库、API、视觉系统和发布流程出现冲突时，应优先检查并更新本文件，再修改实现，避免项目重新进入“功能、视觉和版本互相打架”的状态。
