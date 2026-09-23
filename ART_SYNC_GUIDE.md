# ART_SYNC_GUIDE.md

> Pelican Workbench 美术资产跨账号 / 跨平台 / 跨电脑同步规范

目标：任何账号、AI 平台、中转平台或电脑生成的候选，都能通过同一个 GitHub 仓库安全接力，不依赖聊天记录。

## 1. 唯一同步基准

- 仓库：https://github.com/hulala337/plw
- 主分支：main
- 资产身份：Manifest 中的 asset_id
- 当前进度唯一机器真相源：art-production-spec/ART_PRODUCTION_STATE.json
- 接力协议：ART_HANDOFF.md
- 离线接力：ART_OFFLINE_HANDOFF_GUIDE.md
- 本文件只负责说明资产文件如何同步。

## 2. 标准资产目录

art-assets/<ASSET_ID>/
├─ candidates/
├─ approved/
├─ qa/
└─ review.json

B01 另有 art-assets/B01/master/ 作为风格/身份基准资源。

## 3. 正常 Git 环境

切换账号 / 平台 / 电脑必须先：

git checkout main
git pull origin main
python art-pipeline\handoff_check.py

没有完成 pull + checker，不得开始生成。

## 4. 外部平台生成后

不要手工猜目录和版本号：

python art-pipeline\asset_intake.py "D:\incoming\generated.png"

工具读取 STATE.current_asset、校验 Manifest，并自动保存到：
art-assets/<ASSET_ID>/candidates/<ASSET_ID>_vNN.<ext>

导入不会自动批准或推进 STATE。

## 5. 自动 Handoff Package\n\n仓库已配置 GitHub Actions：每次 `main` 的美术资产/状态/规范发生变化后，会自动从最新提交重新生成并校验 Handoff Package。工作流产物名称为 `PelicanWorkBench-Art-Handoff-Latest`，因此每次你上传新资产并 push 后，下一次工作流完成时拿到的就是最新快照。\n\n自动包包含当前资产状态、生产规范、接力协议、B01 风格锚点资源（仓库中存在时）以及当前资产候选，并带 SHA-256 校验。Handoff Package 是运输快照，不替代 GitHub `main`。\n\n如果某个 AI 平台无法访问 GitHub，只需要在一个能访问 GitHub 的环境下载最新工作流产物，再把 ZIP 交给该平台；之后平台无需 GitHub 权限即可继续生产。\n\n## 6. Return Package

如果生成环境没有 GitHub，可使用 ART_OFFLINE_HANDOFF_GUIDE.md。

如果该环境有项目快照和 asset_intake.py，可以自动导出：

python art-pipeline\asset_intake.py --export-return-package "D:\Return\PelicanWorkBench_Art_Return_B04.zip"

导出内容包括当前资产 candidates、approved、QA、review，以及 STATE、Manifest、接力/同步说明，并生成 SHA-256 checksums.json。

回传前：

python art-pipeline\asset_intake.py --validate-return-package "D:\Return\PelicanWorkBench_Art_Return_B04.zip"

必须显示 RETURN PACKAGE: PASS 才进入 GitHub 导入流程。

Return Package 不等于 APPROVED。

## 7. 防止多账号 / 多平台互相覆盖

禁止：
- 同一资产使用重复版本号。
- 用新候选覆盖旧候选。
- 未 pull 就直接 push。
- 用聊天记录判断哪个候选存在。
- 把 PASS_TO_HUMAN 写成 APPROVED。
- 把候选直接放入生产目录。

必须：
- 每个候选使用唯一版本名。
- 先同步，再生产。
- 生成后立即持久化。
- 审核后才进入 approved。
- 审核和 STATE 一起提交。
- 进入下一个资产前完成 push。

## 8. 大型二进制文件

美术候选体积增长后，应考虑 Git LFS。无论是否使用 Git LFS，资产状态、命名、审核记录和 STATE 都必须遵守本规范。

## 9. 文档关系

- ART_HANDOFF.md：现在生产什么、何时切换
- ART_OFFLINE_HANDOFF_GUIDE.md：无 GitHub / 无仓库环境如何接力
- ART_SYNC_GUIDE.md：资产文件如何同步
- ART_PRODUCTION_STATE.json：当前进度唯一机器真相源
- ART_ASSET_MANIFEST.json：资产身份、规格、顺序与规则
- HUMAN_REVIEW_GUIDE.md：人工审核规则

如果文件之间发生冲突，停止生产并修复一致性。

最后更新：2026-09-23
