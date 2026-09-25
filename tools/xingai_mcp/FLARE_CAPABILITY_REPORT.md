# gpt-image-2.5-flare 能力核查

核查日期：2026-09-25。仅只读 GET；未发送图片 POST、B04 prompt 或 B01 文件。图片额度消耗为0，B04状态未修改。

结论：image_generation / image_editing / reference_image 均 **unverified**。保留 model_not_verified 门禁。

## 实际证据

- `GET https://xingai.ai/v1/models`，Bearer 环境密钥认证，HTTP 200。目标模型存在，但 supported_endpoint_types 只有 openai。
- `GET https://xingai.ai/api/pricing`，HTTP 200。目标模型同样只声明 openai；公开映射为 `POST /v1/chat/completions`。image_ratio 是价格元数据，不能证明图像输出。
- 同一公开映射确实声明通用 image-generation 为 `POST /v1/images/generations`，但没有将目标模型关联到它。
- `GET https://xingai.ai/api/status` 返回 docs_link=`https://docs.newapi.pro`。
- `GET https://xingai.ai/openapi.json` 返回 HTTP 200 **text/html**，不是可用 OpenAPI JSON，不能把200当成接口存在证明。
- 服务商所链接的 [New API 图片文档](https://docs.newapi.ai/en/docs/api/ai-model/images/openai/post-v1-images-generations) 和 [编辑文档](https://docs.newapi.ai/en/docs/api/ai-model/images/openai/post-v1-images-edits) 均可访问，均未提到目标模型。是平台通用协议，不是目标模型部署保证。

## 17项核查（仅针对该模型）

|项|结果|
|---|---|
|1 真正图片生成端点|未确认该模型支持；网关通用端点存在|
|2 完整路径|该模型未知；通用候选 https://xingai.ai/v1/images/generations|
|3 HTTP method|该模型未知；通用文档 POST|
|4 authentication|网关模型查询实测 Bearer；通用图片文档 Bearer；目标图片接口未实测|
|5 request body|目标未知；通用生成JSON/编辑multipart不能直接套用|
|6 model参数|模型列表id为gpt-image-2.5-flare；图片body参数契约未知|
|7 prompt参数|未知；通用文档prompt string不构成目标支持证据|
|8 size|未知，不能推断允许分辨率|
|9 quality|未知，不能推断允许枚举|
|10 response_format|目标未知|
|11 URL/base64|目标未知；通用文档示例包含url/b64_json|
|12 异步任务|未知|
|13 reference image|unverified|
|14 参考图参数名|未知；通用编辑文档image不能证明目标支持|
|15 image editing|unverified|
|16 B01风格参考|unverified，未上传B01|
|17 多参考图|unverified|

## 下一步所需

需要 XingAI 提供明确针对该模型的图片接口文档或请求/响应示例，含完整路径、认证、body字段和返回格式。确认后才按授权执行一次最小文生图smoke test（不带B01、不生成B04），保存至Git忽略的test_output。参考图/编辑须单独验证，不能以文生图成功推断。

本次未执行smoke test，因为尚未满足“已确认图片endpoint”的前提。没有请求通过chat端点生成图片来绕过门禁，也没有伪造verification。
