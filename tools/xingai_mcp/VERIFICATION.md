# 验证记录

日期：2026-09-25。全部改动限定在 `tools/xingai_mcp/`，未修改业务代码、资产状态或 Codex 配置。

## 实际网络与 MCP 验证

通过官方 SDK `ClientSession` 启动真实 stdio 子进程 `server.py`，并调用工具，不仅是直接调用 Python 函数。

| 检查 | 实际结果 |
| --- | --- |
| MCP initialize | 成功，服务名 `xingai-multimodel` |
| tools/list | 四个请求的工具全部可发现 |
| `xingai_list_models` | `GET https://xingai.ai/v1/models` → HTTP 200，422 个模型 |
| auto chat | 返回 `model_selection_required` 和 412 个具有聊天端点元数据的候选；没有伪造最优模型 |
| 真实 chat | 从发现列表选择 `gemini-2.5-flash-lite`，`POST /v1/chat/completions` → HTTP 200；响应 model 同名 |
| 真实 image | 从发现列表选择 `gpt-image-1-mini`，`POST /v1/images/generations` → HTTP 200；PNG，1024×1024，1,914,242 字节 |
| image 模型真实性边界 | 图片响应没有 model 字段，工具明确返回 `model_source=request (server omitted model)`；不能独立确认网关底层用了哪个模型 |
| 真实 video 工具调用 | 查询到四个 video 候选后返回 `interface_unconfirmed`；未提交计费视频任务 |
| 错误输入 | 空 messages 经真实 MCP 调用返回结构化 `invalid_arguments` |
| stderr 扫描 | 真实 MCP 子进程日志为 0 字节；无密钥、Authorization header 或测试 prompt |

真实测试图片（仅本机，Git 忽略）：

`outputs/smoke_20260925_081426.png`

完整不含凭据的本机报告：`outputs/live_smoke_report.json`。此图是叶子插画接口测试，**不是 Pelican 美术候选**，没有写入 `art-assets/`，没有推进 B04。

## 模拟及本地验证

14 项 unittest 全部通过，包括：

- 模型发现、未知能力不按名称推测、唯一候选自动选择、歧义候选返回、已验证配置偏好。
- 聊天成功和上游回显密钥的脱敏。
- 图片 base64 解码、真实图片字节校验、文件保存，以及单参考图 multipart 编辑适配。
- 错误输入、多个参考图拒绝、图片损坏、后缀/MIME 不符、响应大小边界。
- 文件存在拒绝覆盖、目录穿越、系统目录、UNC、Windows ADS/保留设备名保护。
- 下载 HTTPS/主机白名单/公网地址检查，视频下载不携带 API Authorization。
- 401/403/429/500、404 配置 fallback、未配置 fallback、缺少密钥、TLS 错误、POST 超时不盲重试。
- 视频未确认模式不创建任务；文档适配器 create → in_progress → completed → download；task_id 续查不重复创建；pending、failed、网络异常保留任务 ID。
- 真实 stdio 初始化、工具列表、四个工具合法输入的配置错误响应、非法参数结构化返回、日志中密钥/prompt 检查。

依赖安装完成：Python 3.11、mcp 1.30.0、httpx 0.28.1、Pillow 12.3.0。`pip check` 通过。顶层依赖锁定至本机实测版本。

交付文件及本机 JSON 报告扫描未发现实际 `OPENAI_API_KEY` 值。`git diff --check` 与逐个新增文件的 `git diff --no-index --check` 通过；Git 忽略规则已验证覆盖环境文件、虚拟环境和输出目录。工作区原先存在的 B01 本地改名未触碰，除此之外没有修改现有受跟踪文件。本阶段未 commit/push，也未注册用户级 MCP。

## 尚未实际验证的能力

- 图片参考编辑：仅模拟 multipart 合约测试；没有针对真实 XingAI 模型确认编辑能力，因此默认发现结果的 `image_edit` 为 null。
- 真正的视频生成/下载：未验证。XingAI `/api/pricing` 的 `openai-video` 路径是 `/v1/videos`；网站所链接的 New API 文档描述 `/v1/video/generations`。不能认定两者相同。
- 文档视频适配器是明确的可选实现，不默认启用；启用前需确认 XingAI 部署支持相应文档合约。
- API 返回 CDN URL 的真实媒体下载未测试；当前图片响应为 base64。下载安全和不转发认证头仅模拟测试通过。
- 未逐一验证全部 422 个模型、账号通道、余额、质量或模型专属参数。
- 未修改用户 Codex 注册；README 提供官方文档对应的注册步骤。

最初系统 Python urllib 访问返回证书校验错误；新虚拟环境的 httpx/certifi 在保持 TLS 校验开启的情况下成功访问。没有把关闭 TLS 校验作为 API 请求的解决方案。
