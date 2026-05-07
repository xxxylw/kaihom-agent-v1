# Kaihom Agent v1

Kaihom Agent v1 is a Mock-first logistics order entry Agent backend. It is designed to let business users upload logistics document photos from a phone, have an Agent extract order fields, ask for missing information, and produce a reviewable order draft before any real Kaihong Wing integration is available.

## Current Scope

This repository is Mock-only for now. It does not connect to Kaihong Wing, any real Java backend, or any company database.

## Local Setup

Run these commands in Windows PowerShell:

```powershell
cd D:\of_work\code\kaihom-agent-v1
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

If `py -3.11` is unavailable, use any Python 3.11+ interpreter.

## Run Tests

```powershell
pytest
```

## Run the API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

After startup:

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
