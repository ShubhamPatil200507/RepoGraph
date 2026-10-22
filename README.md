# RepoGraph

**See how your code works. Explore how everything connects.**

RepoGraph is an interactive software architecture explorer that transforms GitHub repositories into source-backed, three-dimensional maps of modules, entities, dependencies, and execution paths. Developers can explore how a project works, inspect real code relationships, and use hosted Gemma to explain complex connections.

---

## Core Product Principle

> **Deterministic code analysis discovers what exists.  
> Graph algorithms determine how components connect.  
> Gemma explains the evidence.  
> The visualization makes the architecture understandable.**

RepoGraph never uses language models as a substitute for syntax-aware code parsing or graph construction. Deterministic AST parsers identify verified symbols, routes, models, and dependencies. Hosted Gemma is used exclusively to explain verified findings grounded strictly in repository evidence.

---

## Key Features

### 1. Interactive 3D Architecture Universe
- **Navigable Spatial Universe:** Rendered with Three.js, React Three Fiber, and Drei.
- **Topological Layering:** Modules and entities are spatially stratified by architectural layers (UI, API, Business Logic, Data Access, Database, Config, Tests).
- **Deterministic Seeded Layout:** Stable, reproducible spatial positioning across repeated analyses.
- **Dynamic Highlighting & Dimming:** Selecting any node highlights immediate neighbors and active connection rays while gently dimming unrelated clusters.
- **Accessible Orbit Controls:** Smooth damping, zoom, pan, camera reset, and automatic focus-fly-to on selected components.

### 2. Complementary 2D Architecture Graph
- Powered by `@xyflow/react` (React Flow) for developers who prefer flat, structured diagrams.
- Uses the **exact same normalized graph schema** as the 3D universe.
- Interactive node cards showing symbol type, architectural layer, confidence, and line references.
- Full selection synchronization with the 3D universe and source inspector.

### 3. Dedicated Entity-Relationship (ER) Diagram
- Automatically detects database models from SQLAlchemy, Prisma schemas, Django models, and SQL DDL (`CREATE TABLE`).
- Displays entities, attributes, primary keys (`PK`), foreign keys (`FK`), and verified relationships.
- **Honest Empty State:** When no database evidence exists, RepoGraph clearly states what was checked instead of fabricating fake tables.

### 4. Real Source Inspector & Grounding Evidence Panel
- Inspect real source code snippets extracted from analyzed repository files with exact line numbers.
- Safe external links to GitHub (`blob/main/path#L42-L88`).
- Interactive incoming and outgoing relationship lists with clickable graph navigation.
- Clear evidence status badges (`verified`, `inferred`, `unknown`).

### 5. Hosted Gemma 4 Architecture Intelligence
- Uses the official Google Gen AI Python SDK (`google-genai`) with model identifier `gemma-4-26b-a4b-it`.
- Strictly evidence-grounded: provided only with selected node details, verified edges, and extracted source snippets.
- Explicitly separates **Confirmed Findings**, **Inferred Hypotheses**, and **Unresolved Questions**.
- **Graceful Degradation:** The entire application (parsing, 3D/2D exploration, ER diagrams, feature tracing) remains fully functional without an API key; AI actions are marked clearly as unavailable.

### 6. Feature Path Tracing
- Traverses the static dependency graph using Breadth-First Search (BFS) to identify shortest connection paths between components.
- Highlights path sequences across the 3D and 2D canvas with step-by-step evidence.
- Gemma explains how control or data flows across the discovered path.

### 7. Change Impact Analysis
- "What might break if this component changes?"
- Reverse-dependency graph traversal computes direct and transitive dependents.
- Highlights affected API routes, database models, and unit tests with risk mitigation advice from Gemma.

---

## Architecture & Technology Stack

```
repograph/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/             # REST endpoints (health, analyze, graph, explain, trace, impact)
│   │   ├── core/            # Config, settings, SSRF protection, safe archive extraction
│   │   ├── models/          # Normalized Pydantic models (nodes, edges, ER, API schemas)
│   │   └── services/        # Parsers (Python AST, JS/TS, SQL/Prisma), GraphBuilder, AI service
│   ├── sample_repos/        # Pre-packaged sample repositories for instant local exploration
│   └── tests/               # Pytest suite (security, parsers, graph builder, trace, impact, API)
├── frontend/                 # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── canvas3d/    # React Three Fiber 3D Architecture Universe
│   │   │   ├── canvas2d/    # @xyflow/react 2D Architecture Graph
│   │   │   ├── er/          # Database Entity-Relationship Diagram
│   │   │   ├── inspector/   # Source code inspector & Gemma intelligence panel
│   │   │   ├── filetree/    # Collapsible file tree & search/filters
│   │   │   └── modals/      # Initial hero landing & stage-based progress
│   │   ├── store/           # Centralized reactive state management
│   │   └── utils/           # Architectural layer theme & token utilities
│   └── src/__tests__/       # Vitest & React Testing Library suite
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
- **Resource Limits:** Enforces strict limits: 50 MB max zip size, 120 MB max uncompressed size, 3,500 max files, 2 MB max single file size.
- **Zero Code Execution:** Repository files are never executed, installed, or compiled. Ingestion is purely read-only static analysis.
- **Credential Protection:** `GEMINI_API_KEY` and `GITHUB_TOKEN` remain strictly on the backend and are never sent to the client.

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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

### Backend Tests (Pytest)
```bash
cd repograph/backend
python -m pytest -v
```
All 13 unit tests verify:
- SSRF prevention & DNS resolution checks
- Zip Slip path traversal defense
- Python AST class, route, and model detection
- JavaScript/TypeScript/TSX component & route parsing
- SQL DDL table & relation extraction
- Normalized graph construction & deterministic 3D/2D spatial layout
- Shortest-path BFS feature tracing & transitive change impact propagation
- FastAPI API endpoints & built-in demo ingestion

### Frontend Tests (Vitest & React Testing Library)
```bash
cd repograph/frontend
npm test
```
All unit tests verify:
- Initial landing screen, branding, and sample repository triggers
- Layer color definitions & badge mappings
- ER diagram rendering and honest empty state behavior

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & application version |
| `GET` | `/api/ai/status` | Hosted Gemma availability & model status (safe, no secrets) |
| `POST` | `/api/repositories/analyze` | Initiates safe ingestion and analysis of a GitHub repository |
| `GET` | `/api/analyses/{id}` | Honest stage-based analysis progress & error reporting |
| `GET` | `/api/analyses/{id}/graph` | Normalized graph with deterministic 3D & 2D spatial layouts |
| `GET` | `/api/analyses/{id}/files` | Hierarchical file inventory tree with symbol counts |
| `GET` | `/api/analyses/{id}/nodes/{node_id}` | Concrete node details, incoming/outgoing edges & verified source snippet |
| `GET` | `/api/analyses/{id}/er-diagram` | Database entities, columns, primary/foreign keys & relations |
| `POST` | `/api/analyses/{id}/explain` | Grounded Gemma 4 explanation for a component or connection |
| `POST` | `/api/analyses/{id}/trace` | Graph-derived feature path tracing with step descriptions |
| `POST` | `/api/analyses/{id}/impact` | Transitive change impact analysis & mitigation guidance |
| `DELETE` | `/api/analyses/{id}` | Deletes analysis session and cached source files from disk |

---

## License

Apache-2.0 License.
