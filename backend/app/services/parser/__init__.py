from pathlib import Path
from typing import Any, List, Optional, Tuple
from app.models.graph import EREntity, ERRelationship, GraphEdge, GraphNode
from app.services.parser.base import BaseParser
from app.services.parser.db_parser import DatabaseSchemaParser
from app.services.parser.js_ts_parser import JavaScriptTypeScriptParser
from app.services.parser.python_parser import PythonASTParser

PARSERS: List[BaseParser] = [
    PythonASTParser(),
    JavaScriptTypeScriptParser(),
    DatabaseSchemaParser(),
]


def parse_repository_file(
    file_path: Path,
    rel_path: str,
    content: str
) -> Tuple[List[GraphNode], List[GraphEdge], List[EREntity], List[ERRelationship]]:
    """Runs the first matching language-aware parser for the file."""
    for parser in PARSERS:
        if parser.supports(file_path):
            return parser.parse(file_path, rel_path, content)

    # Fallback for unrecognized text files: emit basic file node
    from app.models.graph import ArchitecturalLayer, EvidenceStatus, NodeType
    from app.services.parser.base import detect_layer_from_path

    norm_path = rel_path.replace("\\", "/")
    layer = detect_layer_from_path(norm_path)
    file_node = GraphNode(
        id=f"{norm_path}::file",
        label=Path(norm_path).name,
        type=NodeType.FILE.value,
        file_path=norm_path,
        start_line=1,
        end_line=len(content.splitlines()) if content else 1,
        language="plain",
        summary=f"File: {norm_path}",
        layer=layer,
        cluster=str(Path(norm_path).parent).replace("\\", "/"),
        evidence_status=EvidenceStatus.VERIFIED.value,
        metadata={"lines_of_code": len(content.splitlines()) if content else 0}
    )
    return [file_node], [], [], []
