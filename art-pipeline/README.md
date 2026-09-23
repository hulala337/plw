# Pelican Workbench 全量美术资产生产管线

这是 `art-production-spec/` 的执行层，不负责改变美术规范，只负责把 manifest 变成可执行的生产流水线。

## 目标

```
ART_ASSET_MANIFEST.json
        ↓
asset_scanner
        ↓
prompt_builder
        ↓
generator (OpenAI Images API)
        ↓
visual_qa
        ↓
consistency_check
        ↓
vision_art_director（V3 AI视觉审稿）
        ↓
production_report
        ↓
review_server（人工审核）
        ↓
integrate
        ↓
web/assets/generated-art
```

原则：

- 不把 API Key 写入仓库。
- 不把生成结果直接覆盖生产资源。
- P0/P1 必须经过人工审核。
- 生成失败不会自动标记为 APPROVED。
- 自动 QA 是门禁，不替代人工审美判断。
- 最终角色/场景必须是原创插画，不以几何 SVG 作为最终美术。

## Windows 快速开始

在仓库根目录：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r art-pipeline\requirements.txt

$env:OPENAI_API_KEY="你的API Key"

python art-pipeline\asset_scanner.py
python art-pipeline\prompt_builder.py --ids B01,B02,B03,B04,B07,B11,C01
python art-pipeline\generator.py --ids B01,B02,B03,B04,B07,B11,C01
python art-pipeline\visual_qa.py
python art-pipeline\consistency_check.py
python art-pipeline\review_server.py
```

然后打开：

`http://127.0.0.1:8765`

人工审核完成后：

```powershell
python art-pipeline\integrate.py
```

## 目录

```
art-pipeline/
  asset_scanner.py
  prompt_builder.py
  generator.py
  visual_qa.py
  consistency_check.py
  review_server.py
  integrate.py
  requirements.txt
```

运行过程中生成的工作目录默认位于：

```
art-work/
  prompts/
  generated/
  candidates/
  approved/
  rejected/
  qa/
  reviews/
  reports/
```

这些中间产物默认不提交 Git；真正批准后的生产资源才进入项目资源目录。

## API

本管线默认使用 OpenAI Images API，并允许通过环境变量覆盖：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（可选）
- `OPENAI_IMAGE_MODEL`，默认 `gpt-image-2`

因此 ChatGPT 会员和 API 用量是两套计费/额度体系；没有 ChatGPT Plus 也可以单独使用 API，只要 API 账户有可用余额/额度。

## 推荐生产顺序

第一批只做风格锚点，不要一次生成全部资产：

1. B01 pelican_master
2. B02 neutral
3. B03 working
4. B04 typing
5. B07 focused
6. B11 drinking_coffee
7. C01 office_master_day
8. C02 office_master_evening
9. C03 office_master_night
10. E01 dashboard_hero

这 10 项通过人工审核后，再批量放大到 P0/P1。


## V3：AI Vision Art Director

V3 在传统技术 QA 和颜色统计检查之上增加视觉语义审稿层：

candidate image
      ↓
technical QA
      ↓
heuristic consistency
      ↓
AI Vision Art Director
  ├─ brief compliance
  ├─ character identity
  ├─ style consistency
  ├─ composition
  ├─ artifact detection
  └─ originality guard
      ↓
PASS_TO_HUMAN / REWORK / HOLD
      ↓
human review
      ↓
integrate

### 运行

```powershell
python art-pipeline\vision_art_director.py --ids B01,B02,B03,C01
python art-pipeline\production_report.py --ids B01,B02,B03,C01
```

或直接运行 V3 批处理：

```powershell
python art-pipeline\batch_v3.py --ids B01,B02,B03,B04,B07,B11,C01,C02,C03,E01
```

默认视觉审稿模型：

- `OPENAI_REVIEW_MODEL=gpt-5.6-luna`
- 可用 `--review-model gpt-5.6-sol` 切换更高能力模型
- `OPENAI_API_KEY` 必须通过环境变量提供
- `OPENAI_BASE_URL` 可选；使用官方 OpenAI API 时保持为空即可

V3 的 `PASS_TO_HUMAN` **不是批准**，只表示 AI 认为候选达到了人工审稿入口标准。P0/P1 仍必须人工决定。

AI 审稿结果写入：

```text
art-work/qa/vision-review/<ASSET_ID>.json
art-work/reports/v3-production-report.json
```

规则文件：

`art-production-spec/ART_REVIEW_SCHEMA.json`

### V3 硬门禁

以下情况直接进入 `REWORK`：

- Character Bible 中明确的角色身份硬失败
- 明显人类手臂/多余肢体/重复身体部件
- 明显错误的喙、眼睛、头身比例
- 明显塑料 3D 或摄影写实偏离
- 明显乱码或不需要的文字
- 明显破坏核心场景连续性的结构

AI 只负责“发现问题 + 分流”，不负责替代最终美术决策。


## 跨账号 / 跨平台 / 跨电脑接力

统一使用仓库根目录的 `ART_HANDOFF.md` 作为**唯一 Markdown 接力入口与完整接力协议**。

持久化状态分工：

- `ART_HANDOFF.md`：快速入口、强制接力规则、执行协议
- `art-production-spec/ART_PRODUCTION_STATE.json`：当前进度的唯一机器真相源
- `art-production-spec/ART_ASSET_MANIFEST.json`：资产身份、规格、顺序与规则
- `art-production-spec/CHARACTER_BIBLE.md`：角色规范
- `art-production-spec/ART_DIRECTION.md`：美术方向
- `art-production-spec/PRODUCTION_RULES.md`：生产规则

`ART_PRODUCTION_HANDOFF.md` 已废弃并删除，不再存在第二份 Markdown 接力状态/协议文件。

新环境先运行：

```powershell
python art-pipeline\\handoff_check.py
```

通过后严格从 STATE 的 `current_asset` 继续。不要依据聊天记录重新猜测进度，不要重复生成已有候选，不得绕过人工审核。

当前断点：**B04 / pelican_thinking / READY / GENERATE**。
