# Test Spec

## Test Strategy
The migrated application is a **web server** (FastAPI REST API). Tests use **pytest** with FastAPI's
built-in `TestClient` (backed by `httpx`) to make real HTTP requests against the in-process app.
No external services or running containers are needed for unit/integration tests.

Test runner: `pytest`
Test file: `migrated/tests/test_operations.py`

A `reset_balance` autouse fixture resets `data._balance = 1000.00` before every test so all tests
are fully independent regardless of execution order.

---

## Unit Tests

### `migrated/data.py`
- Function: `read_balance`
  - Input: (none — reads module-level `_balance`)
  - Expected output: `1000.0` (initial value)
  - Edge case: after `write_balance(0.0)`, `read_balance()` returns `0.0`

- Function: `write_balance`
  - Input: `new_balance=500.0`
  - Expected output: `None` (side effect: `_balance` becomes `500.0`)
  - Edge case: `write_balance(0.0)` — zero balance is valid and must be stored

### `migrated/operations.py`
- Function: `get_balance`
  - Input: (none)
  - Expected output: `1000.0`
  - Edge case: called after `write_balance(0.0)` → returns `0.0`

- Function: `credit`
  - Input: `amount=200.0`
  - Expected output: `1200.0`
  - Edge case: `amount=0.0` → returns `1000.0` (balance unchanged)

- Function: `debit`
  - Input: `amount=50.0`
  - Expected output: `950.0`
  - Edge case: `amount=2000.0` → raises `ValueError` with message `"Insufficient funds for this debit."`
  - Edge case: `amount=0.0` → returns `1000.0` (balance unchanged)
  - Edge case: `amount=1000.0` (exactly equal to balance) → returns `0.0` (boundary — sufficient funds)

---

## Integration / Smoke Tests (web server)

All tests use `TestClient(app)` from `fastapi.testclient`. Base URL is implicit.

### TC-1.1 — View Current Balance
- Method: GET
- Path: `/balance`
- Request body: none
- Expected status code: 200
- Expected response: `{"balance": 1000.0}`

### TC-2.1 — Credit Account with Valid Amount
- Method: POST
- Path: `/credit`
- Request body: `{"amount": 100.0}`
- Expected status code: 200
- Expected response fields: `{"balance": 1100.0, "message": "Amount credited. New balance: 1100.00"}`

### TC-2.2 — Credit Account with Zero Amount
- Method: POST
- Path: `/credit`
- Request body: `{"amount": 0.0}`
- Expected status code: 200
- Expected response fields: `{"balance": 1000.0}` — balance unchanged

### TC-3.1 — Debit Account with Valid Amount
- Method: POST
- Path: `/debit`
- Request body: `{"amount": 50.0}`
- Expected status code: 200
- Expected response fields: `{"balance": 950.0, "message": "Amount debited. New balance: 950.00"}`

### TC-3.2 — Debit Account with Amount Greater Than Balance
- Method: POST
- Path: `/debit`
- Request body: `{"amount": 2000.0}`
- Expected status code: 400
- Expected response fields: `{"detail": "Insufficient funds for this debit."}`

### TC-3.3 — Debit Account with Zero Amount
- Method: POST
- Path: `/debit`
- Request body: `{"amount": 0.0}`
- Expected status code: 200
- Expected response fields: `{"balance": 1000.0}` — balance unchanged

---

## Batch Job Verification
Not applicable — this is a web server, not a batch job.

---

## Known Inputs for Testing
The following values are hardcoded in the COBOL source and serve as known-good anchors:

| Source | Value | Use |
|---|---|---|
| `data.cob` `STORAGE-BALANCE VALUE 1000.00` | Initial balance = `1000.00` | Starting state for all tests |
| README.md example | Credit `200.00` → balance `1200.00` | Validates credit logic |
| README.md example | Debit `300.00` → balance `900.00` | Validates debit logic (after credit) |
| TESTPLAN.md TC-3.2 | Debit `2000.00` on balance `1000.00` | Validates insufficient-funds guard |
| TESTPLAN.md TC-2.2 / TC-3.3 | Credit/debit `0.00` | Validates zero-amount edge cases |
| `operations.cob` `IF FINAL-BALANCE >= AMOUNT` | Boundary: debit exactly equal to balance is allowed | Validates `>=` (not `>`) guard |
