from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
              
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

           
    REDIS_URL: str
    REDIS_POOL_MAX: int = 20

         
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

                   
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    API_BASE_URL: str = "http://localhost:8000"

    # ── App identity ──────────────────────────────────────────────────────────────
    # MindLayer — Personal AI Second Brain
    APP_NAME: str = "MindLayer"
    APP_TAGLINE: str = "Personal AI Second Brain"
    CONTACT_EMAIL: str = "hello@mindlayer.local"

    # ── Email ─────────────────────────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@mindlayer.local"
    EMAIL_FROM_NAME: str = "MindLayer"

           
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_BUCKET: str = "rag-docs"
    MINIO_SECURE: bool = False

              
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

                      
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048



    OPENAI_API_KEY: str = ""
    EMBED_MODEL: str = "text-embedding-3-small"
    EMBED_DIMENSIONS: int = 1536
    EMBED_BATCH_SIZE: int = 64

                     
    JINA_API_KEY: str = ""
    JINA_RERANKER_MODEL: str = "jina-reranker-v2-base-multilingual"
    JINA_RERANKER_TOP_N: int = 5

                         
    EVALUATOR_FAILURE_MODE: str = "warn_only"

            
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

                   
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 1000

         
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.casefold() == "production"

    @model_validator(mode="after")
    def validate_environment_settings(self):
        self.ENVIRONMENT = self.ENVIRONMENT.casefold()
        self.EVALUATOR_FAILURE_MODE = self.EVALUATOR_FAILURE_MODE.casefold()
        self._validate_ai_runtime_settings()
        if self.is_production:
            self._validate_production_settings()
        else:
            if not self.MINIO_ACCESS_KEY:
                self.MINIO_ACCESS_KEY = "minioadmin"
            if not self.MINIO_SECRET_KEY:
                self.MINIO_SECRET_KEY = "minioadmin"
        return self

    def _validate_ai_runtime_settings(self) -> None:
        if self.EMBED_BATCH_SIZE < 1 or self.EMBED_BATCH_SIZE > 2048:
            raise ValueError("EMBED_BATCH_SIZE must be between 1 and 2048")
        allowed_modes = {"warn_only", "fail_open", "fail_closed"}
        if self.EVALUATOR_FAILURE_MODE not in allowed_modes:
            raise ValueError(
                "EVALUATOR_FAILURE_MODE must be one of: warn_only, fail_open, fail_closed"
            )

    def _validate_production_settings(self) -> None:
        self._require_strong_jwt_secret()
        self._require_explicit_cors_origins()
        self._require_provider_keys()
        self._require_secure_minio_credentials()

    def _require_strong_jwt_secret(self) -> None:
        placeholders = {
            "change-me",
            "change-me-to-a-random-256-bit-secret",
            "test-secret-key-change-in-production",
            "secret",
            "your-secret-key",
        }
        normalized_secret = self.JWT_SECRET_KEY.strip().casefold()
        if normalized_secret in placeholders or "change-me" in normalized_secret:
            raise ValueError("JWT_SECRET_KEY must not use a placeholder value in production")
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")

    def _require_explicit_cors_origins(self) -> None:
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must define at least one origin in production")
        for origin in origins:
            if origin == "*":
                raise ValueError("ALLOWED_ORIGINS cannot contain '*' in production")
            if not origin.startswith(("https://", "http://")):
                raise ValueError("ALLOWED_ORIGINS must contain explicit HTTP(S) origins in production")

    def _require_provider_keys(self) -> None:
        required_keys = {
            "OPENROUTER_API_KEY": self.OPENROUTER_API_KEY,
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "JINA_API_KEY": self.JINA_API_KEY,
        }
        missing = [name for name, value in required_keys.items() if not value.strip()]
        if missing:
            raise ValueError(f"Missing provider keys in production: {', '.join(missing)}")

    def _require_secure_minio_credentials(self) -> None:
        if not self.MINIO_ACCESS_KEY or not self.MINIO_SECRET_KEY:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY must be set in production")
        if self.MINIO_ACCESS_KEY == "minioadmin" or self.MINIO_SECRET_KEY == "minioadmin":
            raise ValueError("Default MinIO credentials are not allowed in production")


settings = Settings()
