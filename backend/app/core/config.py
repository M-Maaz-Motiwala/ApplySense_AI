from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApplySense AI"
    env: str = "dev"
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = 120

    database_url: str = Field(..., alias="DATABASE_URL")
    sync_database_url: str = Field(..., alias="SYNC_DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    celery_broker_url: str = Field(..., alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., alias="CELERY_RESULT_BACKEND")

    match_threshold: float = 70.0
    embedding_mode: str = "local"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    groq_api_key: str | None = Field(None, alias="GROQ_API_KEY")
    groq_model: str = Field("llama3-8b-8192", alias="GROQ_MODEL")
    
    primary_llm_provider: str = Field("gemini", alias="PRIMARY_LLM_PROVIDER")
    ollama_base_url: str = Field("https://ollama.com", alias="OLLAMA_BASE_URL")
    ollama_api_key: str | None = Field(None, alias="OLLAMA_API_KEY")
    ollama_model: str = Field("gpt-oss:20b-cloud", alias="OLLAMA_MODEL")

    latex_output_dir: str = "./generated/resumes"
    latex_template_path: str = "app/templates/resume_template.tex.j2"

    gmail_poll_seconds: int = 1800
    job_ingest_cron: str = "0 7 * * *"
    email_monitor_cron: str = "*/30 * * * *"
    gmail_credentials_json: str | None = Field(None, alias="GMAIL_CREDENTIALS_JSON")

    aes256_key_b64: str = Field(..., alias="AES256_KEY_B64")


@lru_cache
def get_settings() -> Settings:
    return Settings()
