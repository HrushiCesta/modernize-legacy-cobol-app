"""
test_operations.py — Pytest integration tests for the Account Management System.

Ported from TESTPLAN.md. Covers all 7 test cases (TC-1.1 through TC-4.1).

Each test uses a synchronous FastAPI TestClient and an autouse fixture that
resets the in-memory balance to 1000.00 before every test, ensuring full
test isolation regardless of execution order.

Test case mapping:
    TC-1.1  →  test_view_balance()
    TC-2.1  →  test_credit_valid_amount()
    TC-2.2  →  test_credit_zero_amount()
    TC-3.1  →  test_debit_valid_amount()
    TC-3.2  →  test_debit_insufficient_funds()
    TC-3.3  →  test_debit_zero_amount()
    TC-4.1  →  test_exit_application()  (no REST equivalent — verified by design)
"""

import pytest
from fastapi.testclient import TestClient

from main import app
import data

# ---------------------------------------------------------------------------
# Shared test client
# ---------------------------------------------------------------------------

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixture — balance isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_balance():
    """Reset the in-memory balance to 1000.00 before each test.

    Without this fixture, credits and debits from one test bleed into the
    next, making the suite order-dependent and fragile.

    Directly mutates data._balance — the module-level variable that
    data.read_balance() and data.write_balance() operate on.
    """
    data._balance = 1000.00
    yield
    # No teardown required; the next invocation of the fixture will reset
    # the balance again before the following test runs.


# ---------------------------------------------------------------------------
# TC-1.1: View Current Balance
# ---------------------------------------------------------------------------

def test_view_balance():
    """TC-1.1 — GET /balance returns HTTP 200 and the initial balance of 1000.00.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : Send GET /balance.
    Expected Result: HTTP 200, {"balance": 1000.0}.
    """
    response = client.get("/balance")

    assert response.status_code == 200

    body = response.json()
    assert body["balance"] == 1000.0


# ---------------------------------------------------------------------------
# TC-2.1: Credit Account with Valid Amount
# ---------------------------------------------------------------------------

def test_credit_valid_amount():
    """TC-2.1 — POST /credit with 100.00 increases balance to 1100.00.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : POST /credit {"amount": 100.0}.
    Expected Result: HTTP 200, balance = 1100.0, message confirms new balance.
    """
    response = client.post("/credit", json={"amount": 100.0})

    assert response.status_code == 200

    body = response.json()
    assert body["balance"] == 1100.0
    assert "1100.00" in body["message"]


# ---------------------------------------------------------------------------
# TC-2.2: Credit Account with Zero Amount
# ---------------------------------------------------------------------------

def test_credit_zero_amount():
    """TC-2.2 — POST /credit with 0.00 leaves balance unchanged at 1000.00.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : POST /credit {"amount": 0.0}.
    Expected Result: HTTP 200, balance = 1000.0.
    """
    response = client.post("/credit", json={"amount": 0.0})

    assert response.status_code == 200

    body = response.json()
    assert body["balance"] == 1000.0
    assert "1000.00" in body["message"]


# ---------------------------------------------------------------------------
# TC-3.1: Debit Account with Valid Amount
# ---------------------------------------------------------------------------

def test_debit_valid_amount():
    """TC-3.1 — POST /debit with 50.00 reduces balance to 950.00.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : POST /debit {"amount": 50.0}.
    Expected Result: HTTP 200, balance = 950.0, message confirms new balance.
    """
    response = client.post("/debit", json={"amount": 50.0})

    assert response.status_code == 200

    body = response.json()
    assert body["balance"] == 950.0
    assert "950.00" in body["message"]


# ---------------------------------------------------------------------------
# TC-3.2: Debit Account with Amount Greater Than Balance
# ---------------------------------------------------------------------------

def test_debit_insufficient_funds():
    """TC-3.2 — POST /debit with 2000.00 (> balance) returns HTTP 400.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : POST /debit {"amount": 2000.0}.
    Expected Result: HTTP 400, detail contains "Insufficient funds",
                     and the balance remains unchanged at 1000.00.
    """
    response = client.post("/debit", json={"amount": 2000.0})

    assert response.status_code == 400

    body = response.json()
    assert "Insufficient funds" in body["detail"]

    # Verify balance was not modified — it should still be 1000.00.
    balance_response = client.get("/balance")
    assert balance_response.status_code == 200
    assert balance_response.json()["balance"] == 1000.0


# ---------------------------------------------------------------------------
# TC-3.3: Debit Account with Zero Amount
# ---------------------------------------------------------------------------

def test_debit_zero_amount():
    """TC-3.3 — POST /debit with 0.00 leaves balance unchanged at 1000.00.

    Pre-conditions : balance reset to 1000.00 by the autouse fixture.
    Test Steps     : POST /debit {"amount": 0.0}.
    Expected Result: HTTP 200, balance = 1000.0.
    """
    response = client.post("/debit", json={"amount": 0.0})

    assert response.status_code == 200

    body = response.json()
    assert body["balance"] == 1000.0
    assert "1000.00" in body["message"]


# ---------------------------------------------------------------------------
# TC-4.1: Exit the Application
# ---------------------------------------------------------------------------

def test_exit_application():
    """TC-4.1 — Exit option has no REST equivalent by design.

    In the original COBOL program the user selected option 4 to exit the
    interactive menu loop (PERFORM UNTIL CONTINUE-FLAG = 'NO').  In the
    REST API the server simply continues running; there is no /exit endpoint.
    The COBOL "Exit" path is therefore not applicable (N/A) in the REST world
    — the server process is stopped externally (e.g. container shutdown).

    This test records that intentional design decision and confirms that no
    /exit route was added to the API.
    """
    # Confirm that no /exit endpoint exists (the route was intentionally
    # omitted during conversion — see main.py conversion strategy notes).
    response = client.get("/exit")
    assert response.status_code == 404, (
        "TC-4.1: A /exit route should NOT exist. "
        "The exit functionality has no REST equivalent and is handled "
        "by stopping the server process externally."
    )
