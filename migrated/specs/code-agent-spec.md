# Code Generation Spec

## Dependency Map

```
main.cob      → calls → operations.cob  (CALL 'Operations' USING operation-type)
operations.cob → calls → data.cob       (CALL 'DataProgram' USING 'READ'/'WRITE', FINAL-BALANCE)
data.cob      → (leaf — no outbound calls)
```

Python equivalent:
```
main.py (FastAPI app + routers)
  → imports → operations.py  (get_balance, credit, debit functions)
      → imports → data.py    (read_balance, write_balance functions)
```

## Conversion Order
1. `data.cob` → `migrated/data.py` — leaf module, no dependencies; must exist before operations.py imports it.
2. `operations.cob` → `migrated/operations.py` — depends on data.py; must exist before main.py imports it.
3. `main.cob` → `migrated/main.py` — entry point; depends on operations.py; converted last.
4. *(new)* `migrated/requirements.txt` — generated from inferred imports; no source equivalent.
5. *(new)* `migrated/tests/test_operations.py` — ported from TESTPLAN.md; no source equivalent.
6. *(new)* `migrated/conftest.py` — pytest configuration to put project root on sys.path.

## API Contracts

### `GET /balance` (defined in `main.py`)
- Request body: none
- Response fields: `{"balance": float}` — current account balance rounded to 2 decimal places
- Consumed by: `tests/test_operations.py`

### `POST /credit` (defined in `main.py`)
- Request body: `{"amount": float}` — amount to add; must be >= 0
- Response fields: `{"balance": float, "message": str}`
  - `balance` — new balance after credit
  - `message` — e.g. `"Amount credited. New balance: 1200.00"`
- Consumed by: `tests/test_operations.py`

### `POST /debit` (defined in `main.py`)
- Request body: `{"amount": float}` — amount to subtract; must be >= 0
- Response fields (success): `{"balance": float, "message": str}`
  - `balance` — new balance after debit
  - `message` — e.g. `"Amount debited. New balance: 900.00"`
- Response fields (insufficient funds — HTTP 400): `{"detail": str}`
  - `detail` — `"Insufficient funds for this debit."`
- Consumed by: `tests/test_operations.py`

## Data File Quirks
No external data files. The COBOL `STORAGE-BALANCE` is an in-memory working-storage variable
initialised to `1000.00`. In Python this becomes a module-level variable in `data.py`:

```python
_balance: float = 1000.00
```

Note: "All values are uniform" — no structural irregularities.

## File Specs

---

### `data.cob` → `migrated/data.py`
- Module name: `data`
- Classes: none
- Functions / module-level state:
  - `_balance: float = 1000.00` — module-level variable; mirrors COBOL `STORAGE-BALANCE PIC 9(6)V99 VALUE 1000.00`
  - `read_balance() -> float` — returns current value of `_balance`; mirrors `IF OPERATION-TYPE = 'READ' MOVE STORAGE-BALANCE TO BALANCE`
  - `write_balance(new_balance: float) -> None` — sets `_balance = new_balance`; mirrors `IF OPERATION-TYPE = 'WRITE' MOVE BALANCE TO STORAGE-BALANCE`
- Imports required: none (stdlib only — `global` keyword used to mutate module-level state)
- Cross-file references: none (leaf module)
- Conversion strategy:
  - The COBOL `PASSED-OPERATION` / `OPERATION-TYPE` dispatch (`READ` vs `WRITE`) is replaced by two explicit Python functions — no string dispatch needed.
  - `PIC 9(6)V99` maps to Python `float` (or `Decimal` if precision is critical — use `float` for simplicity here).
  - `GOBACK` maps to a plain `return`.
  - The `global _balance` declaration must appear inside `write_balance` before the assignment.

---

### `operations.cob` → `migrated/operations.py`
- Module name: `operations`
- Classes: none
- Functions:
  - `get_balance() -> float` — reads and returns current balance; mirrors `IF OPERATION-TYPE = 'TOTAL' CALL 'DataProgram' USING 'READ'`
  - `credit(amount: float) -> float` — adds `amount` to balance, writes it back, returns new balance; mirrors `CREDIT` branch
  - `debit(amount: float) -> float` — subtracts `amount` from balance if sufficient funds, writes it back, returns new balance; raises `ValueError("Insufficient funds for this debit.")` if `balance < amount`; mirrors `DEBIT` branch with `IF FINAL-BALANCE >= AMOUNT` guard
- Imports required:
  - `from data import read_balance, write_balance`
- Cross-file references:
  - imports `read_balance`, `write_balance` from `migrated/data.py`
- Conversion strategy:
  - The COBOL `PASSED-OPERATION` string dispatch (`TOTAL`, `CREDIT`, `DEBIT`) is replaced by three distinct Python functions — cleaner and more Pythonic.
  - `CALL 'DataProgram' USING 'READ', FINAL-BALANCE` → `balance = read_balance()`
  - `ADD AMOUNT TO FINAL-BALANCE` → `balance += amount`
  - `CALL 'DataProgram' USING 'WRITE', FINAL-BALANCE` → `write_balance(balance)`
  - `SUBTRACT AMOUNT FROM FINAL-BALANCE` → `balance -= amount`
  - Insufficient-funds path raises `ValueError` so the FastAPI layer can catch it and return HTTP 400.
  - `GOBACK` → `return balance`

---

### `main.cob` → `migrated/main.py`
- Module name: `main`
- Classes: none
- FastAPI app object: `app = FastAPI(title="Account Management System")`
- Pydantic models:
  - `AmountRequest` — request body for credit/debit: `amount: float`
  - `BalanceResponse` — response body: `balance: float`, `message: str`
- Route handlers (functions):
  - `get_balance_route() -> dict` — `GET /balance`; calls `operations.get_balance()`; returns `{"balance": round(bal, 2)}`
  - `credit_route(body: AmountRequest) -> dict` — `POST /credit`; calls `operations.credit(body.amount)`; returns `{"balance": round(new_bal, 2), "message": f"Amount credited. New balance: {new_bal:.2f}"}`
  - `debit_route(body: AmountRequest) -> dict` — `POST /debit`; calls `operations.debit(body.amount)`; catches `ValueError` and raises `HTTPException(status_code=400, detail=str(e))`; on success returns `{"balance": round(new_bal, 2), "message": f"Amount debited. New balance: {new_bal:.2f}"}`
- Imports required:
  - `from fastapi import FastAPI, HTTPException`
  - `from pydantic import BaseModel`
  - `import operations`
- Cross-file references:
  - imports `get_balance`, `credit`, `debit` from `migrated/operations.py`
- Conversion strategy:
  - The COBOL `PERFORM UNTIL CONTINUE-FLAG = 'NO'` interactive menu loop is replaced by three REST endpoints — one per operation (view balance, credit, debit). The "Exit" option (choice 4) has no REST equivalent; the server simply stops when the container is stopped.
  - `EVALUATE USER-CHOICE WHEN 1` → `GET /balance`
  - `EVALUATE USER-CHOICE WHEN 2` → `POST /credit`
  - `EVALUATE USER-CHOICE WHEN 3` → `POST /debit`
  - `DISPLAY` statements become JSON response fields.
  - `ACCEPT` statements become request body fields.
  - `CALL 'Operations' USING 'TOTAL '` → `operations.get_balance()`
  - `CALL 'Operations' USING 'CREDIT'` → `operations.credit(amount)`
  - `CALL 'Operations' USING 'DEBIT '` → `operations.debit(amount)`
  - All balance values are rounded to 2 decimal places in responses (matching COBOL `PIC 9(6)V99`).
  - Add `if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)` at the bottom for direct execution.

---

### *(new)* `migrated/requirements.txt`
- Source path: (none — generated)
- Content:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  pytest==8.2.0
  httpx==0.27.0
  ```

---

### *(new)* `migrated/conftest.py`
- Source path: (none — generated)
- Purpose: Puts the `migrated/` directory on `sys.path` so `import operations`, `import data`, `import main` all resolve correctly when pytest is run from inside the container at `/app`.
- Content:
  ```python
  import sys, os
  sys.path.insert(0, os.path.dirname(__file__))
  ```

---

### `TESTPLAN.md` → `migrated/tests/test_operations.py`
- Module name: `test_operations`
- Test framework: `pytest` with FastAPI `TestClient` (from `httpx`)
- Classes: none (plain pytest functions)
- Test functions (mapped from TESTPLAN.md test cases):
  - `test_view_balance()` — TC-1.1: GET /balance returns HTTP 200 and `{"balance": 1000.0}`
  - `test_credit_valid_amount()` — TC-2.1: POST /credit `{"amount": 100.0}` → HTTP 200, balance = 1100.0
  - `test_credit_zero_amount()` — TC-2.2: POST /credit `{"amount": 0.0}` → HTTP 200, balance unchanged
  - `test_debit_valid_amount()` — TC-3.1: POST /debit `{"amount": 50.0}` → HTTP 200, balance decreases by 50
  - `test_debit_insufficient_funds()` — TC-3.2: POST /debit `{"amount": 2000.0}` → HTTP 400, detail contains "Insufficient funds"
  - `test_debit_zero_amount()` — TC-3.3: POST /debit `{"amount": 0.0}` → HTTP 200, balance unchanged
- Imports required:
  - `import pytest`
  - `from fastapi.testclient import TestClient`
  - `from main import app`
  - `import data`
- Fixture:
  - `@pytest.fixture(autouse=True)` named `reset_balance` — resets `data._balance = 1000.00` before each test so tests are independent and order-agnostic.
- Conversion strategy:
  - Each row in the TESTPLAN.md table maps to one pytest function.
  - Use `TestClient(app)` (synchronous) — no async needed.
  - Assert both HTTP status code and specific JSON response fields per the API Contracts above.
  - The `reset_balance` fixture is critical: without it, credits/debits from one test bleed into the next.
