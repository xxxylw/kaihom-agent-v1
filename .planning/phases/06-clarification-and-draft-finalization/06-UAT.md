---
status: complete
phase: 06-clarification-and-draft-finalization
source:
  - 06-01-SUMMARY.md
  - 06-02-SUMMARY.md
  - 06-VERIFICATION.md
started: 2026-05-13T00:00:00Z
updated: 2026-05-13T00:00:00Z
language: zh-CN
mode: powershell-http-walkthrough
---

# Phase 6 PowerShell HTTP 验证文档：澄清问答与草稿最终保存

## Current Test

[testing complete]

## 这份文档怎么用

这份文档不是只跑 `pytest`。它是让你在自己电脑的 PowerShell 里，像真实前端/H5 一样一步步发 HTTP 请求，观察接口返回结果。

Phase 6 要验证的完整业务链路是：

```text
登录
  -> 上传单据
  -> 创建 Agent task
  -> 触发 extract，得到 draft_preview
  -> 对缺字段 task 获取澄清问题
  -> 用户提交回答
  -> 系统合并回答，进入 ready_for_review
  -> 对 ready draft 执行 finalize
  -> 保存到 Mock Kaihong draft
```

注意：Phase 6 不做图片/PDF 多模态字段识别。上传的文件仍然通过 Phase 5 的 mock extraction fixture 生成 `draft_preview`。本阶段验证的是“抽取之后的澄清和保存”。

## 前置准备

### 0.1 进入项目目录

执行什么：

```powershell
cd D:\of_work\code\kaihom-agent-v1
```

意义是什么：

- 后续命令都依赖当前目录。
- 本地 SQLite 数据库、上传目录、FastAPI app 都以项目根目录为基准。

预期结果：

- 当前 PowerShell 路径变成项目根目录。

结果：pass

### 0.2 可选：配置 DeepSeek API Key

执行什么：

如果你想真实验证“自然语言回答 -> DeepSeek 解析 -> 合并字段”，需要设置：

```powershell
$env:KAIHOM_DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
$env:KAIHOM_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
$env:KAIHOM_DEEPSEEK_MODEL = "deepseek-v4-flash"
```

如果你没有 key，可以跳过。跳过后：

- `GET /clarification` 仍然可以验证本地生成问题。
- `POST /clarification/answers` 会返回“缺少 DeepSeek API key”的可恢复错误。
- 这也是一个有意义的验证点：系统不会在没有模型配置时假装已经解析成功。

意义是什么：

- DeepSeek 是 Phase 6 的文本智能来源。
- 手工 HTTP 请求不像测试代码那样可以 monkeypatch fake model。
- 所以真实 answer merge 需要真实模型配置。

预期结果：

- 有 key：后续回答提交可能完成字段解析。
- 无 key：后续回答提交应返回 503，不污染草稿。

结果：pass

### 0.3 启动 FastAPI 服务

执行什么：

另开一个 PowerShell 窗口，执行：

```powershell
cd D:\of_work\code\kaihom-agent-v1
python -m uvicorn app.main:app --reload --port 8000
```

意义是什么：

- 后续所有验证都通过 HTTP 调用本地服务。
- `--reload` 方便本地开发，但验证时重点是服务能正常启动。

预期结果：

看到类似：

```text
Uvicorn running on http://127.0.0.1:8000
```

结果：pass

### 0.4 在验证窗口设置基础变量

执行什么：

回到另一个 PowerShell 验证窗口，执行：

```powershell
$BaseUrl = "http://127.0.0.1:8000"
```

意义是什么：

- 后续命令都通过 `$BaseUrl` 访问本地 API，避免重复写 URL。

预期结果：

- 没有报错。

结果：pass

## Tests

### 1. 健康检查：确认服务活着

执行什么：

```powershell
Invoke-RestMethod -Method GET -Uri "$BaseUrl/health"
```

意义是什么：

- 这是最小烟雾测试。
- 如果这里失败，后面的上传、task、clarification 都没有意义。

预期结果：

返回类似：

```text
status app_name          app_version environment
------ --------          ----------- -----------
ok     Kaihom Agent API  0.1.0       local
```

结果：pass

### 2. 登录 Mock Kaihong，拿 bearer token

执行什么：

```powershell
$LoginBody = @{
  username = "yw001"
  password = "mock123456"
} | ConvertTo-Json

$Login = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/mock/kaihong/auth/login" `
  -ContentType "application/json" `
  -Body $LoginBody

$Token = $Login.access_token
$Headers = @{ Authorization = "Bearer $Token" }
$Token
```

意义是什么：

- Phase 6 的接口都是受保护接口。
- 必须先拿到 token，才能模拟真实业务用户访问自己的 task。

预期结果：

返回类似：

```text
mock-token-yw001
```

结果：pass

### 3. 上传一张“不完整单据”fixture

执行什么：

先创建一个临时文件：

```powershell
Set-Content -Path .\incomplete-receipt.jpg -Value "fake-jpeg"
```

用 `curl.exe` 上传。注意这里用 `curl.exe`，不要用 PowerShell 的 `curl` alias。

```powershell
$UploadIncomplete = curl.exe -s `
  -X POST "$BaseUrl/uploads" `
  -H "Authorization: Bearer $Token" `
  -F "files=@incomplete-receipt.jpg;type=image/jpeg" `
  | ConvertFrom-Json

$IncompleteFileId = $UploadIncomplete.files[0].file_id
$IncompleteFileId
```

意义是什么：

- Phase 6 依赖前面阶段的上传和 task。
- 文件名 `incomplete-receipt.jpg` 会触发 Phase 5 mock OCR 的“不完整字段”fixture。
- 这个 task 后续应该进入 `need_more_info`，用于验证澄清问题。

预期结果：

返回类似：

```text
file_xxxxxxxxxxxx
```

结果：pass

### 4. 用不完整文件创建 Agent task

执行什么：

```powershell
$CreateIncompleteBody = @{
  file_ids = @($IncompleteFileId)
  customer_id = "cust_001"
} | ConvertTo-Json

$IncompleteTask = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks" `
  -Headers $Headers `
  -ContentType "application/json" `
  -Body $CreateIncompleteBody

$IncompleteTaskId = $IncompleteTask.task_id
$IncompleteTaskId
$IncompleteTask.status
```

意义是什么：

- Agent task 是整个工作流的业务容器。
- 后续 extract、clarification、answer、finalize 都围绕 `task_id` 进行。

预期结果：

```text
task_xxxxxxxxxxxx
created
```

结果：pass

### 5. 对不完整 task 执行 extract

执行什么：

```powershell
$IncompleteExtract = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks/$IncompleteTaskId/extract" `
  -Headers $Headers

$IncompleteExtract.status
$IncompleteExtract.draft_preview.missing_fields
```

意义是什么：

- 这一步验证 Phase 5 到 Phase 6 的边界。
- Phase 6 不直接识别图片/PDF，它消费的是 extract 之后的 `draft_preview`。
- 不完整 fixture 应该产生缺失字段，从而进入澄清流程。

预期结果：

状态应为：

```text
need_more_info
```

`missing_fields` 中应该能看到类似：

```text
shipper_phone
consignee_address
```

结果：pass

### 6. 获取澄清问题

执行什么：

```powershell
$Clarification = Invoke-RestMethod `
  -Method GET `
  -Uri "$BaseUrl/agent/tasks/$IncompleteTaskId/clarification" `
  -Headers $Headers

$Clarification.session_id
$Clarification.task_status
$Clarification.current_question.text
$Clarification.current_question.requested_fields
```

意义是什么：

- 这是 Phase 6 的第一个核心用户可见能力。
- 系统不只是返回“字段缺失”，而是生成一个用户可以回答的问题。
- 这里也会创建 `agent_graph_sessions` 记录，保存当前问题和图状态。

预期结果：

```text
graph_xxxxxxxxxxxx
need_more_info
Please confirm ...
```

并且 `requested_fields` 里应该包含缺失字段。

如果这里返回 502：

- 含义是服务已经进入 DeepSeek 问题生成路径，但真实 DeepSeek 调用失败，例如 API key、模型名、网络或额度有问题。
- 这是可恢复配置/外部服务错误，不应再表现为 500 Internal Server Error。
- 你可以临时清掉 `$env:KAIHOM_DEEPSEEK_API_KEY` 后重启服务，验证本地 fallback 问题生成；或者修正 DeepSeek 配置后重试。

结果：pass

### 7A. 如果没有 DeepSeek Key：验证回答提交返回可恢复错误

执行什么：

如果你没有设置 `$env:KAIHOM_DEEPSEEK_API_KEY`，执行：

```powershell
$AnswerBody = @{
  answer_text = "发货人电话是 13800000001，收货地址是 Ningbo Port。"
} | ConvertTo-Json

try {
  Invoke-RestMethod `
    -Method POST `
    -Uri "$BaseUrl/agent/tasks/$IncompleteTaskId/clarification/answers" `
    -Headers $Headers `
    -ContentType "application/json" `
    -Body $AnswerBody
} catch {
  $_.Exception.Response.StatusCode.value__
  $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
  $Reader.ReadToEnd()
}
```

意义是什么：

- 手工 HTTP 没有测试里的 fake model。
- 没有 DeepSeek key 时，系统不能假装解析成功。
- 正确行为是返回可恢复错误，task 仍保持 `need_more_info`，等待配置好模型后重试。

预期结果：

HTTP 状态码应为：

```text
503
```

错误内容类似：

```json
{"detail":"DeepSeek API key is required to parse clarification answers"}
```

结果：pass

### 7B. 如果配置了 DeepSeek Key：提交澄清回答并合并字段

执行什么：

如果你已经设置了 `$env:KAIHOM_DEEPSEEK_API_KEY`，执行：

```powershell
$AnswerBody = @{
  answer_text = "发货人电话是 13800000001，收货地址是 Ningbo Port。"
} | ConvertTo-Json

$AnswerResult = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks/$IncompleteTaskId/clarification/answers" `
  -Headers $Headers `
  -ContentType "application/json" `
  -Body $AnswerBody

$AnswerResult.task_status
$AnswerResult.remaining_missing_fields
$AnswerResult.draft_preview.field_evidence.shipper_phone
```

意义是什么：

- 这是 Phase 6 的第二个核心能力：用户自然语言回答被模型解析，再由后端校验并合并进草稿。
- 注意最终写入权在后端，不在 DeepSeek。

预期结果：

- 如果模型正确解析所有缺失字段，`task_status` 应变为：

```text
ready_for_review
```

- `remaining_missing_fields` 应为空。
- `field_evidence.shipper_phone.source_file_id` 应为：

```text
user_clarification
```

结果：pass

### 8. 未完成 task 不能 finalize

执行什么：

如果你的不完整 task 还停在 `need_more_info`，执行：

```powershell
try {
  Invoke-RestMethod `
    -Method POST `
    -Uri "$BaseUrl/agent/tasks/$IncompleteTaskId/finalize" `
    -Headers $Headers
} catch {
  $_.Exception.Response.StatusCode.value__
  $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
  $Reader.ReadToEnd()
}
```

意义是什么：

- 系统不能把缺字段草稿保存成最终草稿。
- finalization 必须被 `ready_for_review` 状态保护。

预期结果：

HTTP 状态码：

```text
400
```

错误内容应说明当前状态不能 finalize，例如：

```json
{"detail":"Cannot finalize task in status need_more_info"}
```

结果：pass

### 9. 上传一张“完整单据”fixture

执行什么：

```powershell
Set-Content -Path .\complete-entrustment.jpg -Value "fake-jpeg"

$UploadComplete = curl.exe -s `
  -X POST "$BaseUrl/uploads" `
  -H "Authorization: Bearer $Token" `
  -F "files=@complete-entrustment.jpg;type=image/jpeg" `
  | ConvertFrom-Json

$CompleteFileId = $UploadComplete.files[0].file_id
$CompleteFileId
```

意义是什么：

- 需要一个不缺字段的 task 来验证 finalization 成功路径。
- 文件名 `complete-entrustment.jpg` 会触发 Phase 5 的完整 fixture。

预期结果：

返回类似：

```text
file_xxxxxxxxxxxx
```

结果：pass

### 10. 创建完整 task 并执行 extract

执行什么：

```powershell
$CreateCompleteBody = @{
  file_ids = @($CompleteFileId)
  customer_id = "cust_001"
} | ConvertTo-Json

$CompleteTask = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks" `
  -Headers $Headers `
  -ContentType "application/json" `
  -Body $CreateCompleteBody

$CompleteTaskId = $CompleteTask.task_id

$CompleteExtract = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks/$CompleteTaskId/extract" `
  -Headers $Headers

$CompleteExtract.status
$CompleteExtract.draft_preview.fields.customer_name
$CompleteExtract.draft_preview.fields.cargo_name
$CompleteExtract.draft_preview.missing_fields
```

意义是什么：

- 这是 finalization 的前置条件。
- 只有 `ready_for_review` 的 task 才能保存成 Mock Kaihong draft。

预期结果：

状态：

```text
ready_for_review
```

字段示例：

```text
Ningbo Future Trading Co., Ltd.
Auto parts
```

`missing_fields` 应为空。

结果：pass

### 11. Finalize ready draft

执行什么：

```powershell
$Finalize = Invoke-RestMethod `
  -Method POST `
  -Uri "$BaseUrl/agent/tasks/$CompleteTaskId/finalize" `
  -Headers $Headers

$Finalize.status
$Finalize.draft_id
$Finalize.source_file_ids
$Finalize.draft_preview.fields.cargo_name
$Finalize.audit
```

意义是什么：

- 这是 Phase 6 的最终闭环。
- 系统把 `draft_preview` 转成 Mock Kaihong draft 请求，并通过已有 Mock Kaihong 边界保存。
- 这证明 Agent 不是只会问答，而是能产出一个可审核草稿。

预期结果：

```text
finalized
draft_xxxxxxxxxxxx
Auto parts
```

`audit.event_type` 应为：

```text
draft_finalized
```

结果：pass

### 12. 查询 task detail，确认状态已 finalized

执行什么：

```powershell
$FinalTask = Invoke-RestMethod `
  -Method GET `
  -Uri "$BaseUrl/agent/tasks/$CompleteTaskId" `
  -Headers $Headers

$FinalTask.status
$FinalTask.draft_preview.fields.cargo_name
```

意义是什么：

- finalize 接口返回成功还不够，还要确认 task 本身状态已经持久化。
- Phase 7 H5 后续查询 task detail 时，需要看到最终状态。

预期结果：

```text
finalized
Auto parts
```

结果：pass

### 13. 查询事件历史，确认业务事件完整

执行什么：

```powershell
$Events = Invoke-RestMethod `
  -Method GET `
  -Uri "$BaseUrl/agent/tasks/$CompleteTaskId/events" `
  -Headers $Headers

$Events.events | Select-Object event_type, from_status, to_status, message
```

意义是什么：

- Agent 工作流需要可追踪。
- 如果用户或开发者问“这个 task 怎么从上传走到 finalized”，事件历史应该能解释。

预期结果：

事件列表中至少应包含：

```text
task_created
files_attached
extraction_started
mock_ocr_completed
fields_extracted
draft_finalized
```

结果：pass

### 14. 查询 OpenAPI，确认 Phase 6 接口可被前端发现

执行什么：

```powershell
$OpenApi = Invoke-RestMethod -Method GET -Uri "$BaseUrl/openapi.json"

$OpenApi.paths.PSObject.Properties.Name -contains "/agent/tasks/{task_id}/clarification"
$OpenApi.paths.PSObject.Properties.Name -contains "/agent/tasks/{task_id}/clarification/answers"
$OpenApi.paths.PSObject.Properties.Name -contains "/agent/tasks/{task_id}/finalize"
```

意义是什么：

- Phase 7 H5 页面需要对接这些接口。
- OpenAPI 能看到这些路径，说明合同不是隐藏实现。

预期结果：

```text
True
True
True
```

结果：pass

### 15. 范围检查：确认没有把图片/PDF 多模态识别塞进 Phase 6

执行什么：

```powershell
Select-String `
  -Path pyproject.toml,app\**\*.py `
  -Pattern "VisionRecognizer","GlmVision","image recognition","PDF recognition" `
  -CaseSensitive
```

意义是什么：

- 我们明确拆过范围：Phase 6 只做文本澄清和保存。
- 图片/PDF 多模态识别以后再做。
- 这一步避免阶段边界失控。

预期结果：

- 不应出现新的 `GlmVisionRecognizer`、`VisionRecognizer`、`image recognition`、`PDF recognition` 实现。

结果：pass

## Summary

total: 15
passed: 15
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None.

## 最终结论

Phase 6 通过 HTTP 手工验收。

你可以在 PowerShell 里验证到：

- 服务能启动并返回健康状态。
- Mock 用户可以登录。
- 用户可以上传单据并创建 Agent task。
- `extract` 会生成 `draft_preview`。
- 不完整草稿会进入 `need_more_info`。
- 系统可以生成澄清问题。
- 未配置 DeepSeek 时，回答提交会返回可恢复错误，不会假装成功。
- 配置 DeepSeek 后，回答可以被解析并合并回草稿。
- 未完成草稿不能 finalize。
- 完整草稿可以 finalize 并保存到 Mock Kaihong draft。
- task 状态最终变成 `finalized`。
- 事件历史可追踪。
- OpenAPI 暴露了 Phase 6 的三个关键接口。
- Phase 6 没有越界实现图片/PDF 多模态识别。
