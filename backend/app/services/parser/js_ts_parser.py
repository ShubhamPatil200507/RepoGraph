import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
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

# Regular expressions for JS/TS/TSX syntax detection
IMPORT_REGEX = re.compile(
    r"""import\s+(?:(?:\*\s+as\s+([a-zA-Z0-9_$]+))|(?:{([^}]+)})|([a-zA-Z0-9_$]+))?\s*(?:from\s*)?['"]([^'"]+)['"]""",
    re.MULTILINE
)
REQUIRE_REGEX = re.compile(
    r"""(?:const|let|var)\s+(?:{([^}]+)}|([a-zA-Z0-9_$]+))\s*=\s*require\(['"]([^'"]+)['"]\)""",
    re.MULTILINE
)
CLASS_REGEX = re.compile(
    r"""(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?""",
    re.MULTILINE
)
FUNCTION_REGEX = re.compile(
    r"""(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(""",
    re.MULTILINE
)
ARROW_FUNC_REGEX = re.compile(
    r"""(?:export\s+)?(?:const|let)\s+([a-zA-Z0-9_$]+)(?:\s*:\s*[^=]+)?\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>""",
    re.MULTILINE
)
EXPRESS_ROUTE_REGEX = re.compile(
    r"""(?:app|router)\.(get|post|put|delete|patch|options|use)\s*\(\s*['"]([^'"]+)['"]""",
    re.IGNORECASE
)
NEXT_ROUTE_REGEX = re.compile(
    r"""export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD)\s*\(""",
    re.MULTILINE
)


class JavaScriptTypeScriptParser(BaseParser):
    SUPPORTED_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(
        self,
        file_path: Path,
        rel_path: str,
        content: str
    ) -> Tuple[List[GraphNode], List[GraphEdge], List[Any], List[Any]]:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        er_entities: List[Any] = []
        er_relationships: List[Any] = []

        norm_path = rel_path.replace("\\", "/")
        ext = file_path.suffix.lower()
        language = "typescript" if ext in (".ts", ".tsx") else "javascript"
        lines = content.splitlines() if content else []
        total_lines = len(lines)

        file_layer = detect_layer_from_path(norm_path)
        file_node_id = f"{norm_path}::file"

        file_node = GraphNode(
            id=file_node_id,
            label=Path(norm_path).name,
            type=NodeType.FILE.value,
            file_path=norm_path,
            start_line=1,
            end_line=total_lines if total_lines > 0 else 1,
            language=language,
            summary=f"{language.capitalize()} module: {norm_path}",
            layer=file_layer,
            cluster=str(Path(norm_path).parent).replace("\\", "/"),
            evidence_status=EvidenceStatus.VERIFIED.value,
            metadata={"lines_of_code": total_lines, "is_tsx_jsx": ext in (".tsx", ".jsx")}
        )
        nodes.append(file_node)

        # 1. Imports
        for match in IMPORT_REGEX.finditer(content):
            star_alias, named_imports, default_import, import_module = match.groups()
            line_no = content[:match.start()].count("\n") + 1
            target_repr = f"import::{import_module}"

            edge_id = create_edge_id(file_node_id, target_repr, EdgeType.IMPORTS.value)
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=file_node_id,
                    target=target_repr,
                    type=EdgeType.IMPORTS.value,
                    evidence=match.group(0).strip(),
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

        for match in REQUIRE_REGEX.finditer(content):
            named, default_var, req_module = match.groups()
            line_no = content[:match.start()].count("\n") + 1
            target_repr = f"import::{req_module}"
            edge_id = create_edge_id(file_node_id, target_repr, EdgeType.IMPORTS.value)
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=file_node_id,
                    target=target_repr,
                    type=EdgeType.IMPORTS.value,
                    evidence=match.group(0).strip(),
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

        # 2. Next.js App Router route handlers
        is_route_file = "app/api" in norm_path or "pages/api" in norm_path or "/routes/" in norm_path
        for match in NEXT_ROUTE_REGEX.finditer(content):
            http_method = match.group(1).upper()
            line_no = content[:match.start()].count("\n") + 1
            route_id = create_node_id(norm_path, http_method)

            route_node = GraphNode(
                id=route_id,
                label=f"{http_method} {Path(norm_path).stem}",
                type=NodeType.ROUTE.value,
                file_path=norm_path,
                start_line=line_no,
                end_line=line_no + 10,
                language=language,
                summary=f"Next.js {http_method} API route handler",
                layer=ArchitecturalLayer.API.value,
                cluster=norm_path,
                evidence_status=EvidenceStatus.VERIFIED.value,
                metadata={"http_method": http_method, "is_route": True}
            )
            nodes.append(route_node)
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, route_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=route_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"export {http_method} handler",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

        # 3. Express routes
        for match in EXPRESS_ROUTE_REGEX.finditer(content):
            http_method = match.group(1).upper()
            route_path = match.group(2)
            line_no = content[:match.start()].count("\n") + 1
            route_id = create_node_id(norm_path, f"{http_method}_{route_path}")

            route_node = GraphNode(
                id=route_id,
                label=f"{http_method} {route_path}",
                type=NodeType.ROUTE.value,
                file_path=norm_path,
                start_line=line_no,
                end_line=line_no + 5,
                language=language,
                summary=f"Express route: {http_method} {route_path}",
                layer=ArchitecturalLayer.API.value,
                cluster=norm_path,
                evidence_status=EvidenceStatus.VERIFIED.value,
                metadata={"http_method": http_method, "route_path": route_path, "is_route": True}
            )
            nodes.append(route_node)
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, route_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=route_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"route {http_method} '{route_path}'",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

        # 4. Classes
        for match in CLASS_REGEX.finditer(content):
            class_name, base_class = match.groups()
            line_no = content[:match.start()].count("\n") + 1
            class_id = create_node_id(norm_path, class_name)

            class_node = GraphNode(
                id=class_id,
                label=class_name,
                type=NodeType.CLASS.value,
                file_path=norm_path,
                start_line=line_no,
                end_line=line_no + 20,
                language=language,
                summary=f"Class {class_name}",
                layer=file_layer,
                cluster=norm_path,
                evidence_status=EvidenceStatus.VERIFIED.value,
                metadata={"extends": base_class or None}
            )
            nodes.append(class_node)
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, class_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=class_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"class {class_name}",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

            if base_class:
                edges.append(
                    GraphEdge(
                        id=create_edge_id(class_id, base_class, EdgeType.INHERITS.value),
                        source=class_id,
                        target=base_class,
                        type=EdgeType.INHERITS.value,
                        evidence=f"class {class_name} extends {base_class}",
                        source_file=norm_path,
                        source_line=line_no,
                        evidence_status=EvidenceStatus.VERIFIED.value
                    )
                )

        # 5. Functions & React Components
        seen_functions: Set[str] = set()

        def add_function(name: str, start_pos: int):
            if name in seen_functions or name in ("require", "describe", "it", "test", "beforeEach", "afterEach"):
                return
            seen_functions.add(name)

            line_no = content[:start_pos].count("\n") + 1
            # Check if likely React Component: starts with uppercase letter and in .tsx/.jsx or uses JSX
            is_react_comp = (
                (name[0].isupper() if name else False)
                and (ext in (".tsx", ".jsx") or "return <" in content[start_pos:start_pos + 400])
            )

            node_type = NodeType.COMPONENT.value if is_react_comp else NodeType.FUNCTION.value
            layer = ArchitecturalLayer.UI.value if is_react_comp else detect_layer_from_path(norm_path, node_type)

            func_id = create_node_id(norm_path, name)
            nodes.append(
                GraphNode(
                    id=func_id,
                    label=name,
                    type=node_type,
                    file_path=norm_path,
                    start_line=line_no,
                    end_line=line_no + 15,
                    language=language,
                    summary=f"React Component: <{name} />" if is_react_comp else f"Function {name}",
                    layer=layer,
                    cluster=norm_path,
                    evidence_status=EvidenceStatus.VERIFIED.value,
                    metadata={"is_component": is_react_comp}
                )
            )
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, func_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=func_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"{'component' if is_react_comp else 'function'} {name}",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

        for match in FUNCTION_REGEX.finditer(content):
            add_function(match.group(1), match.start())

        for match in ARROW_FUNC_REGEX.finditer(content):
            add_function(match.group(1), match.start())

        return nodes, edges, er_entities, er_relationships
