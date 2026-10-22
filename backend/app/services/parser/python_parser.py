import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    ERAttribute,
    EREntity,
    ERRelationship,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NodeType,
)
from app.services.parser.base import (
    BaseParser,
    create_edge_id,
    create_node_id,
    detect_layer_from_path,
)

# Decorator names commonly identifying API endpoints
ROUTE_DECORATOR_IDENTIFIERS = {"get", "post", "put", "delete", "patch", "options", "head", "route", "api_route"}


class PythonASTParser(BaseParser):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".py"

    def parse(
        self,
        file_path: Path,
        rel_path: str,
        content: str
    ) -> Tuple[List[GraphNode], List[GraphEdge], List[EREntity], List[ERRelationship]]:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        er_entities: List[EREntity] = []
        er_relationships: List[ERRelationship] = []

        norm_path = rel_path.replace("\\", "/")
        file_layer = detect_layer_from_path(norm_path)

        # Create module/file root node
        file_node_id = f"{norm_path}::file"
        file_node = GraphNode(
            id=file_node_id,
            label=Path(norm_path).name,
            type=NodeType.FILE.value,
            file_path=norm_path,
            start_line=1,
            end_line=len(content.splitlines()) if content else 1,
            language="python",
            summary=f"Python source file: {norm_path}",
            layer=file_layer,
            cluster=str(Path(norm_path).parent).replace("\\", "/"),
            evidence_status=EvidenceStatus.VERIFIED.value,
            metadata={"lines_of_code": len(content.splitlines()) if content else 0}
        )
        nodes.append(file_node)

        try:
            tree = ast.parse(content, filename=norm_path)
        except SyntaxError as e:
            file_node.metadata["parse_warning"] = f"SyntaxError on line {e.lineno}: {e.msg}"
            return nodes, edges, er_entities, er_relationships
        except Exception as e:
            file_node.metadata["parse_warning"] = f"Parse failed: {str(e)}"
            return nodes, edges, er_entities, er_relationships

        # Extract docstring if present
        docstring = ast.get_docstring(tree)
        if docstring:
            file_node.summary = docstring.strip().split("\n")[0]

        # First pass: map defined symbols in this module for call resolution
        defined_symbols: Set[str] = set()
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_symbols.add(stmt.name)

        # Track imports for cross-node edges
        imported_symbols: Dict[str, str] = {}  # local_alias -> module or target

        for stmt in tree.body:
            # 1. Imports
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    imported_symbols[alias.asname or alias.name] = alias.name
                    edge_id = create_edge_id(file_node_id, f"external::{alias.name}", EdgeType.IMPORTS.value)
                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=file_node_id,
                            target=f"external::{alias.name}",
                            type=EdgeType.IMPORTS.value,
                            evidence=f"import {alias.name}",
                            source_file=norm_path,
                            source_line=stmt.lineno,
                            evidence_status=EvidenceStatus.VERIFIED.value
                        )
                    )

            elif isinstance(stmt, ast.ImportFrom):
                module = stmt.module or ""
                for alias in stmt.names:
                    symbol = alias.asname or alias.name
                    imported_symbols[symbol] = f"{module}.{alias.name}" if module else alias.name
                    target = f"{module}::{alias.name}" if module else alias.name
                    edge_id = create_edge_id(file_node_id, target, EdgeType.IMPORTS.value)
                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=file_node_id,
                            target=target,
                            type=EdgeType.IMPORTS.value,
                            evidence=f"from {module} import {alias.name}",
                            source_file=norm_path,
                            source_line=stmt.lineno,
                            evidence_status=EvidenceStatus.VERIFIED.value
                        )
                    )

            # 2. Classes
            elif isinstance(stmt, ast.ClassDef):
                class_node_id = create_node_id(norm_path, stmt.name)
                is_db_model = False
                base_names = []

                for base in stmt.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)

                # Detect database models (SQLAlchemy, Django, SQLModel, Peewee)
                if any(b in ("Base", "Model", "DeclarativeBase", "SQLModel", "Document", "Entity") for b in base_names):
                    is_db_model = True

                node_type = NodeType.MODEL.value if is_db_model else NodeType.CLASS.value
                layer = ArchitecturalLayer.DATABASE.value if is_db_model else detect_layer_from_path(norm_path, node_type)

                class_summary = ast.get_docstring(stmt) or f"Class {stmt.name}"
                class_node = GraphNode(
                    id=class_node_id,
                    label=stmt.name,
                    type=node_type,
                    file_path=norm_path,
                    start_line=stmt.lineno,
                    end_line=getattr(stmt, "end_lineno", stmt.lineno),
                    language="python",
                    summary=class_summary.strip().split("\n")[0],
                    layer=layer,
                    cluster=norm_path,
                    evidence_status=EvidenceStatus.VERIFIED.value,
                    metadata={"bases": base_names, "is_database_model": is_db_model}
                )
                nodes.append(class_node)

                # Edge: file contains class
                edges.append(
                    GraphEdge(
                        id=create_edge_id(file_node_id, class_node_id, EdgeType.CONTAINS.value),
                        source=file_node_id,
                        target=class_node_id,
                        type=EdgeType.CONTAINS.value,
                        evidence=f"class {stmt.name} defined in {norm_path}",
                        source_file=norm_path,
                        source_line=stmt.lineno,
                        evidence_status=EvidenceStatus.VERIFIED.value
                    )
                )

                # Inheritance edges
                for b_name in base_names:
                    edges.append(
                        GraphEdge(
                            id=create_edge_id(class_node_id, b_name, EdgeType.INHERITS.value),
                            source=class_node_id,
                            target=b_name,
                            type=EdgeType.INHERITS.value,
                            evidence=f"class {stmt.name}({b_name})",
                            source_file=norm_path,
                            source_line=stmt.lineno,
                            evidence_status=EvidenceStatus.VERIFIED.value
                        )
                    )

                # Parse class body: fields, attributes, methods
                er_attrs: List[ERAttribute] = []
                for item in stmt.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = create_node_id(norm_path, f"{stmt.name}.{item.name}")
                        method_node = GraphNode(
                            id=method_id,
                            label=f"{stmt.name}.{item.name}",
                            type=NodeType.METHOD.value,
                            file_path=norm_path,
                            start_line=item.lineno,
                            end_line=getattr(item, "end_lineno", item.lineno),
                            language="python",
                            summary=ast.get_docstring(item) or f"Method {item.name}",
                            layer=layer,
                            cluster=norm_path,
                            evidence_status=EvidenceStatus.VERIFIED.value,
                            metadata={"is_async": isinstance(item, ast.AsyncFunctionDef)}
                        )
                        nodes.append(method_node)

                        edges.append(
                            GraphEdge(
                                id=create_edge_id(class_node_id, method_id, EdgeType.CONTAINS.value),
                                source=class_node_id,
                                target=method_id,
                                type=EdgeType.CONTAINS.value,
                                evidence=f"method {item.name} of {stmt.name}",
                                source_file=norm_path,
                                source_line=item.lineno,
                                evidence_status=EvidenceStatus.VERIFIED.value
                            )
                        )

                        # Check calls inside method
                        self._extract_calls(item, method_id, norm_path, defined_symbols, imported_symbols, edges)

                    # Extract database model attributes (SQLAlchemy Column, Field, ForeignKey)
                    elif is_db_model and isinstance(item, (ast.Assign, ast.AnnAssign)):
                        attr_info = self._parse_db_attribute(item)
                        if attr_info:
                            er_attrs.append(attr_info)
                            if attr_info.is_foreign_key and attr_info.foreign_key_target:
                                # Foreign key relationship
                                target_table = attr_info.foreign_key_target.split(".")[0]
                                er_relationships.append(
                                    ERRelationship(
                                        id=f"fk::{stmt.name}->{target_table}",
                                        source_entity=stmt.name,
                                        target_entity=target_table,
                                        cardinality="many-to-one",
                                        source_file=norm_path,
                                        source_line=item.lineno,
                                        evidence_status=EvidenceStatus.VERIFIED.value
                                    )
                                )

                if is_db_model:
                    er_entities.append(
                        EREntity(
                            id=f"entity::{stmt.name}",
                            name=stmt.name,
                            table_name=stmt.name.lower() + "s",
                            file_path=norm_path,
                            start_line=stmt.lineno,
                            end_line=getattr(stmt, "end_lineno", stmt.lineno),
                            attributes=er_attrs
                        )
                    )

            # 3. Top-level functions & API routes
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node_id = create_node_id(norm_path, stmt.name)
                is_route, route_info = self._check_route_decorator(stmt)

                is_test = stmt.name.startswith("test_")
                if is_route:
                    node_type = NodeType.ROUTE.value
                    layer = ArchitecturalLayer.API.value
                elif is_test:
                    node_type = NodeType.TEST.value
                    layer = ArchitecturalLayer.TESTS.value
                else:
                    node_type = NodeType.FUNCTION.value
                    layer = detect_layer_from_path(norm_path, node_type)

                func_summary = ast.get_docstring(stmt) or f"Function {stmt.name}"
                meta = {
                    "is_async": isinstance(stmt, ast.AsyncFunctionDef),
                    "is_route": is_route,
                }
                if is_route:
                    meta.update(route_info)

                func_node = GraphNode(
                    id=func_node_id,
                    label=stmt.name,
                    type=node_type,
                    file_path=norm_path,
                    start_line=stmt.lineno,
                    end_line=getattr(stmt, "end_lineno", stmt.lineno),
                    language="python",
                    summary=func_summary.strip().split("\n")[0],
                    layer=layer,
                    cluster=norm_path,
                    evidence_status=EvidenceStatus.VERIFIED.value,
                    metadata=meta
                )
                nodes.append(func_node)

                edges.append(
                    GraphEdge(
                        id=create_edge_id(file_node_id, func_node_id, EdgeType.CONTAINS.value),
                        source=file_node_id,
                        target=func_node_id,
                        type=EdgeType.CONTAINS.value,
                        evidence=f"function {stmt.name} defined in {norm_path}",
                        source_file=norm_path,
                        source_line=stmt.lineno,
                        evidence_status=EvidenceStatus.VERIFIED.value
                    )
                )

                # Calls inside function
                self._extract_calls(stmt, func_node_id, norm_path, defined_symbols, imported_symbols, edges)

        return nodes, edges, er_entities, er_relationships

    def _check_route_decorator(self, func_def: Any) -> Tuple[bool, Dict[str, Any]]:
        """Checks if a function is decorated with a route decorator (e.g., @app.get('/users'))."""
        for dec in func_def.decorator_list:
            if isinstance(dec, ast.Call):
                func = dec.func
                method = ""
                if isinstance(func, ast.Attribute) and func.attr.lower() in ROUTE_DECORATOR_IDENTIFIERS:
                    method = func.attr.upper()
                elif isinstance(func, ast.Name) and func.id.lower() in ROUTE_DECORATOR_IDENTIFIERS:
                    method = func.id.upper()

                if method:
                    path = ""
                    if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                        path = dec.args[0].value
                    return True, {"http_method": method, "route_path": path}
            elif isinstance(dec, ast.Attribute) and dec.attr.lower() in ROUTE_DECORATOR_IDENTIFIERS:
                return True, {"http_method": dec.attr.upper(), "route_path": ""}
        return False, {}

    def _parse_db_attribute(self, item: Any) -> Optional[ERAttribute]:
        """Extracts column name, type, and primary/foreign key flags from AST assignment."""
        try:
            target_name = ""
            if isinstance(item, ast.Assign) and item.targets and isinstance(item.targets[0], ast.Name):
                target_name = item.targets[0].id
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                target_name = item.target.id

            if not target_name or target_name.startswith("_"):
                return None

            source_repr = ast.unparse(item.value) if hasattr(ast, "unparse") else ""
            is_pk = "primary_key=True" in source_repr or target_name.lower() == "id"
            is_fk = "ForeignKey(" in source_repr or target_name.endswith("_id")
            fk_target = None

            if "ForeignKey(" in source_repr:
                # Extract target table / column: ForeignKey('table.col')
                import re
                fk_match = re.search(r"ForeignKey\(['\"]([^'\"]+)['\"]", source_repr)
                if fk_match:
                    fk_target = fk_match.group(1)

            # Heuristic data type
            data_type = "String"
            if any(t in source_repr for t in ("Integer", "int", "BigInteger")):
                data_type = "Integer"
            elif any(t in source_repr for t in ("Boolean", "bool")):
                data_type = "Boolean"
            elif any(t in source_repr for t in ("DateTime", "Date")):
                data_type = "DateTime"
            elif any(t in source_repr for t in ("Float", "Numeric")):
                data_type = "Float"
            elif any(t in source_repr for t in ("JSON", "dict")):
                data_type = "JSON"

            return ERAttribute(
                name=target_name,
                data_type=data_type,
                is_primary_key=is_pk,
                is_foreign_key=is_fk,
                foreign_key_target=fk_target,
                is_nullable="nullable=False" not in source_repr
            )
        except Exception:
            return None

    def _extract_calls(
        self,
        func_node: Any,
        caller_id: str,
        norm_path: str,
        defined_symbols: Set[str],
        imported_symbols: Dict[str, str],
        edges: List[GraphEdge]
    ) -> None:
        """Walks statements in a function to detect calls to local or imported symbols."""
        for subnode in ast.walk(func_node):
            if isinstance(subnode, ast.Call):
                called_name = None
                if isinstance(subnode.func, ast.Name):
                    called_name = subnode.func.id
                elif isinstance(subnode.func, ast.Attribute) and isinstance(subnode.func.value, ast.Name):
                    called_name = f"{subnode.func.value.id}.{subnode.func.attr}"

                if not called_name or called_name in ("print", "len", "range", "isinstance", "getattr", "setattr"):
                    continue

                # Local symbol call
                if called_name in defined_symbols:
                    target_id = create_node_id(norm_path, called_name)
                    edge_id = create_edge_id(caller_id, target_id, EdgeType.CALLS.value)
                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=caller_id,
                            target=target_id,
                            type=EdgeType.CALLS.value,
                            evidence=f"call {called_name}() at line {subnode.lineno}",
                            source_file=norm_path,
                            source_line=subnode.lineno,
                            evidence_status=EvidenceStatus.VERIFIED.value
                        )
                    )
                # Imported symbol call
                elif called_name in imported_symbols:
                    target_repr = imported_symbols[called_name]
                    edge_id = create_edge_id(caller_id, target_repr, EdgeType.CALLS.value)
                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=caller_id,
                            target=target_repr,
                            type=EdgeType.CALLS.value,
                            evidence=f"call {called_name}() [imported: {target_repr}]",
                            source_file=norm_path,
                            source_line=subnode.lineno,
                            evidence_status=EvidenceStatus.VERIFIED.value
                        )
                    )
