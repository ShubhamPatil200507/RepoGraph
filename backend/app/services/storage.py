import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.api import AnalysisStageInfo, AnalysisStatusResponse, NodeDetailResponse
from app.models.graph import ERDiagramData, FileItem, GraphEdge, GraphNode, NormalizedGraph

ANALYSIS_STAGES = [
    (1, "Validating repository URL"),
    (2, "Fetching repository metadata"),
    (3, "Downloading source files"),
    (4, "Parsing supported files"),
    (5, "Building dependency graph"),
    (6, "Preparing visualization"),
    (7, "Ready to explore"),
]


class AnalysisRecord:
    def __init__(self, analysis_id: str, repo_info: Dict[str, Any]):
        self.analysis_id = analysis_id
        self.repo_info = repo_info
        self.created_at = time.time()
        self.status = "in_progress"
        self.current_stage_id = 1
        self.progress_message = "Validating repository URL..."
        self.errors: List[str] = []
        self.source_dir: Optional[Path] = None
        self.graph: Optional[NormalizedGraph] = None
        self.er_diagram: Optional[ERDiagramData] = None
        self.file_tree: Optional[FileItem] = None

    def update_stage(self, stage_id: int, message: str) -> None:
        self.current_stage_id = stage_id
        self.progress_message = message

    def mark_completed(
        self,
        graph: NormalizedGraph,
        er_diagram: ERDiagramData,
        file_tree: FileItem,
        source_dir: Path
    ) -> None:
        self.current_stage_id = 7
        self.status = "completed"
        self.progress_message = "Ready to explore"
        self.graph = graph
        self.er_diagram = er_diagram
        self.file_tree = file_tree
        self.source_dir = source_dir

    def mark_failed(self, error_message: str) -> None:
        self.status = "failed"
        self.errors.append(error_message)
        self.progress_message = f"Analysis failed: {error_message}"

    def to_status_response(self) -> AnalysisStatusResponse:
        stages_info = [
            AnalysisStageInfo(
                stage_id=s_id,
                name=s_name,
                completed=(self.status == "completed" or s_id < self.current_stage_id),
                current=(self.status == "in_progress" and s_id == self.current_stage_id)
            )
            for s_id, s_name in ANALYSIS_STAGES
        ]

        return AnalysisStatusResponse(
            analysis_id=self.analysis_id,
            status=self.status,
            current_stage=self.progress_message,
            progress_message=self.progress_message,
            stages=stages_info,
            summary=self.graph.summary if self.graph else None,
            errors=self.errors,
            created_at=self.created_at,
            repository=self.repo_info
        )


class AnalysisStore:
    def __init__(self):
        self._records: Dict[str, AnalysisRecord] = {}

    def create(self, analysis_id: str, repo_info: Dict[str, Any]) -> AnalysisRecord:
        record = AnalysisRecord(analysis_id, repo_info)
        self._records[analysis_id] = record
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        record = self._records.get(analysis_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{analysis_id}' not found."
            )
        return record

    def delete(self, analysis_id: str) -> None:
        record = self._records.pop(analysis_id, None)
        if record and record.source_dir and record.source_dir.exists():
            shutil.rmtree(record.source_dir, ignore_errors=True)

    def get_node_details(self, analysis_id: str, node_id: str) -> NodeDetailResponse:
        record = self.get(analysis_id)
        if not record.graph:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analysis is not completed yet."
            )

        node = next((n for n in record.graph.nodes if n.id == node_id), None)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node '{node_id}' not found in graph."
            )

        # Collect incoming and outgoing edges
        incoming: List[GraphEdge] = []
        outgoing: List[GraphEdge] = []
        neighbor_ids: set = set()

        for edge in record.graph.edges:
            if edge.target == node_id:
                incoming.append(edge)
                neighbor_ids.add(edge.source)
            if edge.source == node_id:
                outgoing.append(edge)
                neighbor_ids.add(edge.target)

        neighbors: List[GraphNode] = [
            n for n in record.graph.nodes if n.id in neighbor_ids
        ]

        # Read actual source snippet from file on disk
        source_code: Optional[str] = None
        if record.source_dir and node.file_path:
            target_file = record.source_dir / node.file_path
            if target_file.exists() and target_file.is_file():
                try:
                    lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
                    start = max(1, node.start_line or 1)
                    end = min(len(lines), node.end_line or (start + 30))
                    # Extract slice with 1-based indexing
                    snippet_lines = lines[start - 1 : end]
                    source_code = "\n".join(snippet_lines)
                except Exception:
                    source_code = None

        # Build safe GitHub link
        github_url = None
        repo_owner = record.repo_info.get("owner")
        repo_name = record.repo_info.get("repo")
        repo_branch = record.repo_info.get("branch") or "main"
        if repo_owner and repo_name and repo_owner != "repograph-demo":
            line_frag = f"#L{node.start_line}" if node.start_line else ""
            if node.end_line and node.end_line > (node.start_line or 1):
                line_frag += f"-L{node.end_line}"
            github_url = f"https://github.com/{repo_owner}/{repo_name}/blob/{repo_branch}/{node.file_path}{line_frag}"

        return NodeDetailResponse(
            node=node,
            source_code=source_code,
            line_start=node.start_line,
            line_end=node.end_line,
            github_url=github_url,
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            neighbor_nodes=neighbors
        )


store = AnalysisStore()
