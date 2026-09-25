# Pelican Workbench V3.6.0

**鹈鹕工作台 · TF7Z-XY**

Pelican Workbench 是 Windows 本地工作伴侣：真实记录工作行为统计，在不保存实际输入内容的前提下，把工作数据转化为 Timeline、Stats、Replay、XP、Level、Achievement 和可成长的 Pelican 工作世界。

## 产品闭环

```
键盘 / 鼠标 / 时间 / 显示器
        ↓
      Tracker
        ↓
      SQLite
        ↓
Today / Timeline / Stats / Replay
        ↓
XP / Level / Achievement
        ↓
Unlock / Collection / Equipment
        ↓
Scene / Pelican / Outfit / Decoration / Effect
        ↓
越来越丰富的工作室
```

## 当前核心功能

- **工作采集**：键盘数量、字符数、鼠标移动/点击/滚轮、活跃/空闲、Focus Session
- **多显示器**：数量、布局、负坐标、跨屏移动、拓扑变化
- **数据分析**：Today、24 小时时间轴、今日/周/月 Stats、行为 Replay
- **Todo**：创建、完成、删除、持久化
- **成长**：XP、Level、Achievement、Unlock、Collection
- **工作世界**：Scene、Pelican、Outfit、Accessory、Decoration、Effect
- **设置**：Idle threshold、开机自启动、天气开关、显示器信息、隐私、删除今日数据
- **Windows**：Tray、本地 WebView、本地 SQLite、安装包
- **导出**：CSV / XLSX
- **安全**：资源完整性校验、Ed25519 签名链、可选 Authenticode

## 重要产品边界

程序可以保存统计数据，但**不保存**：
- 实际键盘输入文本
- 窗口标题 / 文件名
- URL
- 网页正文
- 聊天正文
- 文档正文
- 屏幕录像

Replay 也是行为分类回放，不是屏幕录像。

## 文档入口

### 产品与开发
- [完整产品需求基线](docs/PRODUCT_REQUIREMENTS.md)
- [产品架构](docs/WORKBENCH_PRODUCT_ARCHITECTURE.md)
- [P0 功能验收矩阵](docs/P0_ACCEPTANCE_MATRIX.md)
- [P1 成长系统验收矩阵](docs/P1_ACCEPTANCE_MATRIX.md)
- [P2 世界/美术/发布验收矩阵](docs/P2_ACCEPTANCE_MATRIX.md)

### 美术生产
- [ART_HANDOFF.md](ART_HANDOFF.md)
- [ART_SYNC_GUIDE.md](ART_SYNC_GUIDE.md)
- [ART_OFFLINE_HANDOFF_GUIDE.md](ART_OFFLINE_HANDOFF_GUIDE.md)
- [美术资产目录](art-production-spec/ART_ASSET_CATALOG.md)
- [美术 Manifest](art-production-spec/ART_ASSET_MANIFEST.json)
- [角色规范](art-production-spec/CHARACTER_BIBLE.md)
- [美术方向](art-production-spec/ART_DIRECTION.md)
- [生产规则](art-production-spec/PRODUCTION_RULES.md)
- [人工审核](art-production-spec/HUMAN_REVIEW_GUIDE.md)

## 开发原则

1. GitHub `main` 是当前项目事实来源。
2. P0 功能可靠性优先于视觉装饰。
3. 产品需求、代码、API、UI、数据库和美术资产必须保持同一功能定义。
4. 新功能必须进入产品需求和对应 Acceptance Matrix。
5. 美术资产必须由 Manifest 管理，并经过技术 QA 与人工审核。
6. “代码存在”不等于“功能验收完成”；必须有运行时证据。

## 一键发布

1. Windows 安装 Python 3.11/3.12 x64。
2. 安装 Inno Setup 6。
3. 双击 `build_release.bat`。
4. 安装包输出到 `release\\PelicanWorkbench_Setup_3.6.0.exe`。

构建脚本会创建项目自己的 `.venv`，安装固定版本的 pywebview 与 PyInstaller，执行源码自检与资源完整性检查，然后生成 one-file EXE 并调用 Inno Setup。

## 隐私与安全

工作数据库位于 `%LOCALAPPDATA%\\PelicanWorkbench`。

正式构建时，Ed25519 私钥位于：
`%USERPROFILE%\\.pelican_workbench\\signing\\private.key`

私钥不会进入源码包或安装包。正式公开发布建议使用 Authenticode 代码签名。

> 完整产品行为、数据链路、功能边界与完成定义，以 `docs/PRODUCT_REQUIREMENTS.md` 为准。
