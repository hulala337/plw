# 固定难度路由 v2

实现：`image_routing.py`；高级工具：`server.py` 的 `xingai_generate_project_image`。
模型 ID 只从 `image_models.toml` 读取。simple 使用用户指定的简单模型，medium/complex 共用用户指定的高档模型，不降级、不替换。

七项分数上限：composition 20、character 20、scene 15、multi_object 15、material_lighting 10、text_ui 10、style_consistency 10。
确定性中英关键词评分：基础构图 4；普通角色构图10/角色16/光影5；普通场景构图12/场景10/对象5/光影5；复杂完整场景构图20/场景15/对象15/光影8；多角色角色20；明确文字UI10；参考图或B01一致性10。各项取相应规则值，不重复累加超过上限。
总分0–30 simple，31–65 medium，66–100 complex。核心角色/场景、宣传、主要视觉、B01、最高质量、严格风格匹配最低medium。A/B/C/E/M类项目ID保守采用该底线，不因简单描述或节约额度降档。
该评分是可解释启发式，不是完整自然语言理解；未知描述最低medium。外部不能传分数或档位覆盖内部规则。

## 五项路由验证

|任务|分数|最终 difficulty|
|---|---:|---|
|简单装饰|4|simple|
|普通角色 / 普通场景|31 / 32|medium|
|复杂角色 + 复杂场景|74|complex|
|简单装饰但 asset_id=B01|4|medium（重要性升级）|
|简单装饰，quality_hint=最高质量|4|medium（重要性升级）|

模型ID见同目录TOML。配置允许档位重复模型，不要求三个不同模型。
返回 complexity_score、七项breakdown、difficulty、selected_model、importance、selection_reason、output_path、generated_count；selected_tier是与difficulty一致的兼容字段。

## 一资产一张

生成前以规范化asset_id建立排他文件记录于 Git 忽略的 `outputs/project_image_attempts/`。相同ID并发或重复调用，即使换路径也拒绝。只提交一次 n=1，无失败重试或换模型比较。
失败/超时也保留记录，须人工核实后明确授权返工，不能盲删记录重试。记录不含prompt或密钥。此保证覆盖当前工作区中该高级工具；基础工具和其他机器不共享记录，跨环境仍须遵守仓库资产状态与人工审核流程。

## 真实能力边界

既有适配器路径：`POST https://xingai.ai/v1/images/generations`；参考编辑路径 `/v1/images/edits`。
旧模型的成功调用不能证明本次指定的两个模型支持这些接口。本次只运行路由/模拟测试，真实图片生成0张。两个新配置模型 generation_verified=false；调用高级工具返回model_not_verified，不伪造成功或换成旧模型。后续实际验证成功并确认适配器后才能更新对应证据。
参考编辑也要求明确能力和editing_verified，不能忽略参考图改成文生图。

已读取项目实际交接入口 `ART_HANDOFF.md`；`ART_PRODUCTION_HANDOFF.md` 不存在。正式生产须先同步main、检查STATE/checker、使用B01参考、保存唯一候选、QA和人工审核，不由此工具自动批准或推进资产。
