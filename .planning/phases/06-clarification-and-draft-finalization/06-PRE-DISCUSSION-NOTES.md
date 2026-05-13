---
phase: 06-clarification-and-draft-finalization
status: pre-discussion-notes
created: 2026-05-11
---

# Phase 6 小计划：GLM + LangGraph 澄清智能体

## 临时结论

Phase 6 不再按纯规则版 clarification 来设计，而是朝“真正智能体”方向推进：

- 引入 GLM API，Phase 6 可以真实调用模型。
- 引入 LangGraph，作为澄清问答 Agent 的内部编排层。
- 识别/抽取路线优先按 GLM 多模态能力设计：后续由 GLM 直接理解上传的图片/PDF，并返回结构化字段 JSON，而不是优先走传统本地 OCR。
- 模型费用暂不作为阻塞问题。
- 模型不能接触客户名、电话、详细地址等敏感信息。
- 大体城市、港口、粗粒度物流地点可以在脱敏后传给模型。
- LangGraph 状态倾向持久化，明天正式讨论时再确认具体落库方式。

## Phase 6 暂定目标

让 Agent 基于上传单据、Phase 5 的 `draft_preview`、`missing_fields`、`field_evidence` 和 `conflicts`：

1. 调用 GLM 多模态能力理解上传图片/PDF，提取结构化字段 JSON。
2. 后端用 Pydantic schema 校验模型返回 JSON。
3. 合并多张单据字段，保留每个字段的来源证据。
4. 检测缺失字段和冲突字段。
5. 构造必要的脱敏任务上下文。
6. 调用 GLM 生成自然的澄清问题。
7. 等待用户回答。
8. 调用 GLM 将用户回答解析成结构化字段。
9. 将解析结果合并回 `draft_preview`。
10. 再次校验是否仍有缺失字段或冲突。
11. 完整后进入 `ready_for_review`，否则继续提问。

## 识别/抽取路线

优先设计为 GLM-first：

```text
用户上传多张物流单据图片/PDF
  ↓
GLM 多模态识别和字段抽取
  ↓
模型返回严格 JSON
  ↓
后端 schema 校验和字段合并
  ↓
缺失/冲突进入 LangGraph 澄清流程
```

这样更符合个人项目展示目标：不仅是传统 OCR + 规则抽取，而是一个多模态智能体工作流。

仍然保留 provider 抽象，避免未来被单一模型绑定：

```text
DocumentRecognizer
  - MockRecognizer
  - GlmVisionRecognizer
  - LocalOcrRecognizer 后续可选
```

当前优先级：

1. `GlmVisionRecognizer`
2. `MockRecognizer`
3. `LocalOcrRecognizer` 暂时只作为后续兜底方向

模型返回的 JSON 不直接入库，必须经过：

- schema 校验
- 类型转换
- required fields 检查
- field_evidence 检查
- conflict 检查
- 必要时重试或进入追问

## 建议的分层边界

确定性后端代码负责：

- 用户认证和 task ownership。
- task 状态流转。
- required fields 校验。
- draft_preview 持久化。
- 数据库写入。
- 最终是否允许进入 `ready_for_review`。

GLM 负责：

- 理解上传的图片/PDF 单据。
- 从多张单据中提取结构化字段 JSON。
- 生成更自然的澄清问题。
- 理解用户自然语言回答。
- 将回答映射成结构化字段 JSON。
- 辅助解释字段冲突。
- 辅助处理同义字段和不同单据字段叫法。

LangGraph 负责：

- 编排多步骤澄清流程。
- 处理 human-in-the-loop 暂停和恢复。
- 根据状态决定继续提问、解析回答、合并草稿或结束。

## 脱敏要求

调用 GLM 之前必须先脱敏：

- 客户名称：替换成 `[CUSTOMER_1]` 等占位符。
- 电话号码：替换成 `[PHONE_1]` 等占位符。
- 详细地址：去掉门牌、联系人、电话等细节，只保留必要的城市/港口级信息。
- 脱敏映射只保存在本地数据库，不发送给 GLM。

注意：如果直接使用 GLM 多模态识别原始图片，模型会看到图片中的客户名、电话和详细地址。个人项目阶段可以先按 GLM-first 架构设计，但正式处理真实客户资料前，需要增加隐私模式开关：

```text
AI_INPUT_PRIVACY_MODE=raw_allowed | redacted
```

当前产品展示/个人项目优先考虑 `raw_allowed` 的技术路线；真实业务落地时默认应切到 `redacted` 或经过公司合规确认。

需要设计类似：

```text
app/services/privacy.py
```

用于生成 safe context 和本地 privacy map。

## LangGraph 状态持久化建议

因为澄清问答会暂停等待用户输入，所以建议持久化 LangGraph 状态。

候选方案：

1. 在 `AgentTaskRecord` 增加 JSON 字段：
   - `graph_state_json`
   - `last_question_json`
   - `privacy_map_json`

2. 单独建表 `agent_graph_sessions`：
   - `id`
   - `task_id`
   - `graph_thread_id`
   - `state_json`
   - `privacy_map_json`
   - `created_at`
   - `updated_at`

当前倾向：单独建 `agent_graph_sessions`，因为后续 Agent 流程会越来越复杂，和 task 主表分开更清晰。

## 明天需要继续讨论的问题

1. GLM API 是智谱官方格式，还是 OpenAI-compatible 格式？
2. Phase 6 是否直接接真实 GLM，还是保留 `FakeLLMClient` 作为测试替身？
3. 脱敏粒度怎么定：哪些地址信息可以保留，哪些必须删除？
4. LangGraph 状态用 task 字段保存，还是单独建表？
5. GLM 多模态识别图片/PDF 返回的 JSON schema 怎么设计？
6. 多张单据如何合并字段、保留 evidence、处理冲突？
7. Phase 6 的 API 要怎么设计：
   - 生成问题接口
   - 提交回答接口
   - 查询当前澄清状态接口
8. H5 Phase 7 要怎样消费 Phase 6 的问答状态？

## 暂定一句话方向

Phase 6 will introduce GLM API and LangGraph to build the first real multimodal clarification Agent: GLM extracts structured fields from uploaded logistics documents, LangGraph orchestrates missing-field and conflict clarification, and deterministic backend code owns privacy controls, validation, persistence, and task status transitions.
