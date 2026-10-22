import re
from pathlib import Path
from typing import Any, List, Optional, Tuple
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
)

CREATE_TABLE_REGEX = re.compile(
    r"""CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["'`]?([a-zA-Z0-9_]+)["'`]?\.)?["'`]?([a-zA-Z0-9_]+)["'`]?\s*\((.*?)\);""",
    re.IGNORECASE | re.DOTALL
)

PRISMA_MODEL_REGEX = re.compile(
    r"""model\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}""",
    re.MULTILINE
)


class DatabaseSchemaParser(BaseParser):
    SUPPORTED_EXTENSIONS = {".sql", ".prisma"}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

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
        ext = file_path.suffix.lower()
        file_node_id = f"{norm_path}::file"

        file_node = GraphNode(
            id=file_node_id,
            label=Path(norm_path).name,
            type=NodeType.CONFIG.value if ext == ".prisma" else NodeType.FILE.value,
            file_path=norm_path,
            start_line=1,
            end_line=len(content.splitlines()) if content else 1,
            language="sql" if ext == ".sql" else "prisma",
            summary=f"Database schema file: {norm_path}",
            layer=ArchitecturalLayer.DATABASE.value,
            cluster=str(Path(norm_path).parent).replace("\\", "/"),
            evidence_status=EvidenceStatus.VERIFIED.value,
            metadata={"is_db_schema": True}
        )
        nodes.append(file_node)

        if ext == ".sql":
            self._parse_sql(content, norm_path, file_node_id, nodes, edges, er_entities, er_relationships)
        elif ext == ".prisma":
            self._parse_prisma(content, norm_path, file_node_id, nodes, edges, er_entities, er_relationships)

        return nodes, edges, er_entities, er_relationships

    def _parse_sql(
        self,
        content: str,
        norm_path: str,
        file_node_id: str,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        er_entities: List[EREntity],
        er_relationships: List[ERRelationship]
    ) -> None:
        for match in CREATE_TABLE_REGEX.finditer(content):
            schema_prefix, table_name, body = match.groups()
            line_no = content[:match.start()].count("\n") + 1
            node_id = create_node_id(norm_path, table_name)

            table_node = GraphNode(
                id=node_id,
                label=table_name,
                type=NodeType.MODEL.value,
                file_path=norm_path,
                start_line=line_no,
                end_line=line_no + body.count("\n"),
                language="sql",
                summary=f"SQL Table: {table_name}",
                layer=ArchitecturalLayer.DATABASE.value,
                cluster=norm_path,
                evidence_status=EvidenceStatus.VERIFIED.value,
                metadata={"table_name": table_name}
            )
            nodes.append(table_node)
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, node_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=node_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"CREATE TABLE {table_name}",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

            # Parse columns
            attrs: List[ERAttribute] = []
            for col_line in body.split(","):
                col_line = col_line.strip()
                if not col_line or col_line.upper().startswith(("--", "/*", "CONSTRAINT", "INDEX", "KEY")):
                    # Check table level FOREIGN KEY
                    fk_match = re.search(
                        r"""FOREIGN\s+KEY\s*\((?:[`"']?([a-zA-Z0-9_]+)[`"']?)\)\s*REFERENCES\s+[`"']?([a-zA-Z0-9_]+)[`"']?\s*\((?:[`"']?([a-zA-Z0-9_]+)[`"']?)\)""",
                        col_line,
                        re.IGNORECASE
                    )
                    if fk_match:
                        fk_col, target_tbl, target_col = fk_match.groups()
                        er_relationships.append(
                            ERRelationship(
                                id=f"fk::{table_name}->{target_tbl}",
                                source_entity=table_name,
                                target_entity=target_tbl,
                                cardinality="many-to-one",
                                source_file=norm_path,
                                source_line=line_no,
                                evidence_status=EvidenceStatus.VERIFIED.value
                            )
                        )
                    continue

                col_tokens = col_line.split()
                if len(col_tokens) >= 2:
                    col_name = col_tokens[0].replace('"', "").replace("`", "").replace("'", "")
                    col_type = col_tokens[1].upper()
                    is_pk = "PRIMARY KEY" in col_line.upper()
                    is_nullable = "NOT NULL" not in col_line.upper()

                    fk_target = None
                    if "REFERENCES" in col_line.upper():
                        ref_match = re.search(r"""REFERENCES\s+[`"']?([a-zA-Z0-9_]+)[`"']?""", col_line, re.IGNORECASE)
                        if ref_match:
                            fk_target = ref_match.group(1)
                            er_relationships.append(
                                ERRelationship(
                                    id=f"fk::{table_name}->{fk_target}",
                                    source_entity=table_name,
                                    target_entity=fk_target,
                                    cardinality="many-to-one",
                                    source_file=norm_path,
                                    source_line=line_no,
                                    evidence_status=EvidenceStatus.VERIFIED.value
                                )
                            )

                    attrs.append(
                        ERAttribute(
                            name=col_name,
                            data_type=col_type,
                            is_primary_key=is_pk,
                            is_foreign_key=fk_target is not None or col_name.endswith("_id"),
                            foreign_key_target=fk_target,
                            is_nullable=is_nullable
                        )
                    )

            er_entities.append(
                EREntity(
                    id=f"entity::{table_name}",
                    name=table_name,
                    table_name=table_name,
                    file_path=norm_path,
                    start_line=line_no,
                    end_line=line_no + body.count("\n"),
                    attributes=attrs
                )
            )

    def _parse_prisma(
        self,
        content: str,
        norm_path: str,
        file_node_id: str,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        er_entities: List[EREntity],
        er_relationships: List[ERRelationship]
    ) -> None:
        for match in PRISMA_MODEL_REGEX.finditer(content):
            model_name, body = match.groups()
            line_no = content[:match.start()].count("\n") + 1
            node_id = create_node_id(norm_path, model_name)

            model_node = GraphNode(
                id=node_id,
                label=model_name,
                type=NodeType.MODEL.value,
                file_path=norm_path,
                start_line=line_no,
                end_line=line_no + body.count("\n"),
                language="prisma",
                summary=f"Prisma Model: {model_name}",
                layer=ArchitecturalLayer.DATABASE.value,
                cluster=norm_path,
                evidence_status=EvidenceStatus.VERIFIED.value,
                metadata={"is_prisma_model": True}
            )
            nodes.append(model_node)
            edges.append(
                GraphEdge(
                    id=create_edge_id(file_node_id, node_id, EdgeType.CONTAINS.value),
                    source=file_node_id,
                    target=node_id,
                    type=EdgeType.CONTAINS.value,
                    evidence=f"model {model_name}",
                    source_file=norm_path,
                    source_line=line_no,
                    evidence_status=EvidenceStatus.VERIFIED.value
                )
            )

            attrs: List[ERAttribute] = []
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("//") or line.startswith("@@"):
                    continue
                tokens = line.split()
                if len(tokens) >= 2:
                    field_name = tokens[0]
                    field_type = tokens[1]
                    is_pk = "@id" in line
                    is_nullable = "?" in field_type

                    # Relation detection
                    if "@relation" in line:
                        target_match = re.search(r"""references:\s*\[([^\]]+)\]""", line)
                        er_relationships.append(
                            ERRelationship(
                                id=f"rel::{model_name}->{field_type.replace('?', '').replace('[]', '')}",
                                source_entity=model_name,
                                target_entity=field_type.replace("?", "").replace("[]", ""),
                                cardinality="one-to-many" if "[]" in field_type else "many-to-one",
                                source_file=norm_path,
                                source_line=line_no,
                                evidence_status=EvidenceStatus.VERIFIED.value
                            )
                        )

                    attrs.append(
                        ERAttribute(
                            name=field_name,
                            data_type=field_type,
                            is_primary_key=is_pk,
                            is_foreign_key="@relation" in line or field_name.endswith("Id"),
                            is_nullable=is_nullable
                        )
                    )

            er_entities.append(
                EREntity(
                    id=f"entity::{model_name}",
                    name=model_name,
                    table_name=model_name.lower() + "s",
                    file_path=norm_path,
                    start_line=line_no,
                    end_line=line_no + body.count("\n"),
                    attributes=attrs
                )
            )
