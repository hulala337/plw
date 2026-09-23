# ART_HANDOFF.md

> **唯一入口：跨账号 / 跨平台 / 跨电脑继续 Pelican Workbench 美术资产生产。**
>
> 本文件同时承担“快速接力入口 + 完整接力协议”。不再维护第二份 Markdown 接力文档。

## 1. 30 秒接力流程

1. 拉取最新 `main`。
2. 阅读本文件。
3. 读取 `art-production-spec/ART_PRODUCTION_STATE.json`。
4. 读取 `art-production-spec/ART_ASSET_MANIFEST.json`。
5. 读取 `CHARACTER_BIBLE.md`、`ART_DIRECTION.md`、`PRODUCTION_RULES.md`。
6. 运行 `python art-pipeline\handoff_check.py`。
7. **只按检查结果中的 `current_asset / current_key / current_status / next_action` 继续。**
8. 若 `READY + GENERATE`，直接执行当前资产生成任务；不要重新规划、不要从 B01 重来。
9. 按 Manifest 的 `asset_id` 命名并保存候选。
10. 候选默认不得自动 `APPROVED/FROZEN`；必须人工审核。
11. 持久化审核和状态、commit + push 后，才进入下一个资产。

## 2. 接力目标与核心原则

更换 ChatGPT 账号、AI 平台、中转平台、电脑或 VS Code/Codex 工作环境后，任务必须能够仅依靠 GitHub 恢复，而不依赖原聊天记录。

- 账号不是任务身份。
- 平台不是任务身份。
- 设备不是任务身份。
- `asset_id` 是资产身份。
- GitHub 持久化状态是任务事实来源。
- **`ART_PRODUCTION_STATE.json` 是当前进度的唯一机器真相源。**
- `ART_ASSET_MANIFEST.json` 定义资产身份、规格、顺序与规则。
- 不保存 API Key、密码、Token、Cookie 或登录凭据。
- 不因聊天上下文丢失而重复生成已有候选。
- 检查失败时先修复一致性，不得继续生成。
- `HUMAN REVIEW REQUIRED` 不得自动批准。
- `APPROVED/FROZEN` 不得无记录覆盖；返工必须建立 `REWORK` / 版本记录。

## 3. 新环境标准操作

```text
拉取 main
  ↓
读取 ART_HANDOFF.md
  ↓
读取 STATE
  ↓
读取 Manifest
  ↓
读取 CHARACTER_BIBLE / ART_DIRECTION / PRODUCTION_RULES
  ↓
运行 handoff_check.py
  ↓
读取 current_asset / current_key / current_status / next_action
  ↓
执行 next_action
```

如果检查失败，先修复状态/文件一致性；不得绕过检查继续生产。

## 4. 强制接力规则

### 4.1 状态恢复规则

1. 新环境必须先拉取最新 `main`。
2. 必须先读取 `ART_HANDOFF.md`，再读取 STATE、Manifest 和美术规范。
3. 必须运行 `python art-pipeline\handoff_check.py`。
4. **必须从 checker/STATE 给出的 `current_asset` 继续。**
5. 不允许因换账号、平台、电脑而从 B01 重新开始。
6. 不允许依据聊天记忆自行猜测当前进度。
7. 不允许重复生成已经存在且仍有效的候选。
8. STATE 与 Manifest、文件结构或 checker 冲突时，先修复冲突。

### 4.2 生成与候选规则

1. `READY + GENERATE` 才进入当前资产生成动作。
2. 新生成结果默认 `GENERATED / CANDIDATE`。
3. 生成失败不得标记为 `APPROVED`。
4. 不得用几何 SVG、简单形状拼接等方式伪造最终角色/场景美术。
5. 最终角色/场景必须是高质量原创插画。
6. 必须使用 Manifest 的 `asset_id` 命名。
7. 不得随意改变 B01 主角色身份、比例、视觉语言、完成度或主要色彩体系。
8. 不得加入无意义文字、AI 乱码、随机角色或与 brief 无关的元素。

### 4.3 人工审核规则

1. 自动 QA 是门禁，不替代人工审美判断。
2. `HUMAN REVIEW REQUIRED` 必须由人完成审核。
3. AI 的 `PASS_TO_HUMAN` 只是进入人工审稿入口，**不是批准**。
4. P0/P1 必须人工审核后才能进入 `APPROVED`。
5. 人工审核结论必须持久化到仓库后，再切换任务。
6. `APPROVED/FROZEN` 不得无记录覆盖。

### 4.4 跨账号 / 跨平台规则

1. ChatGPT 账号只是执行环境，不是任务身份。
2. AI 平台或中转平台只是执行环境，不是任务状态来源。
3. 家用电脑、单位电脑等只是执行环境，不是任务状态来源。
4. GitHub `main` 是跨环境持久化接力基准。
5. 平台切换必须先 `git pull`，再检查 STATE。
6. 不得把 API Key、密码、Token、Cookie 或登录凭据写入仓库。
7. 当前平台不能执行某一步时，应保留当前状态并把明确的下一动作写回 STATE，不得擅自改变生产顺序。

### 4.5 资产完成后的强制动作

每个资产完成一次生产循环后，应持久化：

1. 原始生成图/候选图
2. 按 Manifest `asset_id` 命名的项目资产
3. 必要的候选/版本信息
4. 技术 QA / 视觉 QA / 人工审核结果
5. `ART_PRODUCTION_STATE.json` 更新
6. Manifest 对应状态更新（若流程要求）
7. Git commit + push

**只有完成以上持久化，才允许进入下一个资产。**

## 5. 美术生成硬规则

B01 `pelican_master` 是唯一主风格锚点。后续角色必须保持同一角色身份、比例、视觉语言、完成度和主要色彩体系。

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

## 6. 状态机

```text
PLANNED → READY → GENERATING → GENERATED/CANDIDATE
→ QA → REVIEW → HUMAN REVIEW REQUIRED
→ APPROVED → INTEGRATING → FROZEN
                         ↘ REWORK
```

当前状态以 STATE 为准。

## 7. 当前断点

- **Style Anchor：B01 / pelican_master**
- **Current：B04 / pelican_thinking**
- **Status：READY**
- **Next Action：GENERATE**

后续生产顺序由 STATE/Manifest 决定。当前不要从 B01 重新开始，也不要跳过 B02/B03 的人工审核。

## 8. 新账号 / 新平台可直接粘贴的接力指令

> 请接手 Pelican Workbench 美术资产生产。先读取仓库根目录 ART_HANDOFF.md，再读取 art-production-spec/ART_PRODUCTION_STATE.json、ART_ASSET_MANIFEST.json、CHARACTER_BIBLE.md、ART_DIRECTION.md、PRODUCTION_RULES.md，运行 python art-pipeline\\handoff_check.py。严格从检查结果的 current_asset 继续，不重复已经存在的候选，不跳过人工审核；如果 current_status=READY 且 next_action=GENERATE，就直接执行当前资产的生成任务。

## 9. 检查命令

```powershell
python art-pipeline\handoff_check.py
python art-pipeline\handoff_check.py --json
```

**最后更新：2026-09-23**
