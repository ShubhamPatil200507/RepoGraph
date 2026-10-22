import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.core.config import settings
from app.core.security import is_path_safe_for_inspection
from app.models.api import (
    AIStatusResponse,
    AnalyzeRepoRequest,
    AnalyzeRepoResponse,
    AnalysisStatusResponse,
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
    ImpactRequest,
    ImpactResponse,
    NodeDetailResponse,
    TraceRequest,
    TraceResponse,
)
from app.models.graph import ERDiagramData, FileItem, NormalizedGraph
from app.services.ai_service import AIService
from app.services.fetcher import GitHubFetcher
from app.services.graph_builder import GraphBuilder
from app.services.impact_service import ImpactService
from app.services.parser import parse_repository_file
from app.services.storage import store
from app.services.trace_service import TraceService

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


@router.get("/ai/status", response_model=AIStatusResponse)
async def ai_status():
    info = AIService.get_status_info()
    return AIStatusResponse(
        available=info["available"],
        configured_model=info["configured_model"],
        preferred_model=info["preferred_model"],
        message=info["message"]
    )


async def execute_repository_analysis(analysis_id: str, repository_url: str, branch: str = ""):
    record = store.get(analysis_id)
    try:
        # Stage 2 & 3: Metadata & Download
        record.update_stage(2, "Fetching repository metadata...")
        await asyncio.sleep(0.1)

        record.update_stage(3, "Downloading source archive safely...")
        extracted_dir, repo_meta = await GitHubFetcher.fetch_and_extract_repository(
            repository_url, branch
        )
        record.repo_info = repo_meta

        # Stage 4: Parse files
        record.update_stage(4, "Parsing source code with syntax-aware analyzers...")
        graph_builder = GraphBuilder()

        all_files = []
        for root, dirs, files in os.walk(extracted_dir):
            rel_dir = os.path.relpath(root, extracted_dir)
            if not is_path_safe_for_inspection(rel_dir):
                dirs[:] = []
                continue

            for fname in files:
                full_file = Path(root) / fname
                rel_file = (Path(rel_dir) / fname if rel_dir != "." else Path(fname)).as_posix()

                if not is_path_safe_for_inspection(rel_file):
                    continue

                all_files.append((full_file, rel_file))

        total_files = len(all_files)
        parsed_count = 0

        for full_p, rel_p in all_files:
            try:
                stat = full_p.stat()
                if stat.st_size > settings.MAX_SINGLE_FILE_SIZE_BYTES:
                    continue

                content = full_p.read_text(encoding="utf-8", errors="replace")
                nodes, edges, er_ents, er_rels = parse_repository_file(full_p, rel_p, content)

                ext = full_p.suffix.lower()
                lang = "python" if ext == ".py" else ("typescript" if ext in (".ts", ".tsx") else ("javascript" if ext in (".js", ".jsx") else "other"))

                graph_builder.add_parsed_results(
                    nodes, edges, er_ents, er_rels, rel_p, stat.st_size, lang
                )
                parsed_count += 1
            except Exception as e:
                graph_builder.warnings.append(f"Failed parsing {rel_p}: {str(e)}")

        # Stage 5: Build normalized graph and layouts
        record.update_stage(5, "Building normalized dependency graph and spatial coordinates...")
        norm_graph, er_data, file_tree = graph_builder.build_normalized_graph()

        # Stage 6: Preparing visualization
        record.update_stage(6, "Preparing 3D universe and 2D diagram views...")
        await asyncio.sleep(0.1)

        # Stage 7: Mark completed
        record.mark_completed(norm_graph, er_data, file_tree, extracted_dir)

    except Exception as e:
        record.mark_failed(str(e))


@router.post("/repositories/analyze", response_model=AnalyzeRepoResponse)
async def analyze_repository(request: AnalyzeRepoRequest, background_tasks: BackgroundTasks):
    analysis_id = str(uuid.uuid4())
    repo_info = {
        "url": request.repository_url,
        "branch": request.branch or "",
    }
    store.create(analysis_id, repo_info)

    # Launch processing
    background_tasks.add_task(
        execute_repository_analysis,
        analysis_id,
        request.repository_url,
        request.branch or ""
    )

    return AnalyzeRepoResponse(
        analysis_id=analysis_id,
        status="in_progress",
        stage="Validating repository URL",
        message="Analysis started.",
        repository=repo_info
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    record = store.get(analysis_id)
    return record.to_status_response()


@router.get("/analyses/{analysis_id}/graph", response_model=NormalizedGraph)
async def get_analysis_graph(analysis_id: str):
    record = store.get(analysis_id)
    if not record.graph:
        raise HTTPException(status_code=400, detail="Graph not ready yet.")
    return record.graph


@router.get("/analyses/{analysis_id}/graphify")
async def get_analysis_graphify_export(analysis_id: str):
    """Exports the codebase knowledge graph in Graphify-Labs standard schema (graph.json)."""
    from app.services.graphify_exporter import GraphifyExporter
    record = store.get(analysis_id)
    if not record.graph:
        raise HTTPException(status_code=400, detail="Graph not ready yet.")
    return GraphifyExporter.export_graphify_json(record.graph)


@router.get("/analyses/{analysis_id}/files", response_model=FileItem)
async def get_analysis_files(analysis_id: str):
    record = store.get(analysis_id)
    if not record.file_tree:
        raise HTTPException(status_code=400, detail="File inventory not ready yet.")
    return record.file_tree


@router.get("/analyses/{analysis_id}/er-diagram", response_model=ERDiagramData)
async def get_analysis_er_diagram(analysis_id: str):
    record = store.get(analysis_id)
    if not record.er_diagram:
        raise HTTPException(status_code=400, detail="ER diagram not ready yet.")
    return record.er_diagram


@router.get("/analyses/{analysis_id}/nodes/{node_id:path}", response_model=NodeDetailResponse)
async def get_node_details(analysis_id: str, node_id: str):
    return store.get_node_details(analysis_id, node_id)


@router.post("/analyses/{analysis_id}/explain", response_model=ExplainResponse)
async def explain_node(analysis_id: str, req: ExplainRequest):
    record = store.get(analysis_id)
    if not record.graph:
        raise HTTPException(status_code=400, detail="Analysis is not completed.")

    node_detail = store.get_node_details(analysis_id, req.node_id)
    secondary_node = None
    if req.secondary_node_id:
        secondary_node = next((n for n in record.graph.nodes if n.id == req.secondary_node_id), None)

    return await AIService.explain_component(
        node=node_detail.node,
        source_snippet=node_detail.source_code,
        incoming_edges=node_detail.incoming_edges,
        outgoing_edges=node_detail.outgoing_edges,
        question=req.question,
        secondary_node=secondary_node
    )


@router.post("/analyses/{analysis_id}/trace", response_model=TraceResponse)
async def trace_path(analysis_id: str, req: TraceRequest):
    record = store.get(analysis_id)
    if not record.graph:
        raise HTTPException(status_code=400, detail="Analysis is not completed.")

    trace_result = TraceService.trace_feature_path(
        record.graph, req.start_node_id, req.target_node_id, req.max_depth
    )

    if trace_result.path_found and AIService.is_ai_available():
        explanation = await AIService.explain_trace_path(trace_result)
        trace_result.explanation = explanation

    return trace_result


@router.post("/analyses/{analysis_id}/impact", response_model=ImpactResponse)
async def analyze_impact(analysis_id: str, req: ImpactRequest):
    record = store.get(analysis_id)
    if not record.graph:
        raise HTTPException(status_code=400, detail="Analysis is not completed.")

    impact_result = ImpactService.analyze_change_impact(
        record.graph, req.node_id, req.max_depth
    )

    if AIService.is_ai_available():
        explanation = await AIService.explain_impact(impact_result)
        impact_result.gemma_explanation = explanation

    return impact_result


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str):
    store.delete(analysis_id)
    return {"message": f"Analysis '{analysis_id}' and cached files deleted successfully."}
