# Pelican Workbench 美术资产生产固定启动指令

> 用途：每次切换 ChatGPT 账号、AI 平台、中转平台、电脑或 VS Code/Codex 环境时，直接把下面整段粘贴给新环境。
> 仓库：https://github.com/hulala337/plw

请接手 Pelican Workbench（鹈鹕工作台）全量美术资产自动生产系统。不要重新设计项目，不要根据聊天记录猜测进度，必须以 GitHub main 中的项目状态为唯一事实来源。

## 强制执行顺序
1. 先执行：git checkout main；git pull origin main
2. 首先完整读取根目录 ART_HANDOFF.md，并严格遵守其中的强制接力规则。
3. 再读取：art-production-spec/ART_PRODUCTION_STATE.json、ART_ASSET_MANIFEST.json、CHARACTER_BIBLE.md、ART_DIRECTION.md、PRODUCTION_RULES.md、ART_ASSET_CATALOG.md、README.md。
4. 如果存在，再读取 art-pipeline/REFERENCE_ASSET_MAP.json、art-pipeline/ART_REVIEW_SCHEMA.json。
5. 阅读 art-production-spec/HUMAN_REVIEW_GUIDE.md，理解人工审核和 APPROVED 的唯一合法流程。
6. 执行：python art-pipeline\handoff_check.py
7. 严格从 STATE/checker 给出的 current_asset / current_key / current_status / next_action 继续。

## 不可违反的生产规则
- 不得从 B01 重新开始。
- 不得重复生成已经存在且仍有效的候选。
- 不得自行重排生产顺序、跳过当前资产或擅自改变状态。
- READY + GENERATE 时，直接执行当前资产生成，不要再次询问是否开始。
- 最终角色/场景必须是高质量原创插画；禁止用几何 SVG、简单形状拼接伪造最终美术。
- B01 pelican_master 是唯一角色风格锚点；保持角色身份、比例、视觉语言、完成度和主要色彩体系。
- 生成结果默认进入 GENERATED / CANDIDATE，必须经过技术 QA、视觉 QA 和人工审核。
- AI 的 PASS/QA 结果只能说明可以交给人审核，不能代替人工 APPROVED。
- 只有人工明确选择/确认某个候选，并将审核结果持久化到仓库后，资产才能进入 APPROVED。
- 未经人工审核不得进入 APPROVED，更不得进入 FROZEN。
- 当前资产完成生成后，先完成候选保存、QA、人工审核记录和 STATE 更新；只有这些内容已 commit + push，才能进入下一个资产。
- 不得把 API Key、密码、Token、Cookie 或其他凭据写入仓库。

## 当前任务
不要假设当前断点。以刚刚拉取的 ART_PRODUCTION_STATE.json 和 handoff_check.py 输出为准。
如果 current_status=READY 且 next_action=GENERATE：立即执行当前资产的生成任务。
如果当前状态是 GENERATED / CANDIDATE、QA 或 HUMAN REVIEW REQUIRED：先执行当前资产的审核/状态推进流程，不得生成下一个资产。
如果当前状态已经是 APPROVED 或 FROZEN：读取 STATE 中的下一合法动作，再继续，不得重复生成。

## 完成一轮资产后
必须把候选、QA、人工审核结论、状态变化持久化到仓库并 commit + push，然后才能继续下一资产。