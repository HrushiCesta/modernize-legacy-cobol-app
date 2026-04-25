# Converted from data.cob (COBOL DataProgram)
#
# Original COBOL working-storage:
#   01  STORAGE-BALANCE    PIC 9(6)V99 VALUE 1000.00.
#
# The two-branch PASSED-OPERATION dispatch ('READ' / 'WRITE') is replaced by
# two explicit Python functions — read_balance() and write_balance() — which
# are cleaner and avoid string-based dispatch.
#
# PIC 9(6)V99  →  float  (6 integer digits, 2 implied decimal places)
# GOBACK       →  return

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_balance: float = 1000.00


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def read_balance() -> float:
    """Return the current account balance.

    Mirrors the COBOL branch:
        IF OPERATION-TYPE = 'READ'
            MOVE STORAGE-BALANCE TO BALANCE
    """
    return _balance


def write_balance(new_balance: float) -> None:
    """Overwrite the stored balance with *new_balance*.

    Mirrors the COBOL branch:
        IF OPERATION-TYPE = 'WRITE'
            MOVE BALANCE TO STORAGE-BALANCE
    """
    global _balance
    _balance = new_balance
