from pathlib import Path
from app.models.graph import ArchitecturalLayer, EdgeType, NodeType
from app.services.parser.db_parser import DatabaseSchemaParser
from app.services.parser.js_ts_parser import JavaScriptTypeScriptParser
from app.services.parser.python_parser import PythonASTParser


def test_python_ast_parser_classes_routes_and_models():
    parser = PythonASTParser()
    code = """
from fastapi import APIRouter
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)

router = APIRouter()

@router.get("/users")
async def list_users():
    return []
"""
    nodes, edges, er_entities, er_relationships = parser.parse(
        Path("app/api/users.py"), "app/api/users.py", code
    )

    # Verify nodes
    node_labels = {n.label: n for n in nodes}
    assert "UserModel" in node_labels
    assert node_labels["UserModel"].type == NodeType.MODEL.value
    assert node_labels["UserModel"].layer == ArchitecturalLayer.DATABASE.value

    assert "list_users" in node_labels
    assert node_labels["list_users"].type == NodeType.ROUTE.value
    assert node_labels["list_users"].layer == ArchitecturalLayer.API.value
    assert node_labels["list_users"].metadata["http_method"] == "GET"

    # Verify ER entity
    assert len(er_entities) == 1
    assert er_entities[0].name == "UserModel"
    attr_names = [a.name for a in er_entities[0].attributes]
    assert "id" in attr_names
    assert "username" in attr_names


def test_js_ts_parser_components_and_routes():
    parser = JavaScriptTypeScriptParser()
    code = """
import React, { useState } from 'react';
import { fetchOrders } from '../api/client';

export const OrderDashboard: React.FC = () => {
  const [orders, setOrders] = useState([]);
  return <div><h1>Orders</h1></div>;
};

export async function GET(request) {
  return new Response("OK");
}
"""
    nodes, edges, er_entities, _ = parser.parse(
        Path("src/components/OrderDashboard.tsx"), "src/components/OrderDashboard.tsx", code
    )

    node_labels = {n.label: n for n in nodes}
    assert "OrderDashboard" in node_labels
    assert node_labels["OrderDashboard"].type == NodeType.COMPONENT.value
    assert node_labels["OrderDashboard"].layer == ArchitecturalLayer.UI.value

    # Check import edge
    import_targets = [e.target for e in edges if e.type == EdgeType.IMPORTS.value]
    assert any("client" in t for t in import_targets)


def test_sql_ddl_parser():
    parser = DatabaseSchemaParser()
    sql = """
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    total NUMERIC(10, 2)
);
"""
    nodes, edges, er_entities, er_relationships = parser.parse(
        Path("db/schema.sql"), "db/schema.sql", sql
    )

    assert len(er_entities) == 2
    ent_names = {e.name for e in er_entities}
    assert "customers" in ent_names
    assert "orders" in ent_names

    # Check relation
    assert len(er_relationships) >= 1
    rel = er_relationships[0]
    assert rel.source_entity == "orders"
    assert rel.target_entity == "customers"
