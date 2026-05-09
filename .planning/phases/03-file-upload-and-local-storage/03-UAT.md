---
status: complete
phase: 03-file-upload-and-local-storage
source:
  - .planning/phases/03-file-upload-and-local-storage/03-01-SUMMARY.md
started: 2026-05-09T10:38:58.6322003+08:00
updated: 2026-05-09T11:47:51.3792065+08:00
---

# Phase 3 用户验收测试：文件上传和本地存储

## Current Test

[testing complete]

## Tests

### 1. 冷启动冒烟验证
expected: 从干净状态启动后端服务，服务可以正常启动；访问 `/health` 返回健康状态；访问 `/docs` 可以看到 Swagger 文档，并且文档中包含 `/uploads`、`/uploads/{file_id}`、`/uploads/{file_id}/task` 三个上传相关接口。
result: pass

### 2. 登录并准备上传权限
expected: 通过 Mock 登录接口拿到 bearer token；后续调用上传接口时带上 `Authorization: Bearer <token>`，系统允许继续访问受保护的上传接口。
result: pass

### 3. 单文件上传
expected: 上传一张 JPEG、PNG 或 WEBP 单据图片后，接口返回 `201`；响应里有一个系统生成的 `file_...` 文件 ID，包含原始文件名、文件类型、大小、状态等安全 metadata，但不会暴露本机绝对路径。
result: pass

### 4. 多文件上传和 PDF 支持
expected: 在同一个 `/uploads` 接口里一次上传多个文件，例如一张图片加一个 PDF；接口返回多个文件 metadata；每个文件都有独立的 `file_...` ID，PDF 的 `file_kind` 应为 `pdf`，图片的 `file_kind` 应为 `image`。
result: pass

### 5. 文件技术校验
expected: 上传不支持的格式、空文件、超大文件或超过数量限制时，系统拒绝请求并返回清楚的错误；这类失败只表示“技术上传不合规”，不会要求员工提前判断业务单据内容是否正确。
result: pass

### 6. 查询上传文件 metadata
expected: 使用已上传得到的 `file_id` 调用 `GET /uploads/{file_id}`，系统返回同一份文件 metadata；使用不存在的 `file_id` 时返回 `404`。
result: pass

### 7. 关联 Agent 任务
expected: 使用已上传得到的 `file_id` 调用 `PATCH /uploads/{file_id}/task`，传入未来 Agent 任务 ID 后，系统返回更新后的 metadata，并且 `task_id` 已保存。
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
