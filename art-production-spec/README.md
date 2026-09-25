# Pelican Workbench 全量美术资产生产规范

本目录是 Pelican Workbench 的美术资产生产主规格（Art Production Specification）。

目标不是用 SVG/几何图形伪造最终美术，而是为高质量原创插画、角色、场景与辅助视觉建立统一的生产、QA、审核和接入标准。

## 来源

- 当前 GitHub 仓库：hulala337/plw
- 当前 UI 与视觉实现：web/、web/assets/、web/assets/illustrations/
- 当前设计参考：V3_design_preview.png
- 已存在的旧版 SVG 资产视为「现状/占位/结构参考」，不自动视为最终美术。

## 文件

- ART_ASSET_CATALOG.md：按系统模块整理的完整资产目录与逐项要求
- ART_ASSET_MANIFEST.json：机器可读的生产清单
- ART_DIRECTION.md：全局美术方向与角色一致性规则
- PRODUCTION_RULES.md：生成、QA、人工审核、版本冻结与接入规则

## 生产原则

1. P0/P1 核心角色与场景必须使用原创高质量插画资产。
2. 不允许使用简单几何 SVG 冒充最终角色/场景插画。
3. 资产必须先通过视觉 QA，再进入人工审核。
4. 角色类资产必须共享同一 Character Bible。
5. 同一批次出现连续风格漂移时必须停止批量生产并重新校准。
6. 资产文件名、ID、尺寸、透明度和引用路径必须稳定。
7. 已批准资产禁止无版本号覆盖；所有重绘都产生新版本。


## 与产品功能基线的关系

美术资产必须服务于完整产品，而不是独立的“插画包”。产品功能与视觉资产的对应关系以：

- `docs/PRODUCT_REQUIREMENTS.md`
- `docs/WORKBENCH_PRODUCT_ARCHITECTURE.md`
- `docs/P0_ACCEPTANCE_MATRIX.md`
- `docs/P1_ACCEPTANCE_MATRIX.md`
- `docs/P2_ACCEPTANCE_MATRIX.md`

为准。

### 资产库存与生产顺序

- `ART_ASSET_CATALOG.md`：完整资产库存，描述产品长期需要的角色、场景、状态、Dashboard、Timeline、Analytics、Achievement、Settings、Empty/Error、Weather、Decoration、Marketing、Tray 等资产。
- `ART_ASSET_MANIFEST.json`：机器可读资产身份与规格。
- `ART_PRODUCTION_STATE.json.production_sequence`：当前阶段实际生产顺序，不代表整个产品只需要这些资产。

因此，“当前只生产 B01/B02/B03/B04……”不代表其它资产被取消；只是当前阶段尚未进入生产。

### 资产必须覆盖的产品能力

长期资产系统应能够覆盖：

1. Pelican 核心状态与动作
2. Office 环境与时间状态
3. 单/双/多显示器
4. Todo/工作状态
5. Dashboard / Today
6. Timeline / Replay
7. Analytics / Stats
8. Growth / Achievement / Unlock
9. Scene / Collection / Equipment
10. Settings / Privacy / Empty / Error
11. Weather / Environment Effects
12. Tray / Marketing / Onboarding 等非核心视觉

如果代码新增用户可见状态而 Manifest/Asset Catalog 没有对应资产定义，应先补齐规格再进入批量生产。
