# Research Summary

## Decision

Use Python FastAPI as the first implementation runtime. Build a modular Mock-first backend with SQLModel/SQLite, local file storage, Pydantic schemas, deterministic Agent task states, and OpenAPI contracts.

## Why

This matches the project's current constraint: no real Kaihong Wing access yet. It also preserves the future integration boundary, because Java/Kaihong can later call the Agent APIs and replace Mock APIs with real business APIs.

## Sources

- FastAPI file upload docs: https://fastapi.tiangolo.com/tutorial/request-files/
- SQLModel FastAPI dependency/session docs: https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/
- Pydantic BaseModel docs: https://docs.pydantic.dev/latest/api/base_model/
- Pydantic Field docs: https://docs.pydantic.dev/latest/concepts/fields/
- OpenAI Structured Outputs docs: https://platform.openai.com/docs/guides/structured-outputs
- WeChat Mini Program media/upload docs: https://developers.weixin.qq.com/miniprogram/dev/api/media/video/wx.chooseMedia.html and https://developers.weixin.qq.com/miniprogram/dev/api/network/upload/wx.uploadFile.html
