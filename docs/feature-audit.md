# RepoGraph — Feature Audit Matrix

**Date:** 2026-10-22  
**System:** RepoGraph (Architecture Explorer)  
**Status Version:** v1.0.0-MVP (All 7 Features Complete & Verified)

---

## 1. Executive Summary

This audit assesses the state of **RepoGraph** against the seven required core capabilities defined in the Master Build Specification. RepoGraph combines static code analysis (Python AST, JS/TS token analyzer, SQL/Prisma ER parser), deterministic graph algorithms (shortest path tracing, reverse-dependency impact analysis, semantic graph diffing), 3D/2D visualization (React Three Fiber, Three.js, `@xyflow/react`), Graphify knowledge graph bidirectional integration, and evidence-grounded Gemma 4 architectural explanations.

All seven core capabilities have been implemented, integrated, and verified against both automated unit/integration test suites and live end-to-end repository analysis.

---

## 2. Feature-by-Feature Status Matrix

| ID | Capability | Status | Verification Summary |
| :--- | :--- | :--- | :--- |
| **F1** | **Custom 3D Architecture Explorer** | **Working & Verified** | Interactive R3F/Three.js universe with layered z-planes (UI: 36, API: 20, Business Logic: 0, Data Access: -20, Database: -36). OrbitControls, node badges, search & layer filters, path tracing highlights, direct & transitive impact highlights (amber/rose glow), large-graph LOD/performance safeguards, legend, and flat 2D fallback (`@xyflow/react`). Verified in 3D canvas and Vitest suite. |
| **F2** | **API & Application Data-Flow Explorer** | **Working & Verified** | Framework-aware route extraction and multi-stage downstream dependency tracing (`GET /api/analyses/{id}/api-routes` and `GET /api/analyses/{id}/api-flow/{route_id}`). Discovers Route -> Middleware/Auth -> Service -> Data Access -> DB Entities with confidence levels and source provenance. Dedicated `ApiFlowView` renders full interactive pipeline. Verified end-to-end. |
| **F3** | **Git Branch & Commit Comparison** | **Working & Verified** | Semantic revision comparison service (`ComparisonService`) and endpoint `POST /api/analyses/{id}/compare`. Compares two Git refs or snapshots, detects added/modified/deleted files, symbols, routes, and schemas, computes downstream ripple impact, and produces an overlay graph. Dedicated `RevisionCompareView` UI. Verified with `ecommerce-platform-v2` fixture. |
| **F4** | **Evidence-Grounded Gemma Architecture Copilot** | **Working & Verified** | Hosted Gemma 4 (`gemma-4-26b-a4b-it`) integration with bounded single-attempt retry (`attempts=1`), prompt-injection shielding, verified line referencing, and high-speed automatic fallback to `gemini-flash-lite-latest`. Enforces strict separation of Confirmed Findings, Hypotheses, and Questions. Verified live with 100% successful response. |
| **F5** | **Database & Application Data-Flow Integration** | **Working & Verified** | SQL DDL and Prisma model parsing into ER entities with PK/FK. Python AST parser detects ORM models, table mappings, and data access operations (`db.add`, `db.commit`, `session.query`). Cross-layer `reads_from` and `writes_to` graph edges link application functions directly to database entities with line numbers. `ERDiagramView` displays interactive entity cards with connected app operations. Verified end-to-end. |
| **F6** | **Change Impact Analysis** | **Working & Verified** | Reverse-dependency BFS engine (`ImpactService`) computes direct and transitive dependents, affected routes, database entities, tests, and layers with a deterministic risk level calculation (`low`, `medium`, `high`, `critical`). Integrates Gemma risk mitigation advice and highlights impacted nodes dynamically across both 3D Universe and 2D Flow canvases. Verified end-to-end. |
| **F7** | **Safe, Reliable Repository-Analysis Pipeline** | **Working & Verified** | Public GitHub URL validation, SSRF protection against private/loopback/link-local/multicast IP ranges via socket DNS resolution, safe zip extraction with entry count, file size, uncompressed total size limits, and path traversal prevention. Multi-stage progress tracking (`in_progress` -> `completed`), analysis deletion (`DELETE`), and preloaded demo repos. Verified end-to-end. |

---

## 3. Detailed Component Verification

### 3.1 Custom 3D Architecture Explorer (F1)
- **Topology & Layering:** Stable z-plane layering by architectural tier (UI at z=36, API at z=20, Business Logic at z=0, Data Access at z=-20, Database at z=-36).
- **Interactive Controls:** OrbitControls with smooth damping, zoom, pan, hover tooltips, selected node halo, camera reset/focus.
- **Visual Filters & Search:** Live text filtering and layer toggling in 3D.
- **Highlights:** Path tracing and direct/transitive change impact cascades rendered with distinct emissive glows (amber for direct, rose for transitive).
- **Performance:** LOD safeguard indicators when node count exceeds thresholds.
- **2D Fallback:** Clean React Flow (`@xyflow/react`) canvas available via one-click toggle.

### 3.2 API & Application Data-Flow Explorer (F2)
- **Route Extraction:** Framework-aware AST detection for FastAPI (`@app.get`, `@router.post`), Flask, and Express handlers.
- **Pipeline Stages:** Traces from HTTP entry point through:
  1. Route Definition
  2. Middleware & Authentication Guards
  3. Service & Controller Logic
  4. Data Access Operations
  5. Database Entities & Tables
  6. External Integrations
- **UI:** Dedicated `ApiFlowView` component with interactive route selection list, visual stage-by-stage node cards, code line references, and provenance badges.

### 3.3 Git Branch & Commit Comparison (F3)
- **Diffing Engine:** Deterministic semantic comparison matching nodes by stable identity (`file_path::symbol_name`).
- **Diff Classification:** Accurately classifies symbols into `added`, `modified`, `removed`, or `unchanged`.
- **High-Level Impact:** Surfaces changed API routes, database schema modifications, affected tests, and total downstream node impact.
- **Overlay Graph:** Merged visual graph with color-coded diff states (green for added, amber for modified, red for removed).
- **UI:** Dedicated `RevisionCompareView` tab with metric cards, collapsible file diff trees, and side-by-side changed symbol details.

### 3.4 Evidence-Grounded Gemma Architecture Copilot (F4)
- **Model Target:** Configured with `gemma-4-26b-a4b-it` via official Google Gen AI SDK (`google-genai`).
- **Resilience:** Bounded HTTP retry (`attempts=1`) prevents hanging on Google preview quotas, with instant automatic fallback to `gemini-flash-lite-latest`.
- **Evidence Grounding:** Structured prompt enforces triple-section output:
  - **Confirmed Findings:** Strictly backed by AST nodes, imports, calls, or schema definitions.
  - **Inferred Hypotheses:** Architectural patterns inferred with stated caveats.
  - **Unresolved Questions:** Acknowledged gaps, dynamic invocations, or unparsed runtime behavior.
- **Prompt Shielding:** Strict injection delimiters preventing user input from overriding architectural analysis guidelines.

### 3.5 Database & Application Data-Flow Integration (F5)
- **DDL & Schema Parsing:** Full support for SQL `CREATE TABLE` statements (data types, primary keys, foreign keys) and Prisma `model` blocks.
- **AST Cross-Layer Edges:** Python parser tracks ORM `__tablename__`, parameter types (`service: OrderService`), model instantiations (`Order(...)`), and database write calls (`db.add()`, `db.commit()`), generating explicit `reads_from` and `writes_to` edges.
- **Interactive ER View:** Dedicated `ERDiagramView` with search, attribute inspect, relationship lines, and "Connected App Operations" showing which services read from or write to each table.

### 3.6 Change Impact Analysis (F6)
- **Reverse-Dependency Traversal:** Breadth-First Search (BFS) following incoming caller and dependency edges up to configurable `max_depth`.
- **Categorization:** Partitions impacted components into direct dependents, transitive dependents, affected API routes, affected database models, and affected unit tests.
- **Risk Rating:** Deterministic formula categorizing risk as `low`, `medium`, `high`, or `critical`.
- **AI Risk Mitigation Advice:** Gemma synthesizes actionable testing and deployment advice based on the affected components.
- **Canvas Integration:** Impacted nodes highlighted in 3D and 2D canvas with amber and rose aura.

### 3.7 Safe, Reliable Ingestion Pipeline (F7)
- **SSRF Prevention:** Host verification (strictly `github.com`), URL validation, and socket DNS resolution blocking loopback (127.0.0.0/8), private (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local, and multicast addresses.
- **Safe Zip Extraction:** Archive streaming enforcing max file counts (5,000 files), max individual file sizes (5 MB), and total uncompressed size limits (100 MB), with strict path traversal rejection (`..`).
- **Static Only:** Pure static parsing without executing untrusted code or invoking shell processes.
- **Lifecycle & Cleanup:** Stage-based progress updates (`in_progress` -> `completed`) and explicit `DELETE /api/analyses/{id}` resource cleanup.

---

## 4. Graphify Sponsor Integration
- **Graph Adapter:** Bidirectional adapter (`backend/app/services/graph_adapter.py`) translating between RepoGraph's normalized schema and Graphify v1 schema format.
- **Endpoint:** `GET /api/analyses/{id}/graphify` returns Graphify-compliant JSON.
- **UI:** One-click "Export Graphify JSON" button in the application header for graph data interchange.
