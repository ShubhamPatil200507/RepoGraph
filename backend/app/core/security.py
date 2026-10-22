import ipaddress
import re
import socket
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
from fastapi import HTTPException, status
from app.core.config import settings

# Supported GitHub URL pattern: https://github.com/owner/repo or https://github.com/owner/repo/tree/branch
GITHUB_URL_REGEX = re.compile(
    r"^https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/(?:tree|commits?)/([a-zA-Z0-9_\-\./]+))?/?$"
)

# Ignored directory names for static architecture analysis
IGNORED_DIRS = {
    ".git",
    ".github",
    ".vscode",
    ".idea",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    "target",
    "coverage",
    ".turbo",
    "bin",
    "obj",
}

# Binary and non-source extensions to skip
IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz",
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv",
    ".sqlite", ".sqlite3", ".db", ".lock", ".parquet",
}


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Checks whether an IP address belongs to private, loopback, link-local or restricted ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        # Allow RFC 6052 well-known NAT64 prefix (64:ff9b::/96) used by IPv6 networks for IPv4 public translation
        if isinstance(ip, ipaddress.IPv6Address):
            nat64_prefix = ipaddress.IPv6Network("64:ff9b::/96")
            if ip in nat64_prefix:
                return False
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_github_url(url: str) -> Tuple[str, str, Optional[str]]:
    """
    Validates that a URL is strictly a public GitHub repository.
    Enforces SSRF prevention:
    - Scheme must be HTTPS
    - Host must be strictly 'github.com' (no credentials, no subdomains)
    - IP resolution must not resolve to internal or private addresses
    - Returns (owner, repo, branch)
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository URL is required."
        )

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only HTTPS GitHub URLs are allowed."
        )

    if parsed.username or parsed.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URLs containing embedded credentials are not allowed."
        )

    hostname = (parsed.hostname or "").lower()
    if hostname != "github.com":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only repositories on github.com are permitted. Received host: {hostname or 'none'}"
        )

    # DNS SSRF check: verify github.com resolves to public IP
    try:
        addr_info = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            if is_ip_private_or_restricted(ip):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="DNS resolution returned a forbidden private/local IP address."
                )
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to resolve repository hostname."
        )

    match = GITHUB_URL_REGEX.match(url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL format. Example: https://github.com/owner/repository"
        )

    owner, repo, branch = match.groups()
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Guard against dot-dot traversal in owner or repo name
    if owner in (".", "..") or repo in (".", ".."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository or owner name."
        )

    return owner, repo, branch


def is_path_safe_for_inspection(rel_path: str) -> bool:
    """Returns True if the file should be included in static analysis."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in IGNORED_DIRS or part.startswith("."):
            return False

    suffix = Path(rel_path).suffix.lower()
    if suffix in IGNORED_EXTENSIONS:
        return False

    return True


def safe_extract_zip(zip_bytes: bytes, destination_dir: Path) -> Path:
    """
    Safely extracts a ZIP archive into destination_dir:
    - Protects against Zip Slip (archive path traversal)
    - Rejects symlinks or handles them safely
    - Enforces file count and total size limits
    Returns the root folder of the extracted repository.
    """
    destination_dir = destination_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    file_count = 0

    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        infolist = zf.infolist()
        if len(infolist) > settings.MAX_FILE_COUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository contains too many files ({len(infolist)} > {settings.MAX_FILE_COUNT})."
            )

        for member in infolist:
            file_count += 1
            total_bytes += member.file_size

            if total_bytes > settings.MAX_EXTRACTED_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Extracted repository size exceeds limit ({settings.MAX_EXTRACTED_SIZE_BYTES // (1024*1024)} MB)."
                )

            # Zip Slip check: ensure normalized path stays inside destination_dir
            target_path = (destination_dir / member.filename).resolve()
            if not str(target_path).startswith(str(destination_dir)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsafe archive file path detected (path traversal): {member.filename}"
                )

            # Check for symlink attribute (0o120000 in upper 16 bits of external_attr)
            is_symlink = (member.external_attr >> 16) & 0o170000 == 0o120000
            if is_symlink:
                # Skip symlinks to prevent symlink traversal
                continue

            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source_file, open(target_path, "wb") as dest_file:
                    dest_file.write(source_file.read())

    # GitHub zipballs typically have a top-level directory: owner-repo-sha/
    extracted_children = list(destination_dir.iterdir())
    if len(extracted_children) == 1 and extracted_children[0].is_dir():
        return extracted_children[0]
    return destination_dir
