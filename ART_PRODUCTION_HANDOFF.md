# Pelican Workbench 美术资产生产接力协议

## 1. 文件职责

本文件是**长期有效的生产协议**，不是独立的进度数据库。

- 当前进度唯一机器真相源：art-production-spec/ART_PRODUCTION_STATE.json
- 资产身份与规格：art-production-spec/ART_ASSET_MANIFEST.json
- 快速接力入口：ART_HANDOFF.md
- 角色规范：art-production-spec/CHARACTER_BIBLE.md
- 美术方向：art-production-spec/ART_DIRECTION.md
- 生产规则：art-production-spec/PRODUCTION_RULES.md

因此，本文件中出现的“当前 B04”等文字只作为最近断点记录；如果与 STATE 冲突，以 STATE 为准。

## 2. 接力目标

更换 ChatGPT 账号、AI 平台、中转平台、电脑或 VS Code/Codex 工作环境后，任务必须能够从 GitHub 恢复，而不依赖原聊天记录。

核心原则：
- 账号不是任务身份。
- 平台不是任务身份。
- 设备不是任务身份。
- asset_id 是资产身份。
- GitHub 持久化状态是任务事实来源。
- 不保存 API Key、密码、Token、Cookie 或登录凭据。
- 不因为聊天上下文丢失而重复生成已有候选。

## 3. 新环境标准操作

```text
拉取 main
  ↓
读取 ART_HANDOFF.md
  ↓
读取 ART_PRODUCTION_STATE.json
  ↓
读取 ART_ASSET_MANIFEST.json
  ↓
读取 CHARACTER_BIBLE / ART_DIRECTION / PRODUCTION_RULES
  ↓
运行 handoff_check.py
  ↓
读取 current_asset / current_key / current_status / next_action
  ↓
执行 next_action
```

如果检查失败，**先修复状态/文件一致性，不生成新资产**。

## 4. 美术生成规则

B01 pelican_master 是唯一主风格锚点。后续角色必须保持同一角色身份、比例、视觉语言、完成度和主要色彩体系。

硬约束：
- 白色/浅灰羽毛
- 黄色/橙黄色嘴和脚
- 大而有表现力的眼睛
- 深蓝色 hoodie
- 温暖、精致、现代数字插画
- 最终美术必须是高质量原创插画
- 不使用几何 SVG 伪造最终角色/场景美术
- 不生成随机角色
- 不随意改变鹈鹕比例
- 不加入无意义文字或 AI 乱码

## 5. 状态规则

```text
PLANNED → READY → GENERATING → GENERATED/CANDIDATE
→ QA → REVIEW → HUMAN REVIEW REQUIRED
→ APPROVED → INTEGRATING → FROZEN
                         ↘ REWORK
```

- 新生成资产默认 GENERATED / CANDIDATE。
- HUMAN REVIEW REQUIRED 不得自动批准。
- APPROVED/FROZEN 不得无记录覆盖；返工时建立明确的 REWORK/版本记录。
- 人工审核结论必须持久化到仓库后再切换任务。

## 6. 生成后的接力动作

每个资产完成一次生成后，应保存：
1. 原始生成图/候选图
2. 按 Manifest 的 asset_id 命名的项目资产
3. 必要的候选/版本信息
4. QA/人工审核结果
5. 更新 ART_PRODUCTION_STATE.json
6. 更新 Manifest 中对应状态（若项目流程要求）
7. Git commit + push

然后才进入下一个资产。

## 7. 最近断点

最近一次持久化断点为 B04 / pelican_thinking / READY / GENERATE；新环境必须先运行 handoff checker，以 STATE 的实际内容为准。

**不要从 B01 重新开始。不要跳过 B02/B03 的人工审核。**

最后更新：2026-09-23
