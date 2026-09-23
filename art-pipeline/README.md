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
