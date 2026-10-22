# RepoGraph

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**See how your code works. Explore how everything connects.**

RepoGraph is an interactive software architecture explorer that transforms GitHub repositories into source-backed, three-dimensional maps of modules, entities, dependencies, and execution paths. Developers can explore how a project works, inspect real code relationships, and use hosted Gemma to explain complex connections.

---

## Core Product Principle

> **Deterministic code analysis discovers what exists.  
> Graph algorithms determine how components connect.  
> Gemma explains the evidence.  
> The visualization makes the architecture understandable.**

RepoGraph never uses language models as a substitute for syntax-aware code parsing or graph construction. Deterministic AST parsers identify verified symbols, routes, models, and dependencies. Graph algorithms determine execution paths and downstream change impact. Hosted Gemma is used exclusively to explain verified findings grounded strictly in repository evidence.

---

## Open-Weight AI Model Verification & Terms

RepoGraph integrates Google DeepMind's **Gemma** open-weights model family for architectural reasoning and evidence-grounded code explanations:

- **Configured Model Identifier:** `gemma-4-26b-a4b-it` (Gemma 4 26B instruction-tuned mixture-of-experts model).
- **Inference Mode:** Hosted inference through Google's official Gen AI Python SDK (`google-genai`).
- **Open-Weights Terms & License:** Gemma models are governed by the official [Gemma Open Model Terms of Use](https://ai.google.dev/gemma/terms).
- **Official Model Cards & Documentation:**
  - Google DeepMind Gemma Hub: [ai.google.dev/gemma](https://ai.google.dev/gemma)
  - Google Gemma Terms of Use: [ai.google.dev/gemma/terms](https://ai.google.dev/gemma/terms)
  - Hugging Face Model Card: [huggingface.co/google/gemma-2-27b-it](https://huggingface.co/google/gemma-2-27b-it)
  - Kaggle Gemma Models: [kaggle.com/models/google/gemma-2](https://www.kaggle.com/models/google/gemma-2)
- **Grounded Verification Boundary:** The Gemma copilot is fed *strictly deterministic AST evidence*: node identifiers, line numbers, and verified incoming/outgoing edges. It outputs findings separated into Confirmed Findings, Hypotheses, and Questions.
- **Resilient Fallback:** Single-attempt retry (`attempts=1`) prevents hanging on Google preview endpoint quotas, activating instant automatic fallback to `gemini-flash-lite-latest`, or 100% offline non-AI fallback when unconfigured.

---

## The Seven Core Capabilities

### 1. Custom 3D Architecture Explorer
- **Spatial Topology & Layering:** Stratified by architectural tiers on distinct Z-planes (UI at $z=36$, API at $z=20$, Business Logic at $z=0$, Data Access at $z=-20$, Database at $z=-36$).
- **Deterministic Layout:** Stable, reproducible spatial positioning across repeated analyses.
- **Interactive Controls:** OrbitControls with smooth damping, zoom, pan, camera reset, and automatic focus-fly-to on selected components.
- **Dynamic Highlights:** Selecting any node highlights immediate neighbors and active connection rays while gently dimming unrelated clusters. Traced execution paths and change-impact cascades glow with distinct emissive auras (amber for direct dependents, rose for transitive dependents).
- **LOD Performance Safeguards:** Automatic level-of-detail indicators when graphs exceed threshold node counts.
- **Complementary 2D Flow View:** Powered by `@xyflow/react` for developers who prefer flat, structured diagrams, with complete bidirectional state synchronization.

### 2. API & Application Data-Flow Explorer
- **Framework-Aware Route Discovery:** Automatically detects HTTP endpoints across FastAPI (`@app.get`, `@router.post`), Flask, and Express handlers.
- **Multi-Stage Processing Pipeline:** Traces from HTTP entry point through:
  1. Route Definition
  2. Middleware & Authentication Guards
  3. Service & Controller Logic
  4. Data Access Operations
  5. Database Entities & Tables
  6. External Integrations
- **Dedicated View (`ApiFlowView`):** Interactive endpoint selector, stage-by-stage node cards, line-number provenance, and verified vs. inferred confidence indicators.

### 3. Git Branch & Commit Comparison
- **Semantic Codebase Diffing:** `ComparisonService` matches symbols by stable identity (`file_path::symbol_name`) across Git branches, tags, or commits.
- **Change Categorization:** Identifies added, modified, deleted, and unchanged symbols.
- **Architectural Ripple Summary:** Surfaces modified API endpoints, database schema shifts, affected unit tests, and total downstream graph ripple.
- **Overlay Graph & Dedicated View (`RevisionCompareView`):** Side-by-side metric cards, collapsible file diff tree, and an overlay graph highlighting new components in green, modified in amber, and deleted in red.

### 4. Evidence-Grounded Gemma Architecture Copilot
- **Hosted Gemma 4 Integration:** Configured with `gemma-4-26b-a4b-it` via official Google Gen AI SDK (`google-genai`).
- **Resilient Fallback:** Single-attempt retry (`attempts=1`) prevents hanging on Google preview quotas, with instant automatic fallback to `gemini-flash-lite-latest`.
- **Structured Evidence Grounding:** Enforces strict tripartite output:
  - **Confirmed Findings:** Strictly backed by AST nodes, imports, calls, or schema definitions.
  - **Inferred Hypotheses:** Architectural patterns inferred with stated caveats.
  - **Unresolved Questions:** Acknowledged gaps, dynamic invocations, or unparsed runtime behavior.
- **Prompt Injection Defense:** Strict encapsulation blocks user prompts from overriding architectural guidelines.

### 5. Database & Application Data-Flow Integration
- **DDL & Schema Parsing:** Full support for SQL `CREATE TABLE` statements (data types, primary keys, foreign keys) and Prisma `model` blocks.
- **Cross-Layer AST Edges:** Python parser tracks ORM `__tablename__`, parameter types (`service: OrderService`), model instantiations, and database write calls (`db.add()`, `db.commit()`), creating explicit `reads_from` and `writes_to` graph edges linking application functions directly to database entities.
- **Dedicated ER View (`ERDiagramView`):** Interactive entity cards, attribute inspect, relationship lines, and "Connected App Operations" showing which functions read from or write to each table.

### 6. Change Impact Analysis
- **Reverse-Dependency Engine:** Breadth-First Search (BFS) following incoming caller and dependency edges up to a configurable `max_depth`.
- **Architectural Impact Categorization:** Partitions impacted nodes into direct dependents, transitive dependents, affected API routes, affected database models, and affected unit tests.
- **Deterministic Risk Rating:** Evaluates reach and criticality into `low`, `medium`, `high`, or `critical`.
- **AI Risk Mitigation Advice:** Gemma synthesizes actionable testing and deployment advice based on the affected components.
- **Canvas Integration:** Impacted nodes highlighted in 3D Universe and 2D Flow canvases with glowing amber and rose aura.

### 7. Safe, Reliable Repository-Analysis Pipeline
- **SSRF Prevention:** Host verification (strictly `github.com`), URL validation, and socket DNS pre-resolution blocking private, loopback (`127.0.0.1`), link-local (`169.254.169.254`), and multicast ranges (with RFC 6052 NAT64 compatibility).
- **Safe Zip Extraction:** Enforces strict bounds: 50 MB max zip size, 120 MB max uncompressed size, 5,000 max files, 5 MB max single file size, with strict path traversal prevention (`..`).
- **Zero Code Execution:** Repository files are never executed, installed, or compiled. Ingestion is purely read-only static analysis.
- **Multi-Stage Progress & Cleanup:** Stage-based progress updates (`in_progress` -> `completed`) and explicit `DELETE /api/analyses/{id}` resource cleanup.

---

## ⚡ Graphify Knowledge Graph Integration (Sponsor Feature)

RepoGraph includes a bidirectional adapter for **Graphify** (`Graphify-Labs/graphify`):
- **Standard Knowledge Graph Export:** Seamlessly exports analyzed repository graphs in official Graphify v1 schema format (`GET /api/analyses/{id}/graphify`).
- **Community & Semantic Mapping:** Maps architectural layers and modules directly into Graphify community clusters, node types (`code`, `concept`, `document`, `rationale`), and audited relationship types (`calls`, `imports`, `uses`, `inherits`).
- **Bidirectional Adapter (`graph_adapter.py`):** Translates between RepoGraph's normalized schema and Graphify v1 schema format while preserving stable node IDs, provenance, confidence status, and line references.
- **One-Click Export:** Developers can click the **"Export Graphify"** button in the top navigation to obtain an interoperable knowledge graph for downstream AI coding agents or Graphify tools.

---

## Architecture & Technology Stack

```
repograph/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/             # REST endpoints (health, analyze, graph, explain, trace, impact, api-routes, compare)
│   │   ├── core/            # Config, settings, SSRF protection, safe archive extraction
│   │   ├── models/          # Normalized Pydantic models (nodes, edges, ER, API schemas)
│   │   └── services/        # Parsers (Python AST, JS/TS, SQL/Prisma), GraphBuilder, AI service,
│   │                        # ComparisonService, ApiFlowService, GraphAdapter, ImpactService
│   ├── sample_repos/        # Pre-packaged sample repositories (ecommerce-platform, ecommerce-platform-v2)
│   └── tests/               # Pytest suite (security, parsers, graph builder, trace, impact, comparison, api-flow, adapter)
├── frontend/                 # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── canvas3d/    # React Three Fiber 3D Architecture Universe
│   │   │   ├── canvas2d/    # @xyflow/react 2D Architecture Graph
│   │   │   ├── apiflow/     # API & Application Data-Flow Explorer View
│   │   │   ├── compare/     # Revision Comparison View
│   │   │   ├── er/          # Database Entity-Relationship Diagram
│   │   │   ├── inspector/   # Source code inspector & Gemma intelligence panel
│   │   │   ├── filetree/    # Collapsible file tree & search/filters
│   │   │   └── modals/      # Initial hero landing & stage-based progress
│   │   ├── store/           # Centralized reactive state management (useRepoStore)
│   │   └── utils/           # Architectural layer theme & token utilities
│   └── src/__tests__/       # Vitest & React Testing Library suite
├── docs/                     # Feature audit matrix, implementation plan, architecture docs
├── .env.example              # Configuration template
├── SECURITY.md               # Security architecture & vulnerability disclosure policy
└── README.md
```

### Technologies

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Three.js, React Three Fiber, Drei, `@xyflow/react`, Lucide React |
| **Backend** | Python 3.9+, FastAPI, Pydantic v2, Uvicorn, HTTPX, `google-genai` |
| **Parsing** | Python `ast` module, syntax-aware JavaScript/TypeScript/TSX token parsers, SQL DDL / Prisma schema analyzers |
| **Testing** | Pytest, `pytest-asyncio`, Vitest, React Testing Library, JSDOM |

---

## Security Highlights

RepoGraph enforces layered security for untrusted public repository ingestion:
- **SSRF Prevention:** Strict HTTPS scheme validation, hostname whitelisting (`github.com`), DNS pre-resolution blocking private, loopback (`127.0.0.1`), link-local (`169.254.169.254`), and multicast ranges (with RFC 6052 NAT64 compatibility).
- **Zip-Slip Protection:** Validates that all extracted archive paths remain strictly inside the designated sandboxed temporary directory. Discards dangerous symlinks.
- **Resource Limits:** Enforces strict limits: 50 MB max zip size, 120 MB max uncompressed size, 5,000 max files, 5 MB max single file size.
- **Zero Code Execution:** Repository files are never executed, installed, or compiled. Ingestion is purely read-only static analysis.
- **Credential Protection:** `GEMINI_API_KEY` and `GITHUB_TOKEN` remain strictly on the backend and are never exposed to the client.

See [SECURITY.md](SECURITY.md) for full details.

---

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher (Node 20+ recommended)
- Git

### 1. Clone & Set Up Environment

```bash
git clone -b feat/repograph-3d-mvp <repository-url> repograph
cd repograph

# Copy environment template
cp .env.example .env
cp .env.example backend/.env
```

### 2. Configure Backend

Edit `backend/.env`:
```env
# Optional: Set your Gemini API key for hosted Gemma 4 explanations
GEMINI_API_KEY=your_google_ai_studio_api_key_here
GEMMA_MODEL=gemma-4-26b-a4b-it

# Optional: Set your GitHub token to bypass unauthenticated public API rate limits
GITHUB_TOKEN=
```

Install backend dependencies:
```bash
cd backend
python -m pip install -r requirements.txt
```

Run backend server:
```bash
# Starts FastAPI server on http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Configure Frontend

Open a new terminal:
```bash
cd repograph/frontend

# Install dependencies
npm install

# Run frontend dev server
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## Running Automated Tests

### Backend Tests (Pytest — 17 passed)
```bash
cd repograph/backend
python -m pytest -v
```
Verifies:
- SSRF prevention & DNS resolution checks
- Zip Slip path traversal defense
- Python AST class, route, and model detection
- JavaScript/TypeScript/TSX component & route parsing
- SQL DDL table & relation extraction
- Normalized graph construction & deterministic 3D/2D spatial layout
- Shortest-path BFS feature tracing & transitive change impact propagation
- Graphify bidirectional schema adapter
- API & Application Data-Flow service
- Git revision comparison engine
- FastAPI API endpoints & built-in demo ingestion

### Frontend Tests (Vitest — 6 passed)
```bash
cd repograph/frontend
npm test
```
Verifies:
- Initial landing screen, branding, and sample repository triggers
- Layer color definitions & badge mappings
- ER diagram rendering and honest empty state behavior

### End-to-End Verification Script
```bash
cd repograph
python backend/tests/verify_flow.py
```
Exercises all seven capabilities sequentially against the live backend server.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & application version |
| `GET` | `/api/ai/status` | Hosted Gemma availability & model status (safe, no secrets) |
| `POST` | `/api/repositories/analyze` | Initiates safe ingestion and analysis of a GitHub repository |
| `GET` | `/api/analyses/{id}` | Honest stage-based analysis progress & error reporting |
| `GET` | `/api/analyses/{id}/graph` | Normalized graph with deterministic 3D & 2D spatial layouts |
| `GET` | `/api/analyses/{id}/graphify` | Exports standard Graphify-Labs knowledge graph (`graph.json`) |
| `GET` | `/api/analyses/{id}/api-routes` | Returns all detected framework API endpoints |
| `GET` | `/api/analyses/{id}/api-flow/{route_id}` | Traces downstream data flow: Route -> Middleware -> Service -> DB |
| `POST` | `/api/analyses/{id}/compare` | Compares base analysis against target revision with graph diff |
| `GET` | `/api/analyses/{id}/files` | Hierarchical file inventory tree with symbol counts |
| `GET` | `/api/analyses/{id}/nodes/{node_id}` | Concrete node details, incoming/outgoing edges & verified source snippet |
| `GET` | `/api/analyses/{id}/er-diagram` | Database entities, columns, primary/foreign keys & relations |
| `POST` | `/api/analyses/{id}/explain` | Grounded Gemma 4 explanation for a component or connection |
| `POST` | `/api/analyses/{id}/trace` | Graph-derived feature path tracing with step descriptions |
| `POST` | `/api/analyses/{id}/impact` | Transitive change impact analysis & mitigation guidance |
| `DELETE` | `/api/analyses/{id}` | Deletes analysis session and cached source files from disk |

---

## License & Contributing

- **Software License:** Released under the [Apache License 2.0](LICENSE).
- **Contributing Guidelines:** See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, testing requirements, and Hacktoberfest participation.
- **Security Policy:** See [SECURITY.md](SECURITY.md) for vulnerability disclosure procedures.
- **AI Model Terms:** Hosted Gemma usage adheres to the [Gemma Open Model Terms of Use](https://ai.google.dev/gemma/terms).
