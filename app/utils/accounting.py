from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from .. import models


def post_journal_entry(
    db: Session,
    entry_date: date,
    reference_type: str,
    reference_id: int,
    account_code: str,
    account_name: str,
    debit: Decimal = Decimal("0.00"),
    credit: Decimal = Decimal("0.00"),
    description: str = ""
):
    entry = models.UniversalJournal(
        entry_date=entry_date,
        reference_type=reference_type,
        reference_id=reference_id,
        account_code=account_code,
        account_name=account_name,
        debit=debit,
        credit=credit,
        description=description,
    )
    db.add(entry)
    return entry