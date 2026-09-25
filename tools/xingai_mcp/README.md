# XingAI 本地多模型 MCP 工具层

独立于 Pelican Workbench 业务、Git 和资产状态机。主 Agent 仍负责决策、文件操作、测试和 Git；本服务仅负责发现模型、调用 API、保存媒体文件。不会修改 ART 文档、推进资产状态或自动批准资产。

Python 3.11+，官方 `mcp` Python SDK，stdio 传输。服务不读取 Codex 的 `config.toml`、不读取认证文件、不自动加载 `.env`。API Key 只读取进程环境变量 `OPENAI_API_KEY`。

## 安装和启动（PowerShell）

在 `C:\Projects\plw` 执行：

```powershell
python -m venv tools/xingai_mcp/.venv
tools/xingai_mcp/.venv/Scripts/python.exe -m pip install -r tools/xingai_mcp/requirements.txt
$env:XINGAI_BASE_URL = 'https://xingai.ai'
tools/xingai_mcp/.venv/Scripts/python.exe tools/xingai_mcp/server.py
```

启动前通过本机安全方式为父进程配置 `OPENAI_API_KEY`。不要把真实值写进脚本、命令历史、README、Codex TOML 或聊天。`.env.example` 只解释变量，不包含有效凭据。普通终端启动后服务等待 MCP JSON-RPC 输入，没有欢迎输出；这是 stdio 协议所需行为。实际使用时让 MCP 客户端启动此进程。

## 已核实的来源与接口

2026-09-25，开启 TLS 校验的 `httpx` 实测：

- `https://xingai.ai/v1/models`：HTTP 200，当前令牌列出 422 个模型；字段含 `id`、`owned_by`、`supported_endpoint_types`。这是当时快照，运行时每次重新发现。
- `https://xingai.ai/api/pricing`：HTTP 200；公开 `supported_endpoint` 映射。这是接口元数据，不是所有模型均可调用的保证。
- `https://xingai.ai/api/status`：HTTP 200；站点提供的 `docs_link` 指向 `https://docs.newapi.pro`，后者跳转至 `docs.newapi.ai`。文档属于 New API 平台，不能单独证明 XingAI 部署了所有接口。

| 工具 | 路径 / 适配器 | 本阶段行为 |
| --- | --- | --- |
| `xingai_list_models` | `GET /v1/models` | 返回结构化模型清单、API 声明的供应商、三态能力和接口类型 |
| `xingai_chat` | `POST /v1/chat/completions` | 文本消息；透传可选 temperature/max_tokens；非流式 |
| `xingai_generate_image` | `POST /v1/images/generations` | OpenAI Images JSON 适配器；解析 base64 或受信 URL，校验图片并保存 |
| 同一图片工具带参考图 | `POST /v1/images/edits` | 单一本地参考图 multipart 适配器；必须显式配置该模型的 edit 能力和来源 |
| `xingai_generate_video` 默认 | 不提交 POST | XingAI 元数据声明 `/v1/videos`，所链接文档却描述 `/v1/video/generations`；返回 `interface_unconfirmed` 和发现的候选 |
| 视频文档适配器（显式启用） | `POST /v1/video/generations`，`GET /v1/video/generations/{task_id}`，返回 URL 下载 | create → poll → download 已实现且有模拟测试；尚不能宣称在 XingAI 实际部署可用 |

文档：

- [Chat Completions](https://docs.newapi.ai/en/docs/api/ai-model/chat/openai/createchatcompletion)
- [OpenAI 图片生成](https://docs.newapi.ai/en/docs/api/ai-model/images/openai/post-v1-images-generations)
- [OpenAI 图片编辑](https://docs.newapi.ai/en/docs/api/ai-model/images/openai/post-v1-images-edits)
- [创建视频任务](https://docs.newapi.ai/en/docs/api/ai-model/videos/createvideogeneration)
- [查询视频任务](https://docs.newapi.ai/en/docs/api/ai-model/videos/getvideogeneration)

接口不会把 Gemini/Qwen 的不同原生协议当作 OpenAI Images 自动套用；未确认适配器的模型返回明确错误。第一阶段未实现 Gemini 原生、Qwen 原生、Responses 或 Anthropic Messages 调用；它们的实际端点元数据仍可展示。

## 工具参数与选择规则

四个调用均返回 JSON。失败统一含 `success: false`、`error_type`、`message`、`retryable`，可增加 `http_status`、`candidates`、`task_id` 等。输入校验失败也通过 MCP `structuredContent` 返回同一格式。JSON-RPC 本身损坏或客户端没有提供合法工具调用信封时，由 MCP SDK 返回协议错误。

### xingai_list_models

可选 `task_type: chat | image | video`。能力值 `true` 表示 API 端点类型或明确配置支持；`null` 表示未知；`false` 仅来自明确配置。`owned_by` 按 API 原样报告，不根据名字推测实际供应商。聊天端点支持不等价于已确认所有输出模态。

模型列表若明确返回 404/405/501，可使用 `XINGAI_MODEL_CONFIG` 的有来源配置列表，标记 `explicit_configuration_fallback` 和 `configured_not_verified`。没有配置则报错。401、限流、网络错误不会被假模型列表掩盖。

### model="auto"

1. 实时查询模型列表。
2. 按任务能力筛选，不按模型名字猜测。
3. 若配置了 `preferred`，验证该模型仍在发现结果且能力符合后选择。
4. 只有一个合格候选时选择该候选。
5. 多个候选且没有可靠偏好时返回 `model_selection_required`，由 Codex 检查候选后再次调用；不要求人手工逐次指定模型。

没有伪造质量/价格排名，也不将某个模型硬编码为唯一选择。发现清单中的模型可能没有当前账号可用通道或余额。

复制空的 `models.example.json` 为忽略提交的 `models.local.json`，按真实资料填写，例如结构为：

```json
{
  "models": [
    {
      "id": "<从当前API发现的真实ID>",
      "source": "<确认能力的文档URL或实测记录>",
      "capabilities": {"image": true, "image_edit": true},
      "image_adapter": "openai-images"
    }
  ],
  "preferred": {"image": "<同一个真实ID>"}
}
```

上面是配置结构示例，不是可用模型列表。设置 `XINGAI_MODEL_CONFIG=tools/xingai_mcp/models.local.json`。编辑能力不能只凭生成能力推断。

### xingai_chat

`model` 默认 auto；`messages` 必填，支持 system/developer/user/assistant 的字符串 content；可选 temperature（0–2）、max_tokens（正整数）。第一阶段不支持工具消息或多模态消息。返回响应声明的 `model`、请求模型、`model_source`、choices、usage、HTTP/API 状态。若响应省略 model，明确标记来自请求，不假称已验证底层模型。

### xingai_generate_image

必填 prompt、output_path；model 默认 auto；可选 size、quality、reference_images。返回绝对路径、MIME、尺寸、字节数、模型来源和请求状态，不返回图片二进制、base64 或 revised_prompt。

输出默认保存到 `tools/xingai_mcp/outputs/`。相对 output_path 相对于此输出根目录；绝对路径也必须在根目录之内。`XINGAI_OUTPUT_ROOT` 可指定项目内的专用目录。图片后缀只允许 PNG/JPEG/WebP，并与实际文件字节相符；现有文件绝不覆盖。不能通过本工具直接任意写系统文件。

参考图只接受项目内本地文件，最多一张、4 MiB；校验格式，拒绝 URL、越界路径和多图静默截断。发送图片内容而不是本机路径。`reference_images=[]` 等同无参考图。模型必须有明确 `image_edit` 能力映射，否则返回 `capability_unconfirmed` 或候选。尺寸、quality 的各模型支持范围由 API 决定，工具不凭模型名硬编码兼容性；上游 400 会返回结构化错误。

API 返回 URL 时，只下载 HTTPS、明确允许的主机、公网 IP；不转发 Authorization、不跟随重定向。默认只允许 XingAI API 主机。确定真实 CDN 后可在 `XINGAI_DOWNLOAD_HOSTS` 添加精确主机名。URL 下载被拦截时生成可能已计费，不应盲目再生成。图片解码校验不替代美术 QA 或人工批准。

### xingai_generate_video

必填 prompt、output_path；model 默认 auto；可选 duration（秒）、reference_image、task_id。默认保守返回接口未确认。只有确认 XingAI 兼容所链接的视频文档后，才设置 `XINGAI_VIDEO_ADAPTER=newapi-video-generations`。

启用后按文档以 JSON 创建任务（参考图以 data URI 的 image 字段发送），接受 task_id，轮询 queued/in_progress/completed/failed，下载 URL 并检查 MP4 容器签名。轮询窗口 120 秒，每次 HTTP 请求独立超时；服务并不保证任务在窗口内完成。返回 `video_pending` 或轮询网络错误时保留 task_id；下次提供同一 task_id、相同模型及新文件路径即可续查，不重复购买任务。MP4 签名检查不等价于视频解码或视觉 QA。

## 安全和边界

- 不自动加载密钥文件，不写 prompt 日志，不记录请求头或上游错误体。
- 服务禁用 SDK/HTTP 日志，stdio stdout 专供 MCP；所有工具输出清除当前密钥及常见凭据形态。
- TLS 校验始终开启，不提供关闭开关。当前虚拟环境使用 httpx/certifi；系统 Python urllib 曾报告证书错误，但该结果不能证明站点证书已过期。
- 不允许输出覆盖、路径穿越、网络路径、Windows ADS/设备名、符号链接/重解析点。
- 输入图片、响应 JSON、媒体下载均有大小限制。参考图根目录固定为项目，不能读取任意系统文件。
- 生成 POST 不自动重试。超时不代表服务端未接受任务。
- 不提供远程 HTTP MCP 服务，仅本机 stdio。不承担对同机恶意进程竞态的沙箱隔离。
- 输出、虚拟环境、环境文件、本地配置由本目录 `.gitignore` 排除。测试输出不是 B04 候选，不进入资产管线。

## 测试

```powershell
tools/xingai_mcp/.venv/Scripts/python.exe -m unittest discover -s tools/xingai_mcp -p test_server.py -v
tools/xingai_mcp/.venv/Scripts/python.exe -m pip check
```

`test_server.py` 使用模拟 HTTP 服务测试成功路径/异常路径，同时真实启动 stdio 子进程验证 MCP 初始化、工具发现、合法输入和错误输入的结构化返回，以及 stderr 不含密钥/请求头/prompt。

`smoke_mcp.py` 通过真实 MCP 子进程调用真实 API。先发现真实模型，再按需传 `--chat-model <已发现ID>` 和 `--image-model <已发现ID>`。图像选项会产生一次计费请求。报告位于忽略提交的 `outputs/live_smoke_report.json`。不带模型的 auto 调用可能返回候选；如果仅一个匹配模型或设置了偏好，也可能实际生成。视频 smoke 固定使用未确认模式，不购买视频任务。

具体实测结果见 `VERIFICATION.md`，不要把模拟成功当作 XingAI 已验证支持。

## 下一步注册到 Codex（尚未修改用户配置）

根据 [Codex 官方 MCP 文档](https://developers.openai.com/codex/mcp/)，可在用户配置中增加：

```toml
[mcp_servers.xingai]
command = 'C:\Projects\plw\tools\xingai_mcp\.venv\Scripts\python.exe'
args = ['C:\Projects\plw\tools\xingai_mcp\server.py']
cwd = 'C:\Projects\plw'
env_vars = ['OPENAI_API_KEY', 'XINGAI_BASE_URL', 'XINGAI_OUTPUT_ROOT', 'XINGAI_MODEL_CONFIG', 'XINGAI_DOWNLOAD_HOSTS', 'XINGAI_VIDEO_ADAPTER']
startup_timeout_sec = 20
tool_timeout_sec = 600
```

`env_vars` 只写变量名，不写密钥。必须让启动 Codex 的父进程拥有这些环境变量，变更环境后重启相应客户端。随后用 Codex 的 MCP 列表检查四个工具。也可使用 `codex mcp add` 注册命令，但敏感变量不要通过 `--env KEY=真实值` 写入持久配置。本阶段仅提供注册说明，不修改已有 Codex provider 或权限。
