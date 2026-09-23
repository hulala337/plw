# ART_SYNC_GUIDE.md

> **Pelican Workbench 美术资产跨账号 / 跨平台 / 跨电脑同步规范**
>
> 目标：任何账号、AI 平台、中转平台或电脑生成的候选，都能通过同一个 GitHub 仓库安全接力，不依赖聊天记录。

## 1. 唯一同步基准

- 仓库：`https://github.com/hulala337/plw`
- 主分支：`main`
- 资产身份：Manifest 中的 `asset_id`
- 当前进度唯一机器真相源：`art-production-spec/ART_PRODUCTION_STATE.json`
- 接力协议：`ART_HANDOFF.md`
- 本文件只负责说明“资产文件如何同步”。

账号、平台、电脑都只是执行环境，不是任务状态来源。

## 2. 标准资产目录

正式美术文件统一放在仓库根目录：

```text
art-assets/
├─ B01/
│  └─ master/
├─ B02/
│  └─ candidates/
├─ B03/
│  └─ candidates/
├─ B04/
│  ├─ candidates/
│  │  ├─ B04_v01.png
│  │  ├─ B04_v02.png
│  │  └─ B04_v03.png
│  ├─ approved/
│  │  └─ B04.png
│  └─ review.json
└─ ...
```

目录规则：

- `candidates/`：所有待人工选择的候选版本。
- `approved/`：人工明确批准后的正式版本。
- `master/`：B01 等风格/身份基准资源。
- `review.json`：人工审核和版本选择的持久化记录。
- 不允许用同名文件覆盖另一平台已经产生的候选；新版本必须递增 `v01/v02/v03...`。

## 3. 每次切换账号 / 平台 / 电脑

必须先同步：

```powershell
git checkout main
git pull origin main
```

然后：

```powershell
python art-pipeline\handoff_check.py
```

再读取 STATE，确认：

- `current_asset`
- `current_key`
- `current_status`
- `next_action`

**没有完成 pull + checker，不得开始生成。**

## 4. 生成后的标准同步流程

### A. AI 平台能够直接写入本地仓库

把图片保存到当前资产的：

```text
art-assets/<ASSET_ID>/candidates/
```

例如：

```text
art-assets/B04/candidates/B04_v01.png
```

然后执行：

```powershell
git status
git add art-assets/B04
git add art-production-spec/ART_PRODUCTION_STATE.json
git add art-production-spec/ART_ASSET_MANIFEST.json
git commit -m "Add B04 candidate assets"
git push origin main
```

### B. ChatGPT / 其他平台生成后需要下载

1. 下载图片到本机。
2. 放入 `art-assets/<ASSET_ID>/candidates/`。
3. 按 `<ASSET_ID>_vNN.ext` 命名。
4. 检查是否与远端最新 main 同步。
5. Git commit + push。

### C. 无法使用 Git 的电脑

可以先通过 GitHub 网页把候选上传到对应的 `art-assets/<ASSET_ID>/candidates/` 目录。

之后其他电脑必须：

```powershell
git checkout main
git pull origin main
```

网页上传仍然必须遵守相同的命名和状态规则。

## 5. 防止多账号 / 多平台互相覆盖

**禁止：**

- 两个平台同时生成并都保存为 `B04.png`。
- 用新候选覆盖旧候选。
- 未 pull 就直接 push。
- 用聊天记录判断哪个候选已经存在。
- 把 AI 的 `PASS_TO_HUMAN` 写成 `APPROVED`。
- 把候选直接放入生产目录冒充正式资源。

**必须：**

- 每个候选有唯一版本名。
- 先 pull，再生成/上传。
- 生成后立即持久化到 GitHub。
- 人工选中后再复制/移动到 `approved/`。
- 审核结果与 STATE 一起提交。
- 进入下一个资产前必须完成 push。

## 6. 人工批准的标准记录

`review.json` 至少记录：

```json
{
  "asset_id": "B04",
  "selected_candidate": "B04_v02.png",
  "decision": "APPROVED",
  "reviewer": "human",
  "comment": "人工确认角色身份、动作、比例和整体美术风格符合要求。",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SS"
}
```

真实审核时使用实际信息，不要伪造审核人或时间。

## 7. 推荐提交边界

一次生产循环至少应一起提交：

- 当前资产候选/正式资源
- QA 结果（如果产生）
- `review.json`（如果已人工审核）
- `ART_PRODUCTION_STATE.json`
- Manifest 状态（如果流程要求）

提交后：

```text
本机/平台
   ↓
git commit
   ↓
git push
   ↓
GitHub main
   ↓
下一个账号/平台 git pull
   ↓
继续 current_asset
```

## 8. 大型二进制文件

美术候选可能产生大量 PNG/PSD 等二进制文件。若文件体积逐渐增大，应采用 Git LFS 管理大型二进制资源，而不是把超大文件直接作为普通 Git blob 长期堆积。

无论是否使用 Git LFS，**资产状态、命名、审核记录和 STATE 都必须继续遵守本规范。**

## 9. 与接力协议的关系

- `ART_HANDOFF.md`：决定“现在生产什么、何时切换”。
- `ART_SYNC_GUIDE.md`：决定“生成的文件放哪里、如何跨环境同步”。
- `ART_PRODUCTION_STATE.json`：决定“当前到底走到哪一步”。
- `ART_ASSET_MANIFEST.json`：决定“资产 ID 和规格是什么”。
- `HUMAN_REVIEW_GUIDE.md`：决定“什么情况下才能 APPROVED”。

如果这些文件发生冲突，先停止生产并修复一致性。

**最后更新：2026-09-23**
