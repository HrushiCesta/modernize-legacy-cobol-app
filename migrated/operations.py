# Converted from operations.cob (COBOL Operations subprogram)
#
# Original COBOL structure:
#   LINKAGE SECTION:
#     01  PASSED-OPERATION   PIC X(6).
#   WORKING-STORAGE SECTION:
#     01  OPERATION-TYPE     PIC X(6).
#     01  AMOUNT             PIC 9(6)V99.
#     01  FINAL-BALANCE      PIC 9(6)V99 VALUE 1000.00.
#
# The single COBOL subprogram dispatched on PASSED-OPERATION ('TOTAL ', 'CREDIT',
# 'DEBIT ') and used DISPLAY/ACCEPT for I/O.  That string-dispatch pattern is
# replaced here by three explicit Python functions — one per operation — which
# are cleaner, testable, and integrate naturally with the FastAPI layer in
# main.py.
#
# COBOL → Python mapping:
#   CALL 'DataProgram' USING 'READ',  FINAL-BALANCE  →  balance = read_balance()
#   CALL 'DataProgram' USING 'WRITE', FINAL-BALANCE  →  write_balance(balance)
#   ADD AMOUNT TO FINAL-BALANCE                       →  balance += amount
#   SUBTRACT AMOUNT FROM FINAL-BALANCE                →  balance -= amount
#   IF FINAL-BALANCE >= AMOUNT … ELSE …               →  if balance >= amount … else raise
#   DISPLAY "Insufficient funds …"                    →  raise ValueError(…)
#   GOBACK                                            →  return balance
#
# The insufficient-funds path raises ValueError so the FastAPI route handler
# can catch it and convert it to an HTTP 400 response.

from data import read_balance, write_balance


def get_balance() -> float:
    """Return the current account balance.

    Mirrors the COBOL 'TOTAL ' branch:
        IF OPERATION-TYPE = 'TOTAL '
            CALL 'DataProgram' USING 'READ', FINAL-BALANCE
            DISPLAY "Current balance: " FINAL-BALANCE
    """
    balance: float = read_balance()
    return balance


def credit(amount: float) -> float:
    """Add *amount* to the balance, persist it, and return the new balance.

    Mirrors the COBOL 'CREDIT' branch:
        CALL 'DataProgram' USING 'READ', FINAL-BALANCE
        ADD AMOUNT TO FINAL-BALANCE
        CALL 'DataProgram' USING 'WRITE', FINAL-BALANCE
        DISPLAY "Amount credited. New balance: " FINAL-BALANCE
    """
    balance: float = read_balance()
    balance += amount
    write_balance(balance)
    return balance


def debit(amount: float) -> float:
    """Subtract *amount* from the balance if funds are sufficient, persist it,
    and return the new balance.

    Raises ValueError if the current balance is less than *amount*, mirroring
    the COBOL insufficient-funds guard:
        IF FINAL-BALANCE >= AMOUNT
            SUBTRACT AMOUNT FROM FINAL-BALANCE
            CALL 'DataProgram' USING 'WRITE', FINAL-BALANCE
            DISPLAY "Amount debited. New balance: " FINAL-BALANCE
        ELSE
            DISPLAY "Insufficient funds for this debit."
        END-IF
    """
    balance: float = read_balance()
    if balance >= amount:
        balance -= amount
        write_balance(balance)
        return balance
    else:
        raise ValueError("Insufficient funds for this debit.")
