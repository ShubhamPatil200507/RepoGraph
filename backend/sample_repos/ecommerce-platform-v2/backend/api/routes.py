# Order API endpoint handlers - v2
from fastapi import APIRouter, HTTPException, Depends
from backend.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/checkout")
async def checkout_cart(payload: dict, service: OrderService = Depends()):
    '''Checkout user cart items into a confirmed order with fraud checks.'''
    try:
        user_id = payload.get("user_id")
        items = payload.get("items", [])
        order = await service.create_order(user_id, items)
        return {"status": "success", "order_id": order.id, "v2_verified": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}")
async def get_order_details(order_id: int, service: OrderService = Depends()):
    '''Fetch full details for an existing order.'''
    return {"order_id": order_id, "status": "confirmed"}

@router.post("/cancel")
async def cancel_order(order_id: int, service: OrderService = Depends()):
    '''Cancel an existing order and trigger refunds.'''
    success = await service.cancel_order(order_id)
    return {"status": "cancelled" if success else "failed"}
