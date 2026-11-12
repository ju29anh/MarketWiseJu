"""Environment configuration; relative storage paths are rooted at backend/."""
import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, field_validator

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / '.env', override=False)


class Settings(BaseModel):
    port: int = Field(default=8000, ge=1, le=65535)
    host: str = '127.0.0.1'
    environment: Literal['production', 'development', 'test'] = 'production'
    allowed_origins: list[str] = []
    database_url: str = 'sqlite:///./marketwise.db'
    storage_dir: str = ''
    static_dir: str = ''
    public_demo: bool = False
    rate_limit_requests: int = Field(default=12, ge=1, le=300)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    max_research_training: int = Field(default=1, ge=1, le=2)
    secret_key: SecretStr = SecretStr('')
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    max_dataset_rows: int = Field(default=100000, ge=5, le=1000000)
    max_dataset_columns: int = Field(default=200, ge=2, le=1000)
    max_dataset_memory_mb: int = Field(default=128, ge=1, le=1024)
    max_concurrent_analyses: int = Field(default=1, ge=1, le=4)
    max_pending_jobs: int = Field(default=8, ge=1, le=100)
    job_ttl_seconds: int = Field(default=3600, ge=60)
    enable_wikipedia: bool = True
    research_wikipedia: bool = True
    research_wikidata: bool = True
    research_duckduckgo: bool = True
    research_google_news: bool = True
    research_openalex: bool = True
    research_fetch_pages: bool = True
    brave_search_api_key: SecretStr = SecretStr('')
    tavily_api_key: SecretStr = SecretStr('')
    gemini_api_key: SecretStr = SecretStr('')

    @field_validator('environment', mode='before')
    @classmethod
    def normalize_environment(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('allowed_origins')
    @classmethod
    def explicit_origins(cls, values):
        from urllib.parse import urlparse
        for value in values:
            url = urlparse(value)
            if url.scheme not in ('http', 'https') or not url.netloc or url.path or url.query or url.fragment or url.username or '*' in value:
                raise ValueError('ALLOWED_ORIGINS must contain explicit HTTP(S) origins without paths')
        return values

    @property
    def database_path(self) -> Path:
        if not self.database_url.startswith('sqlite:///'):
            raise ValueError('This deployment supports sqlite:/// DATABASE_URL only')
        path = Path(self.database_url.removeprefix('sqlite:///'))
        if self.storage_dir:
            s_path = Path(self.storage_dir)
            root = s_path.resolve() if s_path.is_absolute() else (BACKEND_DIR / s_path).resolve()
        else:
            root = BACKEND_DIR
        return path if path.is_absolute() else (root / path).resolve()

    @property
    def static_path(self) -> Path | None:
        if not self.static_dir:
            return None
        path = Path(self.static_dir)
        return (path if path.is_absolute() else BACKEND_DIR / path).resolve()

    def validate_runtime(self):
        """Fail closed before serving an unsafe or incomplete deployment."""
        if self.environment == 'production':
            secret = self.secret_key.get_secret_value().strip()
            if len(secret) < 32 or secret.lower().startswith(('replace-', 'change', 'your-')):
                raise ValueError('Set a random SECRET_KEY of at least 32 characters')
            if not self.public_demo and self.host not in ('localhost', '127.0.0.1', '::1'):
                raise ValueError('This application has no user authentication. Set PUBLIC_DEMO=true for a public demo; use loopback binding for local use')
        # Resolve this even without opening a connection, so unsupported DBs fail early.
        self.database_path
        path = self.static_path
        if path is not None:
            if path == BACKEND_DIR or path in BACKEND_DIR.parents or path.is_relative_to(BACKEND_DIR):
                raise ValueError('STATIC_DIR must point to the built frontend outside backend source')
            if not (path / 'index.html').is_file() or not (path / 'assets').is_dir():
                raise ValueError('STATIC_DIR must contain a built index.html and assets directory')
            if any(any(part.startswith('.env') or part in ('.git', '.svn', '.codex', '.agents') for part in p.relative_to(path).parts)
                   or p.suffix.lower() in ('.py', '.db', '.sqlite', '.sqlite3', '.pem', '.key', '.log')
                   for p in path.rglob('*') if p.is_file()):
                raise ValueError('STATIC_DIR contains private configuration, source or storage files')


def load_settings() -> Settings:
    values = {name: os.environ[name.upper()] for name in Settings.model_fields if name.upper() in os.environ}
    values['allowed_origins'] = [s.strip() for s in os.getenv('ALLOWED_ORIGINS', '').split(',') if s.strip()]
    return Settings(**values)


settings = load_settings()
DATASETS_DIR = BACKEND_DIR / 'datasets'
UPLOADS_DIR = ((Path(settings.storage_dir) if Path(settings.storage_dir).is_absolute() else (BACKEND_DIR / settings.storage_dir)).resolve() / 'uploads') if settings.storage_dir else DATASETS_DIR / 'uploads'
