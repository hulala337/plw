# ART_OFFLINE_HANDOFF_GUIDE.md

> Pelican Workbench 无 GitHub / 无本地仓库环境的美术资产接力流程

## 1. 核心原则

GitHub main 是唯一项目事实来源。无 GitHub 环境只是临时生产工作区，不是新的主仓库。

GitHub main → Handoff Package → 离线 AI 平台/电脑 → 生成与审核 → Return Package → GitHub 环境 → commit + push → GitHub main

聊天记录、平台会话、云盘或聊天软件都不是状态真相源。

## 2. 两种接力包

### 2.1 Handoff Package：GitHub → 离线环境

建议命名：
PelicanWorkBench_Art_Handoff_YYYYMMDD_<ASSET_ID>.zip

至少包含：

- ART_HANDOFF.md
- ART_SYNC_GUIDE.md
- art-production-spec/ART_PRODUCTION_STATE.json
- art-production-spec/ART_ASSET_MANIFEST.json
- art-production-spec/CHARACTER_BIBLE.md
- art-production-spec/ART_DIRECTION.md
- art-production-spec/PRODUCTION_RULES.md
- HUMAN_REVIEW_GUIDE.md
- REFERENCE_ASSET_MAP.json
- 当前资产 brief
- B01 风格锚点参考图
- 当前资产已有候选
- art-pipeline/asset_intake.py
- checksums.json

平台不需要访问 GitHub，只要能读取这些文件并生成图片即可。\n\n**自动更新机制：**每次 `main` 发生与美术生产相关的提交（包括新候选、QA、审核记录、STATE 或规范变化），GitHub Actions 会自动从最新仓库状态重新生成一份 Handoff Package，并上传为 `PelicanWorkBench-Art-Handoff-Latest` 工作流产物。你不需要手工维护 ZIP。

### 2.2 Return Package：离线环境 → GitHub 环境

建议命名：
PelicanWorkBench_Art_Return_YYYYMMDD_<ASSET_ID>.zip

标准结构：

PelicanWorkBench_Art_Return_YYYYMMDD_B04/
├─ RETURN.md
├─ RETURN.json
├─ art-assets/
│  └─ B04/
│     ├─ candidates/
│     │  ├─ B04_v03.png
│     │  └─ B04_v04.png
│     ├─ approved/
│     │  └─ B04.png
│     ├─ qa/
│     │  └─ B04_qa.json
│     └─ review.json
├─ art-production-spec/
│  └─ ART_PRODUCTION_STATE.json
├─ ART_HANDOFF.md
├─ ART_SYNC_GUIDE.md
└─ checksums.json

Return Package 只是运输容器，不代表 APPROVED。

## 3. 离线环境操作

### Step 1：解压 Handoff Package

解压到临时工作目录。不要依赖 GitHub，也不要要求 AI 平台访问原仓库。

### Step 2：读取状态

按顺序读取：

1. ART_HANDOFF.md
2. ART_PRODUCTION_STATE.json
3. ART_ASSET_MANIFEST.json
4. CHARACTER_BIBLE.md
5. ART_DIRECTION.md
6. PRODUCTION_RULES.md
7. HUMAN_REVIEW_GUIDE.md
8. REFERENCE_ASSET_MAP.json

只使用 STATE 的 current_asset / current_key / current_status / next_action 恢复当前任务。

不要从 B01 重启，不要依据聊天记录猜测进度。

### Step 3：检查已有候选

先查看 art-assets/<ASSET_ID>/candidates/。

新结果必须继续使用下一个未占用版本号。禁止覆盖旧候选。

### Step 4：生成

只有 READY + GENERATE 才直接生成当前资产。

B01 是唯一风格锚点。后续角色保持同一只鹈鹕身份、服装、主要色彩、比例、视觉语言和完成度；最终角色/场景必须是高质量原创插画，不用几何 SVG 伪造。

### Step 5：QA 与人工审核

新候选默认保持 GENERATED / HUMAN REVIEW REQUIRED。

AI 的 PASS_TO_HUMAN 不是 APPROVED。只有人工明确选择并留下审核记录后，才可以进入 approved/。

### Step 6：自动导出 Return Package

如果离线工作区保留了 Handoff Package 中的项目快照和 art-pipeline/asset_intake.py，完成生产后执行：

python art-pipeline\asset_intake.py --export-return-package "D:\Return\PelicanWorkBench_Art_Return_B04.zip"

指定资产：

python art-pipeline\asset_intake.py --export-return-package "D:\Return\PelicanWorkBench_Art_Return_B04.zip" --asset-id B04

工具自动收集当前资产的 candidates、approved、QA、review，以及 STATE、Manifest、ART_HANDOFF.md、ART_SYNC_GUIDE.md，并生成 checksums.json。

不会自动批准资产，也不会推进 STATE。

### Step 7：回传前自动校验

python art-pipeline\asset_intake.py --validate-return-package "D:\Return\PelicanWorkBench_Art_Return_B04.zip"

只有看到 RETURN PACKAGE: PASS 才回传。

## 4. 回到可访问 GitHub 的电脑

1. git checkout main
2. git pull origin main
3. 校验 Return Package。
4. 解压候选到 art-assets/<ASSET_ID>/candidates/。
5. 禁止覆盖远端已有版本。
6. 核对 review.json、QA 和 approved 文件。
7. 运行 handoff checker 与项目 QA。
8. 将审核结果和 STATE 变更一起提交。
9. git commit + git push origin main。
10. push 成功后才允许继续下一个资产。

## 5. 接收方必须检查

- Asset ID 与当前 STATE 一致
- 候选文件名符合 <ASSET_ID>_vNN.ext
- SHA-256 全部通过
- 没有覆盖远端已有候选
- 没有伪造 APPROVED
- review / QA 与实际文件一致
- 没有 API Key、Token、Cookie、密码等凭据

发现冲突时停止导入。

## 6. 多账号 / 多平台 / 多电脑

每次接力只传递“状态快照 + 当前任务所需资产 + 返回结果”，不传整段聊天历史。

账号 A / GitHub → Handoff Package → 平台 B → Return Package → 账号 C / GitHub → main → 账号 D / 平台 E

平台、账号和电脑都只是执行节点，不改变项目身份。

## 7. 离线平台可直接粘贴的启动指令

> 请接手 Pelican Workbench 美术资产生产。当前环境不能连接 GitHub，也可能没有本地 Git 仓库。请先完整读取 Handoff Package 中的 ART_HANDOFF.md、ART_PRODUCTION_STATE.json、ART_ASSET_MANIFEST.json、CHARACTER_BIBLE.md、ART_DIRECTION.md、PRODUCTION_RULES.md、HUMAN_REVIEW_GUIDE.md 和 REFERENCE_ASSET_MAP.json。严格使用 STATE 的 current_asset/current_key/current_status/next_action 恢复任务，不从 B01 重启，不重复已有候选，不覆盖任何版本。若 current_status=READY 且 next_action=GENERATE，就执行当前资产生成；新结果保存到 art-assets/<ASSET_ID>/candidates/，保持 GENERATED / HUMAN REVIEW REQUIRED。完成 QA 和人工审核后，按 ART_OFFLINE_HANDOFF_GUIDE.md 生成并校验 Return Package；不要因为 AI 判断通过就自动 APPROVED，也不要擅自进入下一个资产。

## 8. 最重要的一条

离线环境负责生产，GitHub 环境负责持久化和最终接力。

只要 Return Package 能够被完整校验，任何不能接入 GitHub 的 AI 平台都可以成为临时生产节点，而不会破坏 Pelican Workbench 的统一资产管理流程。

最后更新：2026-09-23
