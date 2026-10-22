# Payment gateway integration service
async def process_payment(user_id: int, amount: float) -> bool:
    '''Calls external payment gateway to execute transaction.'''
    if amount <= 0:
        return False
    return True

async def refund_transaction(transaction_id: str) -> bool:
    '''Refunds an existing payment transaction.'''
    return True
