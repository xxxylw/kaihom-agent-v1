---
status: complete
phase: 05-mock-ocr-and-field-extraction
source: [05-01-SUMMARY.md, 05-VERIFICATION.md]
started: 2026-05-11T14:20:00+08:00
updated: 2026-05-11T14:35:00+08:00
---

# Phase 5 中文 UAT：Mock OCR 与字段抽取验收

## 验收目标

确认 Phase 5 做出的 Mock OCR 与字段抽取能力，从使用者/API 视角可以正常工作：

- 可以登录并拿到 mock token。
- 可以上传一个物流单据文件。
- 可以用上传得到的 `file_id` 创建 Agent task。
- 可以触发 `POST /agent/tasks/{task_id}/extract`。
- 完整 mock OCR fixture 会生成 `ready_for_review` 的任务状态。
- 不完整 mock OCR fixture 会生成 `need_more_info` 的任务状态。
- `draft_preview` 里包含 `fields`、`missing_fields`、`field_evidence`、`conflicts`。
- 抽取事件可以在 task events 里查到。
- 自动化测试全部通过。

## Current Test

```text
[testing complete]
```

## 执行前准备

### 1. 打开第一个 PowerShell：启动服务

执行：

```powershell
cd D:\of_work\code\kaihom-agent-v1
```

意义：

```text
进入项目根目录。后面所有命令都依赖当前目录是 kaihom-agent-v1。
```

如果还没有激活虚拟环境，执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

意义：

```text
让 PowerShell 使用项目自己的 Python 依赖环境，而不是系统里别的 Python 环境。
```

如果依赖还没装，执行：

```powershell
python -m pip install -e ".[dev]"
```

意义：

```text
以可编辑模式安装当前项目，并安装 dev 测试依赖。
这样 uvicorn、pytest、FastAPI 代码导入都会使用当前代码目录里的最新文件。
```

启动 API：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

意义：

```text
启动 FastAPI 后端服务。
Phase 5 的上传、建任务、触发抽取、查询 task 都要通过这个本地 API 服务完成。
```

期望看到类似：

```text
Uvicorn running on http://127.0.0.1:8000
```

这个窗口保持运行，不要关闭。

### 2. 打开第二个 PowerShell：执行验收命令

执行：

```powershell
cd D:\of_work\code\kaihom-agent-v1
```

如果还没有激活虚拟环境，执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

意义：

```text
第二个窗口专门用来发请求和跑测试。
第一个窗口负责运行服务，第二个窗口负责模拟用户/API 调用。
```

## Tests

### 1. 健康检查：确认 API 服务可用

做什么：

```text
访问 /health，确认后端服务已经启动成功。
```

执行：

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

期望输出包含：

```json
{
  "status": "healthy"
}
```

意义：

```text
这是最基础的冷启动检查。
如果这一步失败，后面的上传、建任务、抽取接口都不需要继续测，应该先看 uvicorn 服务是否启动。
```

result: pass

### 2. 登录 Mock Kaihong，获取 token

做什么：

```text
用 mock 用户登录，拿到 bearer token。
```

执行：

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/mock/kaihong/auth/login" `
  -ContentType "application/json" `
  -Body (@{ username = "yw001"; password = "mock123456" } | ConvertTo-Json)

$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
$token
```

期望输出类似：

```text
mock-token-yw001
```

意义：

```text
Phase 5 的 extract 接口是受保护接口。
必须先登录，后续请求才能证明“只有当前用户可以操作自己的 task”。
```

result: pass

### 3. 上传完整单据 fixture 文件

做什么：

```text
上传一个文件名为 complete-entrustment.jpg 的测试文件。
Phase 5 的 mock OCR 会根据这个文件名返回“字段完整”的 OCR 文本。
```

执行：

```powershell
$completePath = Join-Path $env:TEMP "complete-entrustment.jpg"
Set-Content -Path $completePath -Value "fake-jpeg-content" -Encoding ASCII

$completeUpload = curl.exe -s -X POST "http://127.0.0.1:8000/uploads" `
  -H "Authorization: Bearer $token" `
  -F "files=@$completePath;type=image/jpeg" | ConvertFrom-Json

$completeFileId = $completeUpload.files[0].file_id
$completeUpload | ConvertTo-Json -Depth 10
$completeFileId
```

期望：

```text
file_id 以 file_ 开头。
status 是 uploaded。
task_id 是 null。
响应里没有本地绝对路径。
```

意义：

```text
这一步验证 Phase 5 仍然复用 Phase 3 的上传能力。
同时文件名 complete-entrustment.jpg 会驱动 mock OCR 选择完整物流单据 fixture。
```

result: pass

### 4. 创建完整单据 Agent task

做什么：

```text
用完整单据的 file_id 创建一个 Agent task。
```

执行：

```powershell
$completeTaskPayload = @{ file_ids = @($completeFileId) } | ConvertTo-Json

$completeTask = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/agent/tasks" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $completeTaskPayload

$completeTaskId = $completeTask.task_id
$completeTask | ConvertTo-Json -Depth 10
$completeTaskId
```

期望：

```text
task_id 以 task_ 开头。
status 是 created。
draft_preview 是 null。
questions 是空数组。
```

意义：

```text
Phase 5 是在 Phase 4 的 task 状态机之上工作。
抽取前，task 应该还只是 created，不应该提前出现 draft_preview。
```

result: pass

### 5. 触发完整单据字段抽取

做什么：

```text
调用 Phase 5 新增的 extract 接口，让系统执行 mock OCR 和字段抽取。
```

执行：

```powershell
$completeExtract = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/agent/tasks/$completeTaskId/extract" `
  -Headers $headers

$completeExtract | ConvertTo-Json -Depth 20
```

期望：

```text
status 是 ready_for_review。
draft_preview 不为空。
draft_preview.fields.customer_name 是 Ningbo Future Trading Co., Ltd.
draft_preview.fields.cargo_name 是 Auto parts。
draft_preview.fields.package_count 是 20。
draft_preview.fields.gross_weight_kg 是 1200。
draft_preview.missing_fields 是空数组。
draft_preview.field_evidence 里有 cargo_name 等字段证据。
draft_preview.conflicts 是空数组。
questions 仍然是空数组。
```

意义：

```text
这是 Phase 5 的核心正向流程。
它证明系统可以从 mock OCR 文本抽取结构化物流字段，并在必填字段齐全时把任务推进到 ready_for_review。
questions 为空也很重要，因为 Phase 5 只检测缺字段，不生成用户问题；问题生成留给 Phase 6。
```

result: pass

### 6. 查询完整单据 task，确认 draft_preview 已持久化

做什么：

```text
重新查询刚才的 task，确认抽取结果不是只存在于接口响应里，而是已经保存到数据库。
```

执行：

```powershell
$completeDetail = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/agent/tasks/$completeTaskId" `
  -Headers $headers

$completeDetail | ConvertTo-Json -Depth 20
```

期望：

```text
status 仍然是 ready_for_review。
draft_preview.fields.customer_name 仍然存在。
missing_fields 仍然是空数组。
field_evidence 仍然存在。
```

意义：

```text
验证 Phase 5 的 JSON 持久化设计。
后续 Phase 6 需要读取这个 draft_preview 和 missing_fields 来生成澄清问题。
未来查询/报表也会依赖这些稳定字段名。
```

result: pass

### 7. 查询完整单据 task events，确认抽取事件被记录

做什么：

```text
查询 task 的事件流水，确认抽取过程有业务级事件记录。
```

执行：

```powershell
$completeEvents = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/agent/tasks/$completeTaskId/events" `
  -Headers $headers

$completeEvents | ConvertTo-Json -Depth 20
```

期望事件里包含：

```text
task_created
files_attached
extraction_started
mock_ocr_completed
fields_extracted
```

意义：

```text
验证 Phase 5 没有把抽取当成黑盒。
业务人员或开发人员可以通过 events 看到任务什么时候开始抽取、什么时候完成 mock OCR、什么时候字段抽取完成。
```

result: pass

### 8. 上传不完整单据 fixture 文件

做什么：

```text
上传一个文件名为 incomplete-receipt.jpg 的测试文件。
Phase 5 的 mock OCR 会根据这个文件名返回“缺少部分必填字段”的 OCR 文本。
```

执行：

```powershell
$incompletePath = Join-Path $env:TEMP "incomplete-receipt.jpg"
Set-Content -Path $incompletePath -Value "fake-jpeg-content" -Encoding ASCII

$incompleteUpload = curl.exe -s -X POST "http://127.0.0.1:8000/uploads" `
  -H "Authorization: Bearer $token" `
  -F "files=@$incompletePath;type=image/jpeg" | ConvertFrom-Json

$incompleteFileId = $incompleteUpload.files[0].file_id
$incompleteUpload | ConvertTo-Json -Depth 10
$incompleteFileId
```

期望：

```text
file_id 以 file_ 开头。
上传成功。
```

意义：

```text
这一步准备一个“缺字段”的场景。
真实业务里单据经常缺电话、地址、重量等信息，所以 Phase 5 必须能识别缺失，而不是假装一切完整。
```

result: pass

### 9. 创建不完整单据 Agent task 并触发抽取

做什么：

```text
对 incomplete-receipt.jpg 创建 task，并调用 extract。
```

执行：

```powershell
$incompleteTaskPayload = @{ file_ids = @($incompleteFileId) } | ConvertTo-Json

$incompleteTask = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/agent/tasks" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $incompleteTaskPayload

$incompleteTaskId = $incompleteTask.task_id

$incompleteExtract = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/agent/tasks/$incompleteTaskId/extract" `
  -Headers $headers

$incompleteExtract | ConvertTo-Json -Depth 20
```

期望：

```text
status 是 need_more_info。
draft_preview.fields.customer_name 是 Shanghai United Logistics Importer。
draft_preview.missing_fields 包含 shipper_phone。
draft_preview.missing_fields 包含 consignee_address。
draft_preview.missing_fields 不包含 origin。
questions 仍然是空数组。
```

意义：

```text
这是 Phase 5 的核心缺字段流程。
它证明系统可以区分“必填缺失”和“可选缺失”。
origin 是可选字段，所以缺了不应该进入 missing_fields。
```

result: pass

### 10. 验证 OpenAPI 已暴露 extract 接口

做什么：

```text
检查 OpenAPI 文档里是否包含 Phase 5 新增接口。
```

执行：

```powershell
$openapi = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/openapi.json"
$openapi.paths.PSObject.Properties.Name | Where-Object { $_ -like "*extract*" }
```

期望输出：

```text
/agent/tasks/{task_id}/extract
```

意义：

```text
OpenAPI 是以后前端、Java/Kaihong 适配层、接口联调的重要依据。
这个接口出现在 OpenAPI 里，说明它是正式 API 契约的一部分。
```

result: pass

### 11. 跑 Phase 5 专项自动化测试

做什么：

```text
运行 Phase 5 相关测试。
```

执行：

```powershell
python -m pytest tests/test_extraction.py tests/test_agent_tasks.py -q
```

期望输出：

```text
19 passed
```

意义：

```text
自动化测试覆盖字段 schema、mock OCR、字段抽取、缺字段检测、证据 metadata、extract API、状态流转和事件记录。
这是比手工 curl 更稳定的回归保障。
```

result: pass

### 12. 跑全量自动化测试

做什么：

```text
运行整个项目测试。
```

执行：

```powershell
python -m pytest -q
```

期望输出：

```text
38 passed
```

意义：

```text
确认 Phase 5 没有破坏 Phase 1-4 的功能。
如果这里失败，说明新抽取能力可能影响了健康检查、mock Kaihong、上传或 Agent task 状态机。
```

result: pass

### 13. 确认没有引入 LangChain / LangGraph 依赖

做什么：

```text
检查 pyproject.toml 里没有 langchain 或 langgraph。
```

执行：

```powershell
Select-String -Path pyproject.toml -Pattern "langchain|langgraph" -CaseSensitive:$false
```

期望：

```text
没有任何输出。
```

意义：

```text
这是我们 Phase 5 的设计决策：先用确定性 Python/Pydantic 规则跑通字段抽取。
LangGraph 留到 Phase 6 讨论人机澄清状态流时再决定。
```

result: pass

### 14. 清理本地测试上传文件和 metadata

做什么：

```text
清理本次 UAT 上传产生的本地文件和上传 metadata。
```

执行：

```powershell
python -m app.tools.cleanup_uploads
```

期望输出类似：

```text
Deleted upload metadata records: [N]
Deleted upload files: [N]
```

意义：

```text
保持本地开发环境干净。
这里的 N 是当前本地累计数量，不固定；你这次看到 28/28 是正常通过。
这个清理命令会同步清 uploads 文件和数据库里的上传 metadata，避免下次测试时混入旧数据。
```

result: pass

## Summary

total: 14
passed: 14
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

<!-- 如果你执行某一步时发现结果不符合预期，我会把问题记录到这里，并继续诊断。 -->
