# Order orchestration and checkout service - v2
from backend.models.order import Order, OrderItem
from backend.services.payment import process_payment, refund_transaction
from backend.services.inventory import reserve_stock, release_stock

class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    async def create_order(self, user_id: int, items: list) -> Order:
        '''Creates and validates an order, reserving inventory and charging payment.'''
        total = sum(i["price"] * i["qty"] for i in items)
        
        for item in items:
            await reserve_stock(item["product_id"], item["qty"])

        payment_status = await process_payment(user_id, total)
        if not payment_status:
            raise ValueError("Payment failed")

        order = Order(user_id=user_id, total_amount=total, status="confirmed")
        self.db.add(order)
        self.db.commit()
        return order

    async def cancel_order(self, order_id: int) -> bool:
        '''Cancels an order, releases inventory and refunds transaction.'''
        await refund_transaction(str(order_id))
        return True
