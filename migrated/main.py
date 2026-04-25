"""
main.py — FastAPI entry point for the Account Management System.

Converted from main.cob (COBOL MainProgram).

The original COBOL program presented an interactive terminal menu with four
choices driven by a PERFORM UNTIL CONTINUE-FLAG = 'NO' loop:
  1. View Balance   → GET  /balance
  2. Credit Account → POST /credit
  3. Debit Account  → POST /debit
  4. Exit           → (no REST equivalent; stop the server process)

DISPLAY statements become JSON response fields.
ACCEPT  statements become JSON request body fields.
CALL 'Operations' USING ... dispatches become calls into operations.py.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import operations

# ---------------------------------------------------------------------------
# FastAPI application
# Mirrors: PROGRAM-ID. MainProgram.
# ---------------------------------------------------------------------------

app = FastAPI(title="Account Management System")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AmountRequest(BaseModel):
    """
    Request body for POST /credit and POST /debit.

    Mirrors the COBOL ACCEPT AMOUNT statement — the terminal prompt is replaced
    by a JSON field in the request body.
    """
    amount: float


class BalanceResponse(BaseModel):
    """
    Response body for credit/debit endpoints.

    Mirrors the COBOL DISPLAY "... New balance: " FINAL-BALANCE output.
    """
    balance: float
    message: str


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

@app.get("/balance")
def get_balance_route() -> dict:
    """
    GET /balance — View current account balance.

    Mirrors EVALUATE USER-CHOICE WHEN 1:
        CALL 'Operations' USING 'TOTAL '
    which in operations.cob called DataProgram with 'READ' and displayed the
    resulting FINAL-BALANCE.

    Returns:
        {"balance": <current balance rounded to 2 d.p.>}
    """
    bal: float = operations.get_balance()
    return {"balance": round(bal, 2)}


@app.post("/credit")
def credit_route(body: AmountRequest) -> dict:
    """
    POST /credit — Add an amount to the account balance.

    Mirrors EVALUATE USER-CHOICE WHEN 2:
        CALL 'Operations' USING 'CREDIT'
    which in operations.cob accepted the amount, read the current balance,
    added the amount, wrote the updated balance back, and displayed the result.

    Request body:
        {"amount": <float>}

    Returns:
        {"balance": <new balance rounded to 2 d.p.>, "message": "Amount credited. New balance: <X>"}
    """
    new_bal: float = operations.credit(body.amount)
    return {
        "balance": round(new_bal, 2),
        "message": f"Amount credited. New balance: {new_bal:.2f}",
    }


@app.post("/debit")
def debit_route(body: AmountRequest) -> dict:
    """
    POST /debit — Subtract an amount from the account balance.

    Mirrors EVALUATE USER-CHOICE WHEN 3:
        CALL 'Operations' USING 'DEBIT '
    which in operations.cob accepted the amount, checked IF FINAL-BALANCE >= AMOUNT,
    subtracted on success and displayed the result, or displayed "Insufficient funds"
    on failure.

    The insufficient-funds path from COBOL becomes an HTTP 400 response here.
    operations.debit() raises ValueError("Insufficient funds for this debit.")
    which is caught and re-raised as an HTTPException so FastAPI returns:
        HTTP 400  {"detail": "Insufficient funds for this debit."}

    Request body:
        {"amount": <float>}

    Returns (success):
        {"balance": <new balance rounded to 2 d.p.>, "message": "Amount debited. New balance: <X>"}

    Returns (insufficient funds):
        HTTP 400  {"detail": "Insufficient funds for this debit."}
    """
    try:
        new_bal: float = operations.debit(body.amount)
    except ValueError as e:
        # Mirrors: DISPLAY "Insufficient funds for this debit."
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "balance": round(new_bal, 2),
        "message": f"Amount debited. New balance: {new_bal:.2f}",
    }


# ---------------------------------------------------------------------------
# Direct execution entry point
# Mirrors: STOP RUN (orderly shutdown of the program).
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
