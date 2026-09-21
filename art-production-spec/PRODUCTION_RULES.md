# 美术资产生产规则

## 状态

PLANNED → READY → GENERATING → GENERATED → QA → REVIEW → APPROVED → INTEGRATING → FROZEN

失败：
- QA FAIL → REWORK
- HUMAN REJECT → REWORK
- INTEGRATION FAIL → INTEGRATING

## 优先级

P0：首屏、核心 Pelican、核心办公室场景、品牌资产
P1：Dashboard/Timeline/Stats/Settings 的主要插画
P2：状态插画、空状态、成就、提示
P3：小装饰、简单 icon、非关键背景

## 每项资产必须记录

- asset_id
- name
- category
- priority
- purpose
- visual_brief
- subject
- composition
- pose/state
- environment
- palette
- lighting
- background
- aspect_ratio
- target_size
- alpha
- output_format
- reference_assets
- negative_constraints
- qa_requirements
- integration_target
- status
- version

## QA

### 技术
- 文件存在
- 格式正确
- 尺寸正确
- alpha 正确
- 无损坏
- 文件大小合理
- 命名符合 manifest

### 美术
- 主体完整
- 构图符合 brief
- 光影一致
- 色彩一致
- 角色比例一致
- 无明显生成缺陷
- 无乱码文字
- 无意外人物/物体

### 一致性
核心角色必须与 Character Bible 对照。
同一批次必须进行横向风格检查。

## 自动停止

满足任一条件：
- 连续 3 个资产 QA 失败
- 同一角色出现明显脸型/喙/眼睛漂移
- 批次风格评分明显下降
- 关键参考图无法可靠使用

则暂停该批次，重新校准 Art Direction。

## 人工审核

人工只做：
- PASS
- REJECT
- REGENERATE
- MINOR_EDIT

批准后进入 approved，并记录版本。

## 接入

批准资产：
1. 优化
2. 复制到生产资源目录
3. 更新代码引用
4. 检查旧资源引用
5. 运行前端/构建/视觉回归
6. 成功后 FROZEN
