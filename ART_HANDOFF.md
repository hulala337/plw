# ART_HANDOFF.md

> **唯一入口：跨账号 / 跨平台 / 跨电脑继续 Pelican Workbench 美术生产。**

## 30 秒接力流程

1. 打开仓库：https://github.com/hulala337/plw
2. 切换到 main 并拉取最新代码：
   ```powershell
   git checkout main
   git pull origin main
   ```
3. 阅读本文件。
4. 读取机器状态：art-production-spec/ART_PRODUCTION_STATE.json
5. 读取资产清单：art-production-spec/ART_ASSET_MANIFEST.json
6. 运行：
   ```powershell
   python art-pipeline\handoff_check.py
   ```
7. **只按检查结果中的 current_asset / current_key / next_action 继续。**
8. 当前状态若为 READY + GENERATE，直接生成当前资产；不要重新规划、不要从 B01 重来。
9. 生成结果按 Manifest 的 asset_id 命名并保存到项目约定的资产位置/资料库。
10. 生成结果默认是候选，不得自动 APPROVED 或 FROZEN；人工审核后再更新状态并提交 GitHub。

## 当前断点

- **Style Anchor：B01 / pelican_master**
- **Current：B04 / pelican_thinking**
- **Status：READY**
- **Next Action：GENERATE**

## 如果换了 ChatGPT 账号 / 平台

聊天记录不重要，**GitHub 状态才是接力依据**。新对话直接发送：

> 请接手 Pelican Workbench 美术资产生产。先读取仓库根目录 ART_HANDOFF.md，再读取 art-production-spec/ART_PRODUCTION_STATE.json、ART_ASSET_MANIFEST.json、CHARACTER_BIBLE.md、ART_DIRECTION.md、PRODUCTION_RULES.md，运行 python art-pipeline\\handoff_check.py。严格从检查结果的 current_asset 继续，不重复已经存在的候选，不跳过人工审核；如果 current_status=READY 且 next_action=GENERATE，就直接执行当前资产的生成任务。

## 权威层级

```text
ART_HANDOFF.md
  ↓ 快速入口 / 操作步骤
ART_PRODUCTION_STATE.json
  ↓ 当前进度的唯一机器真相源
ART_ASSET_MANIFEST.json
  ↓ 资产身份、规格、顺序与规则
ART_PRODUCTION_HANDOFF.md
  ↓ 完整接力协议与长期规则
CHARACTER_BIBLE.md + ART_DIRECTION.md + PRODUCTION_RULES.md
  ↓ 美术执行规范
```

**禁止把聊天记录、账号、平台、电脑作为生产状态来源。**

ART_PRODUCTION_HANDOFF.md 只解释规则，不维护另一份独立的当前进度。
ART_PRODUCTION_STATE.json 的 current_asset/current_key/current_status/next_action 才是当前进度真相源。

最后更新：2026-09-23
