# Pelican Workbench 美术资产生产接力记录

项目：
Pelican Workbench

主仓库：
https://github.com/hulala337/plw

美术规范：
- art-production-spec/
- art-pipeline/

> **任务事实来源**：GitHub 仓库中的 `ART_PRODUCTION_STATE.json`、`ART_ASSET_MANIFEST.json`、Character Bible、Style Direction、资产目录与审核记录。聊天记录、单个账号、单个平台均不是生产状态的唯一来源。

## 当前生产阶段

状态：**B04 等待生成**

当前资产：
- asset_id：B04
- key：pelican_thinking
- 状态：READY
- 下一步：生成

已完成 / 已进入生产：

### B01
- 类型：Style Anchor / Character Master
- 用途：全局风格锚点
- 状态：REFERENCE / STYLE ANCHOR

### B02
- key：pelican_working
- 已生成
- 有多个候选版本
- 状态：GENERATED / HUMAN REVIEW REQUIRED

### B03
- key：pelican_typing
- 已生成
- 状态：GENERATED / HUMAN REVIEW REQUIRED

## 下一资产

### B04
- key：pelican_thinking
- 状态：READY
- 下一步：生成

随后：

### B07
- key：pelican_drinking_coffee

### C01
- key：office_master

### C02
- key：office_day

### C03
- key：office_night

### E01
- key：dashboard_hero

## B01 主风格锚点

B01 是唯一主风格锚点。

后续角色资产必须保持：
- 同一角色身份
- 同一比例
- 同一视觉语言
- 同一绘制完成度
- 同一主要色彩体系
- 同一角色设定

角色硬约束：
- 白色/浅灰羽毛
- 黄色/橙黄色嘴和脚
- 大而有表现力的眼睛
- 深蓝色 hoodie
- 温暖、精致、现代数字插画

最终美术必须是高质量原创插画；**不使用几何 SVG 伪造最终美术**。

## 强制接力规则

新账号 / 新平台 / 新电脑：

1. 拉取 GitHub 最新仓库
2. 读取 `ART_PRODUCTION_HANDOFF.md`
3. 读取 `ART_HANDOFF.md`
4. 读取 `art-production-spec/ART_PRODUCTION_STATE.json`
5. 读取 `art-production-spec/ART_ASSET_MANIFEST.json`
6. 读取 `art-production-spec/CHARACTER_BIBLE.md`
7. 读取 `art-production-spec/ART_DIRECTION.md`
8. 读取 `art-production-spec/PRODUCTION_RULES.md`
9. 检查当前资产目录、候选目录、QA 与人工审核记录
10. 从 `current_asset` 继续
11. 不重新设计流程
12. 不跳过人工审核
13. 必须保持 B01 的角色身份一致
14. 白色/浅灰羽毛
15. 黄色/橙黄色嘴和脚
16. 大而有表现力的眼睛
17. 深蓝色 hoodie
18. 温暖、精致、现代数字插画
19. 不使用几何 SVG 伪造最终美术
20. 不生成随机角色
21. 不改变鹈鹕比例
22. 不加入无意义文字
23. 不加入 AI 乱码
24. 每个生成资产使用 manifest 中的 asset_id 命名
25. 生成后保存到资料库/项目约定的资产存储位置
26. 生成资产默认属于 `GENERATED / CANDIDATE`
27. 未经人工审核不得标记 `APPROVED` / `FROZEN`

## 跨账号 / 跨平台原则

- 账号不是任务身份。
- 平台不是任务身份。
- 设备不是任务身份。
- **asset_id 才是资产身份；GitHub 持久化状态才是任务事实来源。**
- 不保存任何 API Key、密码、Token、Cookie 或登录凭据。
- 可以记录平台/账号别名用于生产日志，但不能记录认证信息。
- 更换账号后不得因为聊天上下文不存在而重复生成已经存在的候选。
- 先检查状态，再执行动作。
- 如果状态为 `HUMAN REVIEW REQUIRED`，必须进入人工审核，不得自动生成新版本覆盖它。
- 如果状态为 `APPROVED` 或 `FROZEN`，默认禁止重新生成，除非明确创建 REWORK/新版本记录。

## 接力恢复命令

在仓库根目录执行：

```powershell
python art-pipeline\handoff_check.py
```

通过后再继续当前资产。

也可以：

```powershell
python art-pipeline\handoff_check.py --json
```

用于机器读取接力状态。

## 状态机

```
PLANNED
  ↓
READY
  ↓
GENERATING
  ↓
GENERATED / CANDIDATE
  ↓
QA
  ↓
REVIEW
  ↓
HUMAN REVIEW REQUIRED
  ├─ PASS → APPROVED
  ├─ REGENERATE → REWORK
  └─ MINOR_EDIT → REVIEW
  ↓
INTEGRATING
  ↓
FROZEN
```

任何 AI 自动审查都不能替代人工最终决定。

## 当前接力结论

**RESUME FROM B04**

不要从 B01 重新开始，不要跳过 B02/B03 的人工审核，不要把 B04 标记为 APPROVED/FROZEN。

最后更新：2026-09-23
