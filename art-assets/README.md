# art-assets

Pelican Workbench 原创美术资产同步目录。

## 目录约定

每个资产使用 Manifest 的 `asset_id` 建立目录：

```text
art-assets/<ASSET_ID>/
├─ candidates/   # AI/人工生成的候选版本
├─ approved/     # 人工明确批准的正式版本
└─ review.json   # 人工审核记录（需要时）
```

B01 风格锚点可使用：

```text
art-assets/B01/master/
```

候选必须使用版本号命名，例如 `B04_v01.png`、`B04_v02.png`。

跨账号、跨平台、跨电脑同步规则见仓库根目录 `ART_SYNC_GUIDE.md`。
