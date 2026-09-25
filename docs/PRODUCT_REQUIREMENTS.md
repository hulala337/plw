# Pelican Workbench 产品需求与功能完整基线

> 版本基线：V3.6.0  
> 状态基线：GitHub `main`  
> 文档性质：产品需求、功能边界、数据链路、UI、世界系统、美术系统、隐私、安全、发布与验收的统一说明。  
> 目的：避免“代码实现了一个功能、UI 描述了另一个功能、资产生产又按照第三个功能制作”的情况。

## 1. 产品定义

Pelican Workbench（鹈鹕工作台）是一款 Windows 本地工作伴侣应用。

它不是单纯的时间统计器，也不是单纯的桌面宠物。完整产品由：

1. **真实工作采集**：时间、键盘行为计数、鼠标行为、Session、显示器。
2. **数据分析**：Today、Timeline、Stats、Replay。
3. **轻量工作辅助**：Todo、导出、设置、Health、Self Test。
4. **成长系统**：XP、Level、Achievement、Unlock、Collection、Equipment。
5. **工作世界**：Scene、Pelican、Outfit、Accessory、Decoration、Effect、Environment。
6. **美术表现**：统一角色、办公室、天气/时间氛围、状态动画和微交互。
7. **Windows 产品能力**：Tray、开机自启动、本地 WebView、安装包、完整性校验。

最终闭环：

`真实工作 → Tracker → SQLite → Analytics → XP/Level/Achievement → Unlock/Equipment → Scene/Pelican → 实时工作世界`

## 2. 功能总览

| 产品域 | 功能 | 当前代码 | 当前 UI | 目标 |
|---|---|---:|---:|---:|
| Tracker | 键盘计数/字符数 | 已实现 | 已接入 | 稳定 |
| Tracker | 鼠标移动/点击/滚轮 | 已实现 | 已接入 | 稳定 |
| Tracker | 活跃/空闲判断 | 已实现 | 已接入 | 稳定 |
| Session | 工作 Session | 已实现 | 已接入 | 稳定 |
| Display | 多显示器识别/跨屏 | 已实现 | 已接入 | 稳定 |
| Storage | SQLite 持久化/WAL | 已实现 | 不直接展示 | 稳定 |
| Analytics | Today | 已实现 | 已接入 | 稳定 |
| Analytics | Timeline | 已实现 | 已接入 | 稳定 |
| Analytics | Stats 今日/周/月 | 已实现 | 已接入 | 稳定 |
| Analytics | Replay | 已实现 | 已接入 | 稳定 |
| Todo | 增删改/完成 | 已实现 | 已接入 | 稳定 |
| Export | CSV/XLSX | 已实现 | 已接入 | 稳定 |
| Growth | XP/Level | 已实现 | 已接入 | 完整成长闭环 |
| Growth | Achievement | 已实现 | 已接入 | 扩展成就目录 |
| Growth | Unlock | 已实现 | 已接入 | 扩展内容目录 |
| Collection | Pelican/Outfit/Accessory/Scene/Decoration/Effect | 已实现数据层 | 已接入装备交互 | 完整装备闭环验收 |
| Equipment | 装备持久化与校验 | 已实现 API/DB | 已接入成长中心选择 | Windows 重启/异常路径验收 |
| World | Scene/Pelican/Outfit/Decoration/Effect 投影 | 已实现 | Today 已消费 | 完整动态世界验收 |
| Weather | 设置开关 | 已实现 | 已接入 | 真实天气/收藏天气需单独定义 |
| Time | Day/Dusk/Night | 部分数据模型 | 视觉层可消费 | 完整环境状态机 |
| Visual | 角色/办公室分层资产 | 已有 V3.6 资产体系 | 已接入 | 最终原创插画资产 |
| Animation | 局部眼神/打字等微动画 | 已有 V3.6-E | 已接入 | 状态驱动动画系统 |
| Tray | Windows Tray | 已实现 | 系统级 | 完善菜单与状态 |
| Startup | Windows 开机自启动 | 已实现 | Settings | 稳定 |
| Privacy | 不保存实际输入/窗口标题/URL | 已实现边界 | Settings 已说明 | 持续保持 |
| Health | Listener/Tracker/DB/Web 健康 | 已实现 | Settings 已有诊断面板 | Windows runtime 验收 |
| Self Test | DB + hooks + display + web | 已实现 | 命令行 | 发布前自动门禁 |
| Security | Ed25519 资源完整性 | 构建链已设计 | 不展示 | 发布链稳定 |
| Release | PyInstaller/Inno Setup | 已实现 | 安装包 | 完整发布验收 |
| Donation | 微信二维码自愿支持 | 已实现 UI | 已接入 | 保持非核心能力 |

**“已实现”不等于“已验收”。** 最终完成必须以运行时证据和对应 Acceptance Matrix 为准。

## 3. Tracker：真实工作采集

### 3.1 键盘

允许记录：
- 总按键次数
- 可打印字符数量
- Backspace
- Delete
- Enter
- Space
- 其他按键分类

禁止记录：
- 实际键入文本
- 剪贴板正文
- 聊天正文
- 文档正文

### 3.2 鼠标

记录：
- 光标移动距离，单位 px
- 左/右/中键点击
- 滚轮事件与滚动距离
- 活动事件
- 跨显示器切换次数

鼠标距离必须基于虚拟桌面像素坐标连续计算，不得用一个固定前端换算比例冒充真实物理距离。

### 3.3 工作/空闲

Tracker 根据最近一次真实输入和用户设置的 idle threshold 判断 active/idle。

要求：
- idle 时间不能计入有效工作时间
- idle 不产生工作 XP
- 从 idle 恢复后可继续当前工作链
- 数据库异常不能杀死监听线程
- 高速鼠标移动不能造成高频数据库写入风暴

### 3.4 Session

Session 至少记录：
- 开始
- 结束
- 有效工作秒数
- break/idle 信息
- 活动事件数
- 工作类别序列
- 结束原因

必须支持：
- 正常结束
- idle 结束
- 应用关闭
- 崩溃/重启后的 stale session recovery
- 跨午夜 Session

## 4. 多显示器

必须真实读取 Windows 显示器布局：

- 数量
- 每块显示器矩形
- 虚拟桌面坐标
- 当前鼠标所在显示器
- 显示器拓扑变化

必须正确支持：
- 左/上方负坐标
- 不同分辨率
- 不同 DPI/缩放
- 跨屏移动
- 插拔/重新排列

显示器数据既服务 Analytics，也服务 World：
- 单屏 → 单屏工作室
- 双屏 → 双屏场景（解锁后）
- 三屏及以上 → 未来可扩展场景规则

## 5. SQLite 与数据一致性

核心数据必须本地持久化。

核心表域：
- daily
- activity_slices
- app_usage
- focus_sessions
- todos
- settings
- progress_profile
- progress_events
- unlocks
- achievements
- equipment
- scenes
- pelicans
- outfits
- accessories
- decorations
- effects

要求：
- 应用重启不丢失
- WAL/busy timeout/foreign keys 正确启用
- pending 数据只有在数据库提交成功后才能清空
- DB 暂时不可写时 Tracker 继续运行并保留待写数据
- Forget Today 清理今天相关统计和 Session，但**不能清除 lifetime Growth**
- 成长奖励必须幂等，刷新/重启不得重复领奖

## 6. Analytics

### Today
默认入口，回答“我现在的工作室发生了什么”：
- 当前工作/空闲
- 今日有效时间
- 当前 Session
- 键盘/鼠标统计
- 显示器
- Timeline 摘要
- Todo
- 当前 Scene/Pelican
- 工作类型分布

### Timeline
24 小时工作节奏：
- active
- idle
- Session
- 分类片段
- 当前时间 scrub
- zoom
- Now

### Stats
时间范围：
- Today
- Week
- Month

至少展示：
- 工作时长
- 趋势
- 工作类别
- Session
- 活跃/空闲
- 输入行为统计

### Replay
Replay 是行为分类的时间回放，不是屏幕录像。

不得保存或回放：
- 实际输入
- 网页正文
- 聊天正文
- 文档正文
- 屏幕画面

## 7. Todo

Todo 是轻量工作辅助，不应成为复杂项目管理器。

必须支持：
- 创建
- 完成
- 删除
- 持久化
- Today 展示
- DONE 状态
- 完成事件最多奖励一次 XP

未来可扩展：
- 优先级
- 截止时间
- 标签
- 与 Achievement 联动

但扩展前必须保持当前轻量定位。

## 8. Growth

### XP
主要来源：
- 有效工作时间
- 有效 Session
- Todo 完成
- Achievement
- 连续工作/里程碑

禁止：
- idle 刷 XP
- 刷新重复领奖
- 同一 Todo 完成事件重复领奖
- 同一 Achievement 重复领奖

### Level
Level 必须对应真实内容解锁，而不是只显示数字。

### Achievement
初始成就至少覆盖：
- First Session
- 10 Hours
- 100 Hours
- Multi Monitor
- 7 Day Streak

未来继续增加长期行为里程碑。

### Unlock
可解锁：
- Scene
- Pelican
- Outfit
- Accessory
- Decoration
- Effect

Unlock 必须：
- 有明确 required_level
- 幂等
- 未解锁不能装备
- 与 Collection 状态一致

## 9. Collection 与 Equipment

Collection 是“我拥有什么”；Equipment 是“我现在使用什么”。

Collection 分类固定为：
- Pelicans
- Outfits
- Accessories
- Scenes
- Decorations
- Effects
- Achievements

Equipment 必须支持：
- Scene
- Pelican
- Outfit
- Accessory
- 多个 Decoration
- Effect

规则：
- 默认装备必须存在
- 锁定物品不可装备
- 未知 ID 不可装备
- 一个 Decoration 不得覆盖另一个 Decoration
- 重启后装备保持
- World 使用 Equipment 生成当前世界投影

**当前状态：Equipment 已接入成长中心的可操作选择界面，并通过 `/api/equipment` 持久化；仍需完成 Windows 重启、锁定项、未知 ID、多装饰共存等运行时验收。**

## 10. World：动态工作世界

World 由数据组合，而不是一张不可变背景：

`Scene + Environment + Time + Weather + Desk + Monitors + Decorations + Lighting + Effects + Pelican`

### Scene
至少：
- 基础 Office
- Dual Monitor Office
- Dusk Office
- 后续 Night/Rain/Snow 等环境变体

### Time
目标状态：
- Day
- Dusk
- Night

### Weather
必须区分：
1. **真实天气数据**
2. **可收藏/可装备的视觉天气**

当前代码已有 weather_enabled 设置、Scene weather 字段，以及本地天气视觉桥接；这仍不等于已经完成真实天气服务。未来接入真实天气时必须定义：
- 数据源
- 更新频率
- 离线 fallback
- 城市/位置来源
- 隐私边界

### World 状态驱动
示例：
- active → Working
- idle → Resting
- 长时间工作 → Tired
- 完成任务 → Celebration
- 多显示器 → Dual Monitor Scene
- 夜间 → Night Scene

## 11. Pelican IP 系统

Pelican 不是一张静态图，而是可组合角色：

`Body + Outfit + Accessory + Expression + Animation + Interaction`

基础状态：
- Working
- Focused
- Thinking
- Resting
- Tired
- Coffee
- Happy
- Sleepy
- Greeting
- Celebrating

必须保持：
- 同一头部/身体比例
- 同一喙形
- 同一眼距
- 同一羽毛轮廓
- 翅膀始终是鹈鹕翅膀，不得变成人手
- 同一主要服装/品牌视觉语言

状态变化应尽量由真实工作状态驱动，而不是无意义随机播放。

## 12. 美术系统

B01 是唯一角色身份/风格锚点。

美术最终目标：
- 高质量原创 2D/2.5D 插画
- 柔和光影
- 真实空间层次
- 温暖、聪明、轻松、有陪伴感
- 角色与办公室长期一致

办公室必须保持：
- 窗户比例
- 桌面语言
- 植物/灯具/杯子体系
- 城市/水面背景逻辑
- 光照方向

禁止：
- 几何 SVG 冒充最终角色/场景
- generic AI mascot
- 不同资产风格漂移
- 随机文字/乱码
- 角色比例漂移

美术资产生产必须遵守：
- Manifest
- Character Bible
- Art Direction
- Production Rules
- Human Review
- Handoff/Sync

Asset Catalog 是**完整资产库存**；STATE.production_sequence 是**当前阶段的生产顺序**。两者不能混为一谈。

## 13. UI 与交互可靠性

主视图：
- Today
- Replay
- Timeline
- Stats
- Growth
- Settings

Settings 至少：
- 开机自启动
- idle threshold
- 显示器信息
- 天气开关
- 桌面宠物/相关视觉开关
- 隐私说明
- 删除今日数据
- 支持作者
- 版本信息

必须保证：
- 所有主导航可点击
- 二级入口可达
- 空数据不导致 JS 初始化失败
- 不存在的 DOM 元素不得让整个事件系统崩溃
- 装饰层 pointer-events 不得遮挡交互层
- reload 后状态保持
- reduced-motion 可关闭动画

## 14. Health 与 Self Test

Health 不是“窗口还开着”。

至少检查：
- Keyboard Listener
- Mouse Listener
- Tracker thread
- SQLite
- API/Web server
- Display detection

Self Test 必须覆盖：
`真实 Hook → Tracker → Pending → SQLite → API → Frontend`

并验证：
- P0 表存在
- Growth 表/目录完整
- 默认装备存在
- API contract 存在
- 测试数据结束后清理

最终发布前必须有 Windows runtime evidence，不能只依赖静态检查。

## 15. Privacy

默认本地优先。

允许：
- 按键数量
- 字符数量
- 鼠标距离/点击/滚轮
- 时间
- Session
- 显示器信息
- 工作类别统计

禁止：
- 实际键盘文本
- 窗口标题
- 文件名
- URL
- 网页正文
- 聊天正文
- 文档正文
- 屏幕录像

Export 同样遵守该边界。

## 16. Windows 产品能力

必须支持：
- 本地 FastAPI 服务
- pywebview 窗口
- Windows Tray
- 开机自启动
- 关闭主窗口回 Tray
- Tray Quit 才真正退出
- 本地数据库
- one-file EXE
- Inno Setup 安装包

发布链：
`main → build_release.bat → validation → build → installer → install → launch → Self Test`

## 17. 安全与完整性

正式发布：
- Ed25519 对关键资源生成签名清单
- 启动时校验完整性
- 私钥只保存在用户机器安全路径
- 不进入 Git
- 不进入源码包
- 不进入安装包

可选：
- Windows Authenticode

必须明确：离线 EXE 无法做到绝对不可逆向，完整性校验的目标是发现常见资源篡改并提高二次打包成本。

## 18. 非核心能力

以下功能不得影响核心工作记录链路：
- Donation/微信二维码
- 装饰性动画
- 纯视觉天气效果
- 市场宣传图
- 非关键装饰资产

这些能力故障时，Tracker、SQLite、Analytics、Todo、Growth 核心链路仍必须工作。

## 19. 开发优先级

### P0：可靠性
Tracker、SQLite、Session、多显示器、API、主导航、Todo、Stats、Replay、Settings、Self Test、发布链。

### P1：成长产品
XP、Level、Achievement、Unlock、Collection、Equipment、World Projection。

### P2：世界内容
更多 Scene、Pelican、Outfit、Decoration、Weather、Effects、状态联动。

### P3：视觉精修
原创角色、原创办公室、材质、空间、光影、局部动画、微交互。

原则：P0 未稳定，不用视觉工作掩盖功能问题。

## 20. 文档与事实来源

事实优先级：

1. GitHub `main` 的代码与运行结果
2. `docs/PRODUCT_REQUIREMENTS.md`
3. `docs/P0_ACCEPTANCE_MATRIX.md`
4. `docs/P1_ACCEPTANCE_MATRIX.md`
5. `docs/P2_ACCEPTANCE_MATRIX.md`
6. `docs/WORKBENCH_PRODUCT_ARCHITECTURE.md`
7. UI/美术历史说明文件

历史版本说明不能覆盖当前代码事实。

任何新功能必须回答：
1. 属于哪个 Domain？
2. 数据从哪里来？
3. 是否持久化？
4. 是否影响 XP/Unlock？
5. 是否影响 Scene？
6. 是否影响 Pelican？
7. 是否需要 API？
8. 是否需要 Self Test？
9. 是否改变隐私边界？
10. 是否影响发布？

## 21. 完成定义 Definition of Done

一个功能只有同时满足以下条件才算完成：

- 需求有明确说明
- 数据链路明确
- API（如需要）存在并有测试
- UI 可操作
- 状态持久化正确
- 重启后正确恢复
- 空数据/异常路径正确
- 隐私边界符合规定
- Self Test/Acceptance 有对应覆盖
- Windows 运行时验证通过
- 若涉及视觉，有对应 Asset ID 和人工审核
- 若涉及发布，安装包验证通过

**最终目标不是“页面看起来完成”，而是：**

`真实工作 → 可靠记录 → 正确分析 → 合理成长 → 内容解锁 → 工作世界变化 → 重启后仍然存在`

这才是 Pelican Workbench 的完整产品闭环。
