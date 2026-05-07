# Research: Pitfalls

**Project:** Kaihom Agent v1

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Building too much before the core loop works | Start with upload -> mock extraction -> clarification -> draft save |
| Treating LLM output as trusted | Validate against Pydantic schemas and require human confirmation |
| Letting Mock APIs drift from future integration needs | Keep clear contracts and field mapping docs |
| Logging sensitive document text | Redact logs and avoid printing OCR/prompt bodies by default |
| Direct future DB access to Kaihong Wing | Use controlled Java/internal APIs only |
| Trying Mini Program first | Build mobile H5 first, then adapt to WeChat once the backend loop is proven |
| Overengineering Agent frameworks | Use deterministic workflow first; introduce LangChain/LlamaIndex only if it removes real complexity |

## LLM Structured Output Note

OpenAI's Structured Outputs guide recommends schema-constrained outputs when extracting structured data from unstructured input, because JSON mode alone does not guarantee schema adherence. Official guide: https://platform.openai.com/docs/guides/structured-outputs

For this project, any LLM extraction should output into the same Pydantic draft schema used by the API. Invalid output should be rejected and retried or downgraded to clarification.
