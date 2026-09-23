# Pelican Workbench 全量美术资产目录

> 本目录以当前仓库、V3 设计参考和已经存在的视觉实现为基础整理。旧 SVG 主要作为现有结构参考；P0/P1 最终资产应重新生产为高质量原创插画。

## A. 品牌与启动资产

### A01 logo_primary
- 用途：应用主 Logo
- 内容：Pelican 头部/完整小角色 + Pelican Workbench 品牌识别
- 构图：方形安全区，主体居中
- 背景：透明
- 输出：SVG/PNG 双版本
- 要求：小尺寸仍保持喙、眼睛和轮廓清晰
- QA：16/24/32/64/128px 可识别

### A02 logo_compact
- 用途：托盘、标题栏、小尺寸入口
- 构图：Pelican 头像/头部
- 背景：透明
- QA：24px 仍可辨识

### A03 app_icon
- 用途：Windows EXE/快捷方式/任务栏
- 构图：强识别、无细碎装饰
- 输出：ICO + PNG 多尺寸
- QA：16–256px

### A04 logo_light
- 用途：深色背景
- 要求：浅色/高对比版本

### A05 logo_dark
- 用途：浅色背景
- 要求：深色/高对比版本

### A06 tray_icon
- 用途：Windows system tray
- 要求：单色/高识别版本，避免复杂插画

## B. Pelican 主角色系统

### B01 pelican_master
- 用途：角色母版
- 内容：完整站立/坐姿角色
- 透明背景
- 要求：建立唯一 Character Bible 基准
- 这是所有角色变体的 source of truth

### B02 pelican_working
- 默认状态
- relaxed、友好、轻微微笑

### B03 pelican_typing
- 坐在工作位
- 面向电脑
- 专注但不紧张

### B04 pelican_thinking
- 双翅/翅膀动作体现输入
- 可配 typing marks
- 不改变身体比例

### B05 pelican_neutral
- 轻微抬头/思考
- 眼神有方向

### B06 pelican_happy
- 开心完成工作
- 表情明显但自然

### B07 pelican_drinking_coffee
- 高专注状态
- 视觉重点在眼神和姿态

### B08 pelican_focused
- 长时间工作后的疲惫
- 不做夸张负面表情

### B09 pelican_tired
- 放松/休息
- 可用于低活动状态

### B10 pelican_resting
- 夜间/离开状态
- 柔和低对比

### B11 pelican_sleeping
- 手持/翅膀持杯
- 咖啡杯必须与场景体系一致

### B12 pelican_celebrating
- 完成目标/高分
- 可有少量星星/纸屑，但不能喧宾夺主

### B13 pelican_greeting
- 首次启动/欢迎
- 面向用户

### B14 pelican_encouraging
- 配“再坚持一下，你可以的！”类鼓励区域
- 预留文字安全区

### B15 pelican_mini
- Sidebar、卡片、空状态的小角色
- 必须来自 master 角色体系

## C. 核心办公室场景

### C01 office_master
- 用途：Dashboard Hero 主场景
- 内容：Pelican + desk + monitor/laptop + chair + plant + coffee + lamp + window + city/water
- 横向宽画幅
- 主体位于视觉焦点区域
- 预留 UI overlay 安全区

### C02 office_day
- 同一空间、傍晚光线
- 不允许改变家具布局

### C03 office_night
- 同一空间、夜景
- 窗外低亮度
- 室内灯光成为主光源

### C04 office_window_city_day
- 城市/水面/天空背景
- 不含角色
- 可独立替换天气

### C05 office_window_city_evening
- 日落/蓝调时间

### C06 office_window_city_night
- 夜间城市灯光

### C07 office_window_sunny
- 晴天状态

### C08 office_window_cloudy
- 阴天状态

### C09 office_window_rain
- 雨天状态
- 雨滴、玻璃水痕必须克制

### C10 office_window_snow
- 雪天状态
- 仅在产品环境支持时启用

### C11 office_window_fog
- 雾天/低能见度
- 低对比

### C12 office_desk
- 桌面基础层
- 供场景组合

### C13 office_chair
- 角色坐姿的固定椅子
- 与 master 场景透视一致

### C14 office_monitor_single
- 单显示器
- 与多显示器版本共享设计语言

### C15 office_monitors_dual
- 双显示器
- 用于多屏环境视觉状态

### C16 office_monitors_triple
- 三显示器
- 仅在需要时使用

### C17 office_laptop
- 笔记本电脑
- 屏幕可留空供 UI 合成

### C18 office_lamp
- 桌灯
- 日/夜版本可调整光照

### C19 office_plant
- 主植物
- 可有成长状态

### C20 office_plant_small
- 小型装饰植物

### C21 office_coffee_cup
- 咖啡杯
- 品牌小图形可选

### C22 office_books
- Better / Faster / Happier 书籍组
- 文字必须后期排版，不依赖生成模型直接生成文字

### C23 office_papers
- 文档/纸张
- 不生成真实可读内容

### C24 office_todo_board
- TO DO 板
- 空白可编辑版本
- 文本由前端渲染

### C25 office_done_board
- DONE 板
- 空白/贴纸组件

### C26 office_sticky_notes
- 便签组
- 颜色遵循品牌色

### C27 office_window_blinds
- 窗帘/百叶
- 可随时间改变明暗

### C28 office_foreground_decor
- 前景装饰层
- 低对比，不遮挡主体

## D. 工作状态/活动插画

### D01 state_productive
- 高效工作
- Pelican + 明确工作动作
- 积极但不兴奋过度

### D02 state_deep_focus
- 深度专注
- 简洁背景、强调眼神

### D03 state_document
- 文档编辑
- 文档/纸张/电脑视觉符号

### D04 state_web_search
- 网页检索
- 浏览器/搜索视觉隐喻

### D05 state_excel
- 表格/数据工作
- 网格、数据卡片，不生成真实数据

### D06 state_ppt
- 演示文稿制作
- 屏幕/幻灯片视觉隐喻

### D07 state_wechat
- 即时通讯
- 聊天气泡视觉隐喻
- 避免复制真实品牌界面

### D08 state_other_work
- 其他工作
- 泛化办公状态

### D09 state_idle
- 短暂空闲
- 中性

### D10 state_away
- 离开电脑
- Pelican 离开座位/伸懒腰等轻动作

### D11 state_break
- 休息
- 咖啡/拉伸/窗边

## E. Dashboard 主要插画

### E01 dashboard_hero
- 核心首屏 hero
- 最高美术等级
- Pelican 工作场景
- 宽画幅

### E02 dashboard_score_mascot
- 今日工作评分卡旁角色
- 小尺寸高辨识

### E03 dashboard_focus_mascot
- 专注 Session 卡片
- 体现持续专注

### E04 dashboard_todo_mascot
- 待办事项区域
- 轻量角色

### E05 dashboard_encouragement
- “再坚持一下，你可以的！”区域
- 留文字安全区

### E06 dashboard_empty
- 无数据/新用户
- 鼓励探索，不制造焦虑

## F. 时间轴与数据视觉资产

### F01 timeline_document
- 文档编辑状态标识
- 可为插画/小图标

### F02 timeline_web
- 网页检索

### F03 timeline_excel
- Excel/表格

### F04 timeline_ppt
- PPT

### F05 timeline_chat
- 即时通讯

### F06 timeline_other
- 其他工作

### F07 timeline_idle
- 发呆/离开

### F08 timeline_focus_marker
- 当前焦点时间标记
- 小 Pelican/羽毛元素可选

### F09 timeline_drag_handle
- 拖动时间轴的视觉提示
- 简洁图标，不使用复杂插画

## G. 统计分析

### G01 analytics_overview_mascot
- 统计页主插画
- Pelican + 数据元素

### G02 analytics_keyboard
- 键盘行为
- 图标级资产

### G03 analytics_mouse
- 鼠标行为
- 不使用“公里”作为视觉暗示，重点表现操作轨迹/活动强度

### G04 analytics_focus
- 专注分析
- 时间环/目标隐喻

### G05 analytics_activity
- 活动量
- 动态/节奏感

### G06 analytics_weekly
- 周报插画

### G07 analytics_monthly
- 月报插画

### G08 analytics_empty
- 无统计数据状态

## H. 成就与激励

### H01 achievement_first_day
- 第一天使用

### H02 achievement_focus
- 长时间专注

### H03 achievement_consistency
- 连续工作/稳定节奏
- 不鼓励不健康过劳

### H04 achievement_growth
- 成长/进步

### H05 achievement_complete
- 任务完成

### H06 achievement_streak
- 连续达成

### H07 achievement_master
- 总体成就
- 最高等级徽章/插画

## I. 设置/引导/隐私

### I01 onboarding_welcome
- 首次启动欢迎

### I02 onboarding_permission
- 输入监听/数据权限说明
- 视觉重点是隐私与可控

### I03 privacy_protection
- 隐私保护主插画
- shield + Pelican
- 明确“不记录输入内容，只统计工作行为数据”的视觉语义

### I04 data_export
- 数据导出

### I05 appearance_theme
- 主题与外观

### I06 startup
- 开机启动

### I07 about
- 关于我们

### I08 settings_empty
- 设置页空状态/辅助插画

## J. 空状态与错误状态

### J01 empty_no_data
- 新用户无数据

### J02 empty_no_activity
- 今天没有活动

### J03 empty_no_focus
- 尚未形成专注 Session

### J04 empty_no_todo
- 没有待办

### J05 error_generic
- 通用错误
- 不制造恐慌

### J06 error_permission
- 权限异常
- Pelican 帮助用户解决问题

### J07 error_service
- 服务异常

### J08 offline
- 离线状态

## K. 天气与时间氛围

### K01 weather_sunny
### K02 weather_cloudy
### K03 weather_rain
### K04 weather_snow
### K05 weather_storm
### K06 weather_fog

每项：
- 必须与办公室窗外场景一致
- 不生成可读天气文字
- 天气图形与主场景统一

## L. 装饰资产

### L01 feather
- Pelican 羽毛
- 品牌辅助元素

### L02 feather_cluster
- 小型羽毛组

### L03 cloud_small
### L04 cloud_large
### L05 sun
### L06 moon
### L07 stars
### L08 water_ripple
### L09 bird_silhouette
### L10 plant_leaf
### L11 coffee_steam
### L12 sparkle
### L13 soft_shadow
### L14 paper_texture
### L15 ambient_particles

这些允许较简化，可使用 SVG/程序绘制，但必须服从 Art Direction。

## M. 产品宣传与分享

### M01 promotional_hero
- Pelican Workbench 主宣传图
- 高质量完整场景

### M02 promotional_square
- 1:1 社交/分享

### M03 promotional_wide
- 横幅

### M04 product_screenshot_frame
- 产品展示背景/装置

### M05 qr_card_frame
- 二维码卡片背景
- 中心区域必须留空
- 不生成二维码本身

## N. Windows / Tray

### N01 tray_popup_hero
- 托盘菜单顶部 Pelican 小图

### N02 tray_open
- 打开主界面状态

### N03 tray_settings
- 设置状态

### N04 tray_running
- 运行中状态

### N05 tray_idle
- 空闲状态

## O. 动画分层资产

核心办公室和 Pelican 推荐拆层：
1. background sky
2. city/water
3. window
4. room base
5. desk
6. monitor
7. Pelican body
8. Pelican face
9. eyes
10. wing/action
11. props
12. foreground
13. weather
14. lighting
15. particles

要求：需要动画的核心资产必须优先提供可分层版本，而不是只有一张扁平图。

## P. 生产级衍生尺寸

核心资产至少准备：
- source/master
- desktop
- dashboard
- card
- small
- thumbnail

禁止通过极端放大低分辨率图片作为最终资源。


## 接力生产命名约定

B01 为唯一主风格锚点。B02/B03/B04/B07 与 C01/C02/C03 是当前首批接力生产序列，资产 ID 与 key 必须以 manifest 为准。历史文件名如与当前 manifest 不一致，不得据此创建新的 asset_id；应通过状态文件和人工审核记录完成迁移。
