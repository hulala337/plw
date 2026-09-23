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

## 跨账号 / 跨平台 / 跨电脑资产同步

资产文件现在有统一的 GitHub 同步机制：

- 详细规范：根目录 `ART_SYNC_GUIDE.md`
- 资产根目录：`art-assets/`
- 候选：`art-assets/<ASSET_ID>/candidates/`
- 人工批准版本：`art-assets/<ASSET_ID>/approved/`
- 风格锚点：`art-assets/B01/master/`
- 人工审核记录：`art-assets/<ASSET_ID>/review.json`
- 候选命名：`<ASSET_ID>_vNN.<ext>`
- GitHub `main` 是跨环境同步基准
- 每次切换环境先 `git pull origin main`
- 每个候选生成/上传后必须 commit + push
- 不允许同名覆盖其他平台已有候选

### 标准接力

```text
账号/平台 A
   ↓ 生成
art-assets/B04/candidates/B04_v01.png
   ↓ commit + push
GitHub main
   ↓ git pull
账号/平台 B
   ↓ 读取 STATE + 候选
继续审核 / 生成 B04_v02
   ↓ commit + push
GitHub main
```

**只有候选、QA、审核记录和 STATE 已持久化并 push 后，才允许进入下一个资产。**

## 外部平台资产导入（asset_intake.py）

如果图片是在 ChatGPT、其他 AI 平台或其他电脑生成后下载到本机，不要手工猜目录和版本号。使用：

```powershell
python art-pipeline\\asset_intake.py "C:\\Users\\你的用户名\\Downloads\\生成图片.png"
```

工具默认读取 `ART_PRODUCTION_STATE.json` 的 `current_asset`，校验该 ID 是否存在于 Manifest，并自动选择候选目录中的下一个版本号。例如当前是 B04 时会得到：

```text
art-assets/B04/candidates/B04_v01.png
art-assets/B04/candidates/B04_v02.png
...
```

也可以明确指定资产并先预览：

```powershell
python art-pipeline\\asset_intake.py "D:\\incoming\\pelican.png" --asset-id B04 --dry-run
```

规则：自动复制而不删除源文件；默认禁止覆盖；候选始终保持 `GENERATED / HUMAN REVIEW REQUIRED`，不会自动 APPROVED、FROZEN 或推进 STATE。支持 PNG/JPG/JPEG/WebP/GIF/PSD/SVG。导入后仍需按 `ART_SYNC_GUIDE.md` 完成 QA、人工审核（如适用）以及 commit + push。

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

V3 的 `PASS_TO_HUMAN` **不是批准**，只表示 AI 认为候选达到了人工审稿入口标准。P0/P1 仍必须人工决定。

AI 审稿结果写入：

```text
art-work/qa/vision-review/<ASSET_ID>.json
art-work/reports/v3-production-report.json
```

AI 只负责“发现问题 + 分流”，不负责替代最终美术决策。

## 接力文档关系

- `ART_HANDOFF.md`：唯一接力入口、当前任务和强制生产规则
- `ART_SYNC_GUIDE.md`：资产文件如何跨账号/平台/电脑同步
- `art-production-spec/ART_PRODUCTION_STATE.json`：当前进度唯一机器真相源
- `art-production-spec/ART_ASSET_MANIFEST.json`：资产身份、规格、顺序与规则
- `art-production-spec/HUMAN_REVIEW_GUIDE.md`：人工审核与 APPROVED 规则

`ART_PRODUCTION_HANDOFF.md` 已废弃并删除。

新环境先运行：

```powershell
python art-pipeline\handoff_check.py
```

当前断点：**B04 / pelican_thinking / READY / GENERATE**。
