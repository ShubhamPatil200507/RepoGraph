# Contributing to RepoGraph

Thank you for your interest in contributing to **RepoGraph**! We welcome contributions from developers, researchers, open-source maintainers, and Hacktoberfest participants.

---

## Code of Conduct

RepoGraph is dedicated to providing a welcoming, inclusive, and harassment-free experience for everyone. Please be respectful and constructive in all communications.

---

## Core Product Principles

When contributing code, parsers, or architecture analysis logic, adhere to our foundational design rule:

> **Deterministic code analysis discovers what exists.**  
> **Graph algorithms determine how components connect.**  
> **Gemma explains the evidence.**  
> **The visualization makes the architecture understandable.**

Never substitute LLM hallucinations for syntax-aware parsing or deterministic graph algorithms. AI is used exclusively to explain verified findings grounded in code evidence.

---

## Development Setup

### 1. Prerequisites
- Python 3.9+
- Node.js 18+ (Node 20+ recommended)
- Git

### 2. Local Setup
```bash
# Clone the repository
git clone https://github.com/ShubhamPatil200507/RepoGraph.git
cd RepoGraph

# Setup Backend
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
# Optional: add your GEMINI_API_KEY to backend/.env

# Setup Frontend
cd ../frontend
npm install
```

### 3. Running Dev Servers
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Automated Testing & Validation

All pull requests must pass the automated test suites before being merged:

```bash
# Backend unit & integration tests (Pytest)
cd backend
python -m pytest -v

# Frontend component tests (Vitest)
cd frontend
npm run test -- --run

# Frontend production build
cd frontend
npm run build
```

---

## Submitting Pull Requests

1. **Create a descriptive feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   # or fix/your-bugfix-name
   ```
2. **Commit your changes:**
   Use clear, conventional commit messages:
   - `feat:` for new capabilities
   - `fix:` for bug fixes
   - `docs:` for documentation updates
   - `test:` for new tests or fixtures
3. **Ensure tests pass:** Run both backend and frontend test suites locally.
4. **Open a Pull Request:** Fill in the provided PR template with a summary, problem statement, validation results, and evidence grounding details.

---

## Security

Please do not report security vulnerabilities through public GitHub issues. Review our [SECURITY.md](SECURITY.md) for private disclosure instructions.
