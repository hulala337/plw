# ART_HANDOFF.md

> 本文件是跨账号 / 跨平台 / 跨电脑接力入口。规范正文以 `ART_PRODUCTION_HANDOFF.md` 为准。

请先阅读：
1. `ART_PRODUCTION_HANDOFF.md`
2. `art-production-spec/ART_PRODUCTION_STATE.json`
3. `art-production-spec/ART_ASSET_MANIFEST.json`
4. `art-production-spec/CHARACTER_BIBLE.md`
5. `art-production-spec/ART_DIRECTION.md`

然后运行：

```powershell
python art-pipeline\handoff_check.py
```

**当前断点：B04 / pelican_thinking / READY / GENERATE。**

不得依据聊天记录猜测生产状态；以仓库持久化状态为准。
