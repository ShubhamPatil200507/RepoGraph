from pathlib import Path


def ensure_sample_repo(target_dir: Path) -> None:
    """Creates a comprehensive sample repository with Python, TypeScript, React, and DB models."""
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Backend models (SQLAlchemy)
    models_dir = target_dir / "backend" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    user_py = """# User model definition
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="customer")
"""
    (models_dir / "user.py").write_text(user_py, encoding="utf-8")

    order_py = """# Order and Item database models
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.models.user import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")

    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
"""
    (models_dir / "order.py").write_text(order_py, encoding="utf-8")

    # 2. Backend services (Business Logic)
    services_dir = target_dir / "backend" / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    order_svc_py = """# Order orchestration and checkout service
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
"""
    (services_dir / "order_service.py").write_text(order_svc_py, encoding="utf-8")

    payment_py = """# Payment gateway integration service
async def process_payment(user_id: int, amount: float) -> bool:
    '''Calls external payment gateway to execute transaction.'''
    if amount <= 0:
        return False
    return True

async def refund_transaction(transaction_id: str) -> bool:
    '''Refunds an existing payment transaction.'''
    return True
"""
    (services_dir / "payment.py").write_text(payment_py, encoding="utf-8")

    inventory_py = """# Inventory tracking service
async def reserve_stock(product_id: int, quantity: int) -> bool:
    '''Reserves warehouse stock for an upcoming order.'''
    return True

async def release_stock(product_id: int, quantity: int) -> bool:
    '''Releases reserved stock back to active inventory.'''
    return True
"""
    (services_dir / "inventory.py").write_text(inventory_py, encoding="utf-8")

    # 3. Backend API routes (Routing layer)
    routes_dir = target_dir / "backend" / "api"
    routes_dir.mkdir(parents=True, exist_ok=True)

    routes_py = """# Order API endpoint handlers
from fastapi import APIRouter, HTTPException, Depends
from backend.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/checkout")
async def checkout_cart(payload: dict, service: OrderService = Depends()):
    '''Checkout user cart items into a confirmed order.'''
    try:
        user_id = payload.get("user_id")
        items = payload.get("items", [])
        order = await service.create_order(user_id, items)
        return {"status": "success", "order_id": order.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}")
async def get_order_details(order_id: int, service: OrderService = Depends()):
    '''Fetch full details for an existing order.'''
    return {"order_id": order_id, "status": "confirmed"}
"""
    (routes_dir / "routes.py").write_text(routes_py, encoding="utf-8")

    # 4. Frontend UI components (React / TypeScript)
    ui_dir = target_dir / "frontend" / "src" / "components"
    ui_dir.mkdir(parents=True, exist_ok=True)

    checkout_tsx = """// Checkout React component
import React, { useState } from 'react';

export const CheckoutView: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    setLoading(true);
    await fetch('/api/orders/checkout', {
      method: 'POST',
      body: JSON.stringify({ items: [] })
    });
    setLoading(false);
  };

  return (
    <div className="checkout-container">
      <h2>Complete Your Purchase</h2>
      <button onClick={handleCheckout} disabled={loading}>
        {loading ? "Processing..." : "Place Order"}
      </button>
    </div>
  );
};
"""
    (ui_dir / "CheckoutView.tsx").write_text(checkout_tsx, encoding="utf-8")

    # 5. Database Schema SQL
    sql_dir = target_dir / "database"
    sql_dir.mkdir(parents=True, exist_ok=True)

    schema_sql = """-- Database DDL schema definition
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(120) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_name VARCHAR(100) NOT NULL,
    quantity INTEGER DEFAULT 1,
    price NUMERIC(10, 2) NOT NULL
);
"""
    (sql_dir / "schema.sql").write_text(schema_sql, encoding="utf-8")

    # 6. Tests
    tests_dir = target_dir / "backend" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    test_py = """# Unit and integration tests for orders
import pytest
from backend.services.order_service import OrderService

def test_order_creation_flow():
    '''Tests complete order calculation and validation logic.'''
    assert True
"""
    (tests_dir / "test_orders.py").write_text(test_py, encoding="utf-8")
