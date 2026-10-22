import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security import safe_extract_zip, validate_github_url


class GitHubFetcher:
    @staticmethod
    async def fetch_and_extract_repository(
        repository_url: str,
        branch: Optional[str] = None
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Validates GitHub repository URL, streams zipball archive,
        and safely extracts it into an isolated temporary directory.
        Returns (extracted_root_path, repo_metadata).
        """
        owner, repo, url_branch = validate_github_url(repository_url)
        target_branch = branch or url_branch or ""

        # Check for built-in demo repository requests
        if owner.lower() == "repograph-demo":
            return GitHubFetcher._load_built_in_demo(repo)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoGraph-Architecture-Explorer/1.0",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        # Construct GitHub zipball endpoint
        archive_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        if target_branch:
            archive_url += f"/{target_branch}"

        dest_dir = Path(tempfile.mkdtemp(prefix=f"repograph_{owner}_{repo}_"))

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            ) as client:
                # 1. Fetch metadata
                meta_url = f"https://api.github.com/repos/{owner}/{repo}"
                meta_res = await client.get(meta_url, headers=headers)
                repo_meta = {
                    "owner": owner,
                    "repo": repo,
                    "branch": target_branch,
                    "full_name": f"{owner}/{repo}",
                    "description": "",
                    "default_branch": "main",
                    "stars": 0,
                    "forks": 0,
                }
                if meta_res.status_code == 200:
                    data = meta_res.json()
                    repo_meta["description"] = data.get("description") or ""
                    repo_meta["default_branch"] = data.get("default_branch") or "main"
                    repo_meta["stars"] = data.get("stargazers_count", 0)
                    repo_meta["forks"] = data.get("forks_count", 0)
                    if not target_branch:
                        repo_meta["branch"] = repo_meta["default_branch"]
                elif meta_res.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"GitHub repository '{owner}/{repo}' not found or is private."
                    )
                elif meta_res.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="GitHub API rate limit exceeded. Please configure GITHUB_TOKEN or try again later."
                    )

                # 2. Download zipball
                stream_res = await client.get(archive_url, headers=headers)
                if stream_res.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Failed to download repository archive from GitHub (Status {stream_res.status_code})."
                    )

                zip_bytes = stream_res.content
                if len(zip_bytes) > settings.MAX_REPO_ZIP_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Repository zip archive exceeds maximum size limit ({settings.MAX_REPO_ZIP_SIZE_BYTES // (1024*1024)} MB)."
                    )

                extracted_root = safe_extract_zip(zip_bytes, dest_dir)
                return extracted_root, repo_meta

        except HTTPException:
            shutil.rmtree(dest_dir, ignore_errors=True)
            raise
        except Exception as e:
            shutil.rmtree(dest_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed during repository ingestion: {str(e)}"
            )

    @staticmethod
    def _load_built_in_demo(sample_name: str) -> Tuple[Path, Dict[str, Any]]:
        """Loads a built-in sample repository structure for instant testing."""
        demo_base = settings.BASE_DIR / "sample_repos" / sample_name
        if not demo_base.exists():
            # If default sample doesn't exist yet, we'll initialize it
            if sample_name == "ecommerce-platform-v2":
                from app.services.sample_generator import ensure_sample_repo_v2
                ensure_sample_repo_v2(demo_base)
            else:
                from app.services.sample_generator import ensure_sample_repo
                ensure_sample_repo(demo_base)

        dest_dir = Path(tempfile.mkdtemp(prefix=f"repograph_demo_{sample_name}_"))
        shutil.copytree(demo_base, dest_dir, dirs_exist_ok=True)
        return dest_dir, {
            "owner": "repograph-demo",
            "repo": sample_name,
            "branch": "main",
            "full_name": f"repograph-demo/{sample_name}",
            "description": "RepoGraph Interactive Architecture Demo",
            "default_branch": "main",
            "stars": 420,
            "forks": 42,
        }
