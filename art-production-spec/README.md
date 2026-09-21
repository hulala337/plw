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
