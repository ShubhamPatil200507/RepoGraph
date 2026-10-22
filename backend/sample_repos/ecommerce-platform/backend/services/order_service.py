# Order orchestration and checkout service
from backend.models.order import Order, OrderItem
from backend.services.payment import process_payment
from backend.services.inventory import reserve_stock

class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    async def create_order(self, user_id: int, items: list) -> Order:
        '''Creates and validates an order, reserving inventory and charging payment.'''
        total = sum(i["price"] * i["qty"] for i in items)
        
        # 1. Reserve stock
        for item in items:
            await reserve_stock(item["product_id"], item["qty"])

        # 2. Process payment
        payment_status = await process_payment(user_id, total)
        if not payment_status:
            raise ValueError("Payment failed")

        # 3. Persist order
        order = Order(user_id=user_id, total_amount=total, status="confirmed")
        self.db.add(order)
        self.db.commit()
        return order
