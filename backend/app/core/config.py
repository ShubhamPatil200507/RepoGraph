import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "RepoGraph"
    APP_VERSION: str = "1.0.0"
    TAGLINE: str = "See how your code works. Explore how everything connects."

    # Gemini / Gemma AI Configuration
    GEMINI_API_KEY: str = ""
    GEMMA_MODEL: str = "gemma-4-26b-a4b-it"
    FALLBACK_GEMMA_MODELS: list = ["gemma-2-27b-it", "gemma-2-9b-it", "gemini-2.5-flash"]

    # GitHub Access (Optional for public repos)
    GITHUB_TOKEN: str = ""

    # Frontend CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Security & Ingestion Limits
    MAX_REPO_ZIP_SIZE_BYTES: int = 50 * 1024 * 1024       # 50 MB
    MAX_EXTRACTED_SIZE_BYTES: int = 120 * 1024 * 1024     # 120 MB
    MAX_FILE_COUNT: int = 3500                            # max 3500 files
    MAX_SINGLE_FILE_SIZE_BYTES: int = 2 * 1024 * 1024     # 2 MB per file
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    AI_TIMEOUT_SECONDS: float = 45.0

    # Analysis Cache Storage Directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage" / "analyses"



settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
