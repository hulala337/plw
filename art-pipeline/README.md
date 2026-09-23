# Pelican Workbench 全量美术资产生产管线

这是 art-production-spec/ 的执行层，不负责改变美术规范，只负责把 manifest 变成可执行的生产流水线。

## 核心原则

- 不把 API Key 写入仓库。
- 不把生成结果直接覆盖生产资源。
- P0/P1 必须经过人工审核。
- 生成失败不会自动标记为 APPROVED。
- 自动 QA 是门禁，不替代人工审美判断。
- 最终角色/场景必须是原创插画，不以几何 SVG 作为最终美术。

## 跨账号 / 跨平台 / 跨电脑

- ART_HANDOFF.md：唯一接力入口
- ART_OFFLINE_HANDOFF_GUIDE.md：无 GitHub / 无本地仓库时的接力
- ART_SYNC_GUIDE.md：资产文件同步
- GitHub main：跨环境同步基准
- art-assets/：统一资产目录

### 外部资产导入

python art-pipeline\\asset_intake.py "C:\\Users\\你的用户名\\Downloads\\生成图片.png"

默认使用 STATE.current_asset，并自动选择下一个候选版本。

### Return Package 自动导出

python art-pipeline\\asset_intake.py --export-return-package "D:\\Return\\PelicanWorkBench_Art_Return_B04.zip"

### Return Package 校验

python art-pipeline\\asset_intake.py --validate-return-package "D:\\Return\\PelicanWorkBench_Art_Return_B04.zip"

校验通过必须显示：RETURN PACKAGE: PASS

Return Package 包含当前资产 candidates / approved / QA / review，以及 STATE、Manifest、ART_HANDOFF.md、ART_SYNC_GUIDE.md 和 SHA-256 checksums。它不会自动 APPROVED，也不会推进 STATE。

## 接力原则

每次切换环境先同步，再检查，再生产；生成后持久化候选、QA、审核和 STATE，并 commit + push。只有 push 成功后才允许进入下一个资产。

当前断点：B04 / pelican_thinking / READY / GENERATE。
