---
status: complete
phase: 04-agent-task-state-machine
source: [04-01-SUMMARY.md, 04-VERIFICATION.md]
started: 2026-05-09T14:50:00+08:00
updated: 2026-05-09T15:10:00+08:00
---

# Phase 4 中文 UAT：Agent 任务状态机验收

## 验收目标

确认 Phase 4 做出的 Agent 任务状态机可以从用户/接口视角正常工作：

- 可以登录并拿到 mock token。
- 可以上传一个文件。
- 可以用上传得到的 `file_id` 创建 Agent task。
- 新 task 初始状态是 `created`。
- task 可以查询。
- task events 可以查询。
- 上传文件 metadata 会绑定到新 task。
- 自动化测试全部通过。

## Current Test

[testing complete]

## 执行前准备

### 1. 打开第一个 PowerShell：启动服务

执行：

```powershell
cd D:\of_work\code\kaihom-agent-v1
```

如果还没有激活虚拟环境，执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果依赖还没装，执行：

```powershell
python -m pip install -e ".[dev]"
```

启动 API：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
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

## Tests

### 1. 准备环境并启动 API 服务

expected: 服务启动后，健康检查返回 `status = healthy`。

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

result: pass

### 2. 登录 Mock Kaihong，获取 token

expected: 登录成功，返回 `access_token`，后续请求可以用这个 token 访问受保护接口。

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

result: pass

### 3. 上传一个测试文件，拿到 file_id

expected: 上传成功，返回一个以 `file_` 开头的 `file_id`，并且 `task_id` 还是空。

执行：

```powershell
$uploadPath = Join-Path $env:TEMP "kaihom-phase4-uat.jpg"
Set-Content -Path $uploadPath -Value "fake-jpeg-content" -Encoding ASCII

$upload = curl.exe -s -X POST "http://127.0.0.1:8000/uploads" `
  -H "Authorization: Bearer $token" `
  -F "files=@$uploadPath;type=image/jpeg" | ConvertFrom-Json

$fileId = $upload.files[0].file_id
$upload | ConvertTo-Json -Depth 10
$fileId
```

期望：

- `file_id` 以 `file_` 开头。
- `status` 是 `uploaded`。
- `task_id` 是 `null`。
- 响应里没有本地绝对路径。

result: pass

### 4. 用 file_id 创建 Agent task

expected: 创建成功，返回一个以 `task_` 开头的 `task_id`，状态是 `created`，没有进入 `extracting`。

执行：

```powershell
$payload = @{ file_ids = @($fileId) } | ConvertTo-Json

$task = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/agent/tasks" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $payload

$taskId = $task.task_id
$task | ConvertTo-Json -Depth 10
$taskId
```

期望：

- `task_id` 以 `task_` 开头。
- `status` 是 `created`。
- `file_ids` 包含刚才的 `$fileId`。
- `questions` 是空数组。
- `draft_preview` 是 `null`。
- `error_code` 和 `error_message` 是 `null`。

result: pass

### 5. 查询 Agent task 详情

expected: 可以通过 `task_id` 查到当前任务状态、关联文件、安全文件 metadata。

执行：

```powershell
$taskDetail = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/agent/tasks/$taskId" `
  -Headers $headers

$taskDetail | ConvertTo-Json -Depth 10
```

期望：

- `task_id` 等于 `$taskId`。
- `status` 是 `created`。
- `file_ids` 包含 `$fileId`。
- `files[0].task_id` 等于 `$taskId`。
- 响应中没有 `storage_path`。
- 响应中没有本地绝对路径。

result: pass

### 6. 查询 Agent task 事件记录

expected: 可以查到任务事件，至少包含 `task_created` 和 `files_attached`，顺序正确。

执行：

```powershell
$events = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/agent/tasks/$taskId/events" `
  -Headers $headers

$events | ConvertTo-Json -Depth 10
```

期望：

- `events[0].event_type` 是 `task_created`。
- `events[1].event_type` 是 `files_attached`。
- `events[0].to_status` 是 `created`。
- 这些事件是业务级事件，不是 OCR/LLM/LangGraph 内部节点事件。

result: pass

### 7. 确认上传文件 metadata 已绑定 task_id

expected: 重新查询上传文件 metadata 时，`task_id` 已经变成刚才创建的 `$taskId`。

执行：

```powershell
$fileDetail = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/uploads/$fileId" `
  -Headers $headers

$fileDetail | ConvertTo-Json -Depth 10
```

期望：

- `file_id` 等于 `$fileId`。
- `task_id` 等于 `$taskId`。

result: pass

### 8. 用不存在的 file_id 创建任务，确认失败清晰

expected: 系统返回 404，不会创建半成品任务。

执行：

```powershell
$badPayload = @{ file_ids = @("file_does_not_exist") } | ConvertTo-Json

try {
  Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/agent/tasks" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $badPayload
} catch {
  $_.Exception.Response.StatusCode.value__
  $_.ErrorDetails.Message
}
```

期望：

- 状态码是 `404`。
- 错误信息包含 `Uploaded file not found`。

result: pass

### 9. 跑 Phase 4 专项自动化测试

expected: Phase 4 专项测试全部通过。

执行：

```powershell
python -m pytest tests/test_agent_tasks.py -q
```

期望输出：

```text
9 passed
```

result: pass

### 10. 跑全量自动化测试

expected: 所有已有测试全部通过，没有破坏前面 Phase 1-3 的功能。

执行：

```powershell
python -m pytest
```

期望输出：

```text
27 passed
```

result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

<!-- 如果你执行某一步时发现结果不符合预期，我会把问题记录到这里，并继续诊断。 -->
