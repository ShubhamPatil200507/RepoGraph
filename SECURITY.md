# Security Policy — RepoGraph

RepoGraph treats application security as a fundamental requirement. Because repository analysis processes untrusted public code and interacts with external network APIs, multiple security layers are enforced throughout the ingestion, parsing, and explanation workflows.

---

## 1. Threat Model & Mitigations

### 1.1 Server-Side Request Forgery (SSRF) Protection

When users supply repository URLs, malicious actors might attempt to target internal network services, cloud metadata endpoints (`169.254.169.254`), or private intranets.

**Mitigations Implemented:**
- **Scheme Validation:** Only `https://` URLs are accepted. Plain HTTP, FTP, file schemes, and custom schemes are strictly rejected.
- **Hostname Whitelisting:** URLs must match `github.com` or `www.github.com`. Arbitrary hosts, redirects to third-party domains, and IP-based hostnames are forbidden.
- **DNS Resolution Pre-checks:** Before any HTTP connection is initiated, the target hostname is resolved via `socket.getaddrinfo`. The resolved IP addresses are evaluated:
  - Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`) are blocked.
  - Loopback addresses (`127.0.0.0/8`, `::1`) are blocked.
  - Link-local endpoints (`169.254.0.0/16`, `fe80::/10`) are blocked.
  - Multicast and unspecified ranges are blocked.
  - Standard RFC 6052 NAT64 prefixes (`64:ff9b::/96`) used by IPv6 networks for IPv4 public translation are verified safely.
- **Credential Stripping:** URLs containing embedded basic auth credentials (e.g. `https://user:pass@github.com/...`) are rejected immediately.

---

### 1.2 Archive Path Traversal (Zip Slip) Defense

Malicious ZIP archives can contain path elements such as `../../etc/cron.d/evil` to overwrite system files during decompression.

**Mitigations Implemented:**
- **Canonical Path Enforcement:** Every ZIP entry is resolved against the designated sandboxed temporary directory using `(destination_dir / member.filename).resolve()`. If the normalized path does not start with `destination_dir`, extraction halts immediately with a 400 error.
- **Symlink Neutralization:** ZIP members marked as symbolic links (external attributes matching `0o120000`) are discarded during extraction to prevent symlink traversal attacks.
- **Decompression Bomb Protection:**
  - Maximum archive download size is capped at 50 MB (`MAX_REPO_ZIP_SIZE_BYTES`).
  - Total uncompressed size limit is capped at 120 MB (`MAX_EXTRACTED_SIZE_BYTES`).
  - Total file count is capped at 3,500 files (`MAX_FILE_COUNT`).

---

### 1.3 Zero Code Execution (Static-Only Analysis)

RepoGraph performs **strictly static analysis**:
- Repository files are **never executed**, compiled, or imported as live Python/JS runtime modules.
- Dependency installation commands (`pip install`, `npm install`, `setup.py`, `package.json` scripts) are **never executed**.
- Analysis is performed exclusively using AST inspection (`ast.parse`) and regex/token analyzers on raw source strings.

---

### 1.4 API & Credential Security

- **Backend-Only Provider Access:** The Google GenAI SDK and `GEMINI_API_KEY` are isolated entirely to the FastAPI backend. Keys are never transmitted in API responses, frontend bundles, or browser network traffic.
- **Narrow CORS:** Cross-Origin Resource Sharing is configured to allow only the verified frontend origin (`FRONTEND_ORIGIN`).
- **Leakage Prevention:** Production API errors return clean, generic error descriptions without leaking internal Python stack traces, server paths, or environment variables.
- **Resource Cleanup:** Temporary extracted repository files are scoped to unique isolated directories and deleted when the analysis session is terminated via `DELETE /api/analyses/{analysis_id}`.

---

## 2. Reporting a Vulnerability

If you discover a potential security vulnerability in RepoGraph, please report it privately:
- Do not open a public GitHub issue.
- Provide a clear description, reproduction steps, and potential impact.
- Security updates and patches will be prioritized and verified.
