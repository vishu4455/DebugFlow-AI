from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    APP_NAME: str = "Pipeline Failure Debugger"
    DEBUG: bool = False

    # Gemini
    GEMINI_API_KEY: str = "your-gemini-api-key"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Postgres
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pipeline_debugger"

    # Airflow
    AIRFLOW_BASE_URL: str = "http://localhost:8080"
    AIRFLOW_USERNAME: str = "airflow"
    AIRFLOW_PASSWORD: str = "airflow"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"
    S3_LOG_BUCKET: str = "my-pipeline-logs"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Auth / JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Demo users (in production use a real user table)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"   # hashed at startup
    DEMO_USERNAME: str = "demo"
    DEMO_PASSWORD: str = "demo123"

    # API Keys (comma-separated)
    API_KEYS: str = "dev-key-12345,ci-key-67890"

    # SSE / streaming
    SSE_HEARTBEAT_SECONDS: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
