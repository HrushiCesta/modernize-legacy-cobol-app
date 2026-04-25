# Infrastructure Spec

## Runtime
- Language: Python 3.11
- Base image: python:3.11-slim

## Dependencies
All packages required by the migrated FastAPI application:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pytest==8.2.0
httpx==0.27.0
```

- `fastapi` — web framework for REST API endpoints
- `uvicorn[standard]` — ASGI server to run FastAPI
- `pytest` — test runner for unit and integration tests
- `httpx` — async HTTP client used by pytest with FastAPI's TestClient

## Network
- Port: 8000
- Protocol: HTTP

## Environment Variables
No environment variables required.

The initial account balance is hardcoded to `1000.00` (matching the COBOL `STORAGE-BALANCE` initial value). If future configuration is needed, a `INITIAL_BALANCE` env var can be added.

## External Services
No external services required.

The account balance is stored in-memory (a module-level Python variable in `data.py`), mirroring the COBOL `STORAGE-BALANCE` working-storage variable that persisted only for the lifetime of the process.
