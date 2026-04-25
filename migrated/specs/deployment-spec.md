# Deployment Spec

## Local Run
Exact shell command to start the application from the `migrated/` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml

```yaml
version: "3.9"

services:
  account-api:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## Build Steps
1. Install Python dependencies: `pip install -r requirements.txt`
2. No database migrations required — balance is stored in-memory.
3. Start the server: `uvicorn main:app --host 0.0.0.0 --port 8000`

## CI/CD Guidance
- Trigger: on push to `main` / on pull request
- Build command: `cd migrated && docker compose build`
- Test command: `cd migrated && docker compose up -d && docker compose exec -T account-api pytest -v`
- Deploy command: Manual — push image to registry and redeploy container on target host.
