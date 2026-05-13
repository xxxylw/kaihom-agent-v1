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
---

# Phase 6 中文验收说明：澄清问答与草稿最终保存

## Current Test

[testing complete]

## 这一阶段到底验证什么

Phase 6 验证的是：在 Phase 5 已经生成 `draft_preview`、`missing_fields`、`field_evidence` 和 `conflicts` 之后，系统能不能完成下面这条业务闭环：

```text
已有抽取草稿
  -> 发现缺失字段或冲突字段
  -> 生成澄清问题
  -> 用户提交回答
  -> 系统解析并合并回答
  -> 草稿完整后进入 ready_for_review
  -> 用户 finalize
  -> 保存到 Mock Kaihong draft
```

Phase 6 不验证图片/PDF 多模态识别。图片/PDF 字段识别仍然留给后续阶段；这里验证的是“抽取结果之后的人机澄清和保存”。

## Tests

### 1. 建立澄清会话基础

执行什么：

- 检查 `app/models/agent_graph_session.py` 是否存在。
- 确认系统新增了独立的 `AgentGraphSessionRecord`。
- 确认它保存 `task_id`、`graph_thread_id`、`state_json`、`current_question_json`、`answer_history_json`、`privacy_map_json` 等字段。

意义是什么：

- 澄清问答不是一次性动作，它会暂停等待用户回答。
- 所以 LangGraph 的状态不能只放内存里，否则服务重启或用户晚点回答时状态会丢。
- 单独建 `agent_graph_sessions`，可以让 Agent task 主表继续保持干净，后续 Agent 流程复杂后也更容易扩展。

预期结果：

- 每个需要澄清的 task 都可以关联一个 graph session。
- 当前问题、历史回答、脱敏映射和图状态可以持久保存。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_graph.py -q
4 passed
```

### 2. 配置 DeepSeek 文本能力

执行什么：

- 检查 `app/core/config.py` 中的 DeepSeek 配置：
  - `deepseek_api_key`
  - `deepseek_base_url`
  - `deepseek_model`
  - `deepseek_timeout_seconds`
  - `deepseek_max_retries`
- 检查 `app/services/deepseek_client.py`。
- 确认测试不会依赖真实 DeepSeek 网络请求。

意义是什么：

- Phase 6 决策是直接接 DeepSeek API，不做复杂的通用 provider 抽象。
- DeepSeek 只负责文本澄清：生成自然问题、解析用户自然语言回答。
- 测试必须可重复，所以用 fake HTTP response 验证客户端逻辑，而不是打真实模型。

预期结果：

- 没有 API key 时，应用仍可导入和运行测试。
- 有 API key 时，DeepSeek client 使用配置的 base URL、model、timeout 和 retry。
- 模型返回 JSON 异常时会重试一次。

结果：pass

自动化证据：

```text
python -m pytest tests/test_deepseek_client.py -q
4 passed
```

### 3. 调用模型前做最小脱敏

执行什么：

- 检查 `app/services/privacy.py`。
- 构造带客户名、电话、详细地址的 `OrderDraftPreview`。
- 调用 redaction helper，确认输出给模型的内容里不再包含敏感原文。

意义是什么：

- Phase 6 虽然不把原始图片/PDF 发给 DeepSeek，但 `draft_preview` 和用户回答里仍可能包含客户名、电话、详细地址。
- 这些内容进入模型前要先替换成占位符。
- 本地保留 privacy map，模型只看到 `[CUSTOMER_1]`、`[PHONE_1]`、`[ADDRESS_1]` 这类安全上下文。

预期结果：

- 客户名被替换。
- 电话号码被替换。
- 地址字段被替换。
- 货名、重量、港口等非敏感业务信息仍可保留，避免模型完全失去上下文。

结果：pass

自动化证据：

```text
python -m pytest tests/test_privacy.py -q
2 passed
```

### 4. 生成澄清问题

执行什么：

- 先走已有链路创建一个 task：
  - 上传文件。
  - 创建 Agent task。
  - 调用 `/agent/tasks/{task_id}/extract`。
- 对于状态为 `need_more_info` 的 task，调用：

```text
GET /agent/tasks/{task_id}/clarification
```

意义是什么：

- 用户看到的第一个关键体验是：系统不是只说“字段缺了”，而是能生成一个可以回答的问题。
- 这个接口也是 Phase 7 H5 页面后续展示问题的主要入口。

预期结果：

- 返回 `session_id`。
- 返回 `current_question`。
- `current_question` 中包含结构化的 `requested_fields`。
- task 仍保持在 `need_more_info`，等待用户回答。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_get_clarification_returns_current_question -q
1 passed
```

### 5. 用户提交澄清回答

执行什么：

- 在已有 clarification session 上调用：

```text
POST /agent/tasks/{task_id}/clarification/answers
```

- 请求体包含用户自然语言回答：

```json
{
  "answer_text": "Here are the missing details."
}
```

意义是什么：

- 这是“人机协作补全订单”的核心动作。
- 用户不应该必须理解内部字段名；系统要能把回答解析成结构化字段。
- 后端不能盲信模型，必须验证字段名和值类型。

预期结果：

- 系统解析出字段更新。
- 字段名必须属于 `ALL_DRAFT_FIELDS`。
- 字段值必须能通过 `OrderDraftFields` 的 Pydantic 校验。
- 合法字段被合并回 `draft_preview`。
- 新字段 evidence 记录为 `user_clarification`。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_submit_answer_merges_fields_and_reaches_ready_for_review -q
1 passed
```

### 6. 防止模型乱写字段

执行什么：

- 模拟模型返回不存在的字段，例如：

```json
{
  "fields": {
    "not_a_field": "x"
  }
}
```

- 提交回答接口后检查系统行为。

意义是什么：

- LLM 输出只能作为建议，不能直接改数据库。
- 如果模型返回幻觉字段，后端必须挡住。
- 这是 Phase 6 的安全边界：模型不拥有最终写入权。

预期结果：

- API 返回 400。
- 原来的 `draft_preview` 不被污染。
- 原来的 `missing_fields` 不被错误清空。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_submit_answer_rejects_unknown_model_field_without_mutating_draft -q
1 passed
```

### 7. 草稿完整后进入 ready_for_review

执行什么：

- 对缺失字段 task 提交足够完整的澄清回答。
- 检查 task 状态。

意义是什么：

- Phase 6 的目标不是无限聊天，而是补全草稿。
- 当 required fields 都完整、阻塞冲突都解决后，task 应该从 `need_more_info` 进入 `ready_for_review`。
- 这个状态是 finalization 的前置门槛。

预期结果：

- `remaining_missing_fields` 为空。
- `is_complete` 为 true。
- task 状态变为 `ready_for_review`。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_submit_answer_merges_fields_and_reaches_ready_for_review -q
1 passed
```

### 8. 未完成草稿不能 finalize

执行什么：

- 创建一个仍然处于 `need_more_info` 的 task。
- 调用：

```text
POST /agent/tasks/{task_id}/finalize
```

意义是什么：

- 系统不能把缺字段或有冲突的草稿保存成最终草稿。
- 这保护了业务流程：finalize 只能发生在用户已补全、系统已校验的状态之后。

预期结果：

- API 返回 400。
- 错误信息说明当前状态还是 `need_more_info`。
- task 不会进入 `finalized`。
- 不会创建 Mock Kaihong draft。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_finalize_rejects_need_more_info_task -q
1 passed
```

### 9. ready draft 可以保存到 Mock Kaihong

执行什么：

- 创建一个完整 fixture task。
- 调用 `/extract` 后确认它是 `ready_for_review`。
- 调用：

```text
POST /agent/tasks/{task_id}/finalize
```

意义是什么：

- 这是 Phase 6 的最终业务闭环。
- 系统要把内部 `draft_preview` 转成 Mock Kaihong draft 请求，走已有 Mock Kaihong 边界保存，而不是绕过业务 API。
- 这样后续真实 Kaihong 集成时，替换的是边界实现，不是整个 Agent 流程。

预期结果：

- 返回 `draft_id`。
- task 状态变为 `finalized`。
- 返回 source file IDs。
- 返回 draft field values。
- audit metadata 中记录 `draft_finalized`。

结果：pass

自动化证据：

```text
python -m pytest tests/test_clarification_api.py::test_finalize_ready_task_saves_mock_kaihong_draft -q
1 passed
```

### 10. OpenAPI 合同可见

执行什么：

- 读取 FastAPI OpenAPI paths。
- 检查以下接口是否存在：

```text
/agent/tasks/{task_id}/clarification
/agent/tasks/{task_id}/clarification/answers
/agent/tasks/{task_id}/finalize
```

意义是什么：

- Phase 7 H5 页面需要靠 OpenAPI 合同对接后端。
- DRAFT-04 要求未来 Kaihong/Java-facing 合同能从 API 文档里看见。
- 这一步确保新增流程不是隐藏在服务层，而是真正暴露为可消费 API。

预期结果：

- 三个接口都出现在 OpenAPI 文档中。

结果：pass

自动化证据：

```text
python -c "from app.main import app; paths=app.openapi()['paths']; print('/agent/tasks/{task_id}/clarification' in paths, '/agent/tasks/{task_id}/clarification/answers' in paths, '/agent/tasks/{task_id}/finalize' in paths)"
True True True
```

### 11. 回归测试：旧功能没有被破坏

执行什么：

- 跑全量测试：

```text
python -m pytest -q
```

意义是什么：

- Phase 6 改到了 task、database、schema、API，这些都是 Phase 3-5 也依赖的公共路径。
- 必须确认上传、创建 task、mock extraction、Mock Kaihong 旧功能没有回归。

预期结果：

- 全量测试通过。

结果：pass

自动化证据：

```text
python -m pytest -q
55 passed
```

### 12. 范围检查：没有偷偷实现图片/PDF 多模态识别

执行什么：

- 搜索代码中是否新增 `GlmVisionRecognizer`、多模态识别、图片/PDF recognition 相关实现。
- 检查 Phase 6 的实际新增能力是否仍然只围绕 text clarification。

意义是什么：

- 我们在讨论阶段明确收窄过 Phase 6：先做 LangGraph + DeepSeek 文本澄清闭环。
- 图片/PDF 多模态字段识别以后再做。
- 这一步防止 Phase 6 失控，把后续识别阶段提前塞进来。

预期结果：

- 没有新增图片/PDF 多模态识别实现。
- `/extract` -> `draft_preview` 仍然是识别层和澄清层之间的稳定边界。

结果：pass

自动化证据：

```text
Phase 6 verification: No GlmVisionRecognizer or new multimodal recognition implementation was added.
```

## Summary

total: 12
passed: 12
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None.

## 总结

Phase 6 已通过验收。它完成的是：

- 用独立 `agent_graph_sessions` 保存澄清状态。
- 用 DeepSeek 文本接口生成问题和解析回答。
- 调用模型前进行最小脱敏。
- 暴露澄清状态查询、回答提交、最终保存三个 API。
- 后端校验并合并回答，防止模型乱写字段。
- 草稿完整后进入 `ready_for_review`。
- ready draft 可以 finalize，并保存到 Mock Kaihong draft。

下一阶段 Phase 7 可以基于这些 API 做手机 H5 demo。
