# Research: Features

**Project:** Kaihom Agent v1

## Table-Stakes Features for v1 Mock

- Health endpoint and OpenAPI docs.
- Mock login/current user endpoints.
- Mock customers, dictionaries, and historical orders.
- Multipart image upload from mobile/H5.
- Agent task creation and task status query.
- Mock OCR text extraction path.
- Field extraction into a draft schema.
- Missing-field clarification questions.
- User answer submission and draft updates.
- Draft finalization and local persistence.

## Differentiating Features Later

- Real OCR and multimodal extraction.
- Confidence scoring and source evidence per field.
- Similar historical order lookup.
- Customer-specific field rules.
- WeChat/Enterprise WeChat integration.
- Real Java/Kaihong adapter with service-to-service authentication.

## Evidence

- WeChat Mini Program upload flow commonly uses media selection plus `wx.uploadFile`, which uploads to a developer server with multipart form data. Official API references are at `developers.weixin.qq.com/miniprogram/dev/api/media/video/wx.chooseMedia.html` and `developers.weixin.qq.com/miniprogram/dev/api/network/upload/wx.uploadFile.html`.
- FastAPI's upload docs map directly to this flow because it accepts multipart uploads via `UploadFile`.
