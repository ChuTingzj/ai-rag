from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:15432/rag"
    redis_url: str = "redis://localhost:16379"
    embedding_provider: str = "local_bge_m3"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    rerank_provider: str = "bge_reranker"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    jwt_secret: str = ""
    internal_service_token: str = ""
    connectors_service_url: str = "http://127.0.0.1:8082"
    connector_encryption_secret: str = ""
    data_dir: str = "./data"


settings = Settings()
