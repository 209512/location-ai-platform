from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 데이터베이스 설정
    database_url: str = "postgresql+asyncpg://user:password@localhost/locationdb"

    # Redis 설정
    redis_url: str = "redis://localhost:6379"

    # AI API 설정
    openai_api_key: str = "your-openai-api-key"

    # URL 단축기 설정
    base_url: str = "http://localhost:8000"

    # 보안 설정
    secret_key: str = "your-secret-key"

    # 환경 설정
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
