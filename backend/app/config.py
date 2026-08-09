from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. All values overridable via environment variables or a .env file.
    Defaults are safe for local dev (SQLite, no Azure creds required)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database: swap DATABASE_URL to a Postgres Flexible Server DSN in production.
    # e.g. postgresql+psycopg2://user@host:5432/dbname (Entra auth token as password)
    database_url: str = "sqlite:///./dev.db"

    # API security mode for admin write operations (ingest).
    # - none: no app-level auth (local dev only)
    # - api_key: require X-API-KEY header
    # - azure_ad: require Azure AD bearer token
    auth_mode: str = "none"
    ingest_api_key: str | None = None
    azure_ad_tenant_id: str | None = None
    azure_ad_client_id: str | None = None
    azure_ad_audience: str | None = None

    # CORS: local dev default is the Vite frontend port.
    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        if not self.allowed_origins:
            return []
        if self.allowed_origins.startswith("["):
            import json

            try:
                parsed = json.loads(self.allowed_origins)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    # Azure AI Foundry / Azure AI Search — required only when using the live RAG chain.
    azure_ai_project_endpoint: str | None = None
    azure_ai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    azure_search_endpoint: str | None = None
    azure_search_api_key: str | None = None
    azure_search_index_name: str = "supplier-facts"
    azure_embedding_deployment: str = "text-embedding-3-large"
    azure_chat_deployment: str = "gpt-4o"

    default_price_weight: float = 0.35
    default_lead_time_weight: float = 0.25
    default_quality_weight: float = 0.25
    default_sustainability_weight: float = 0.15

    log_level: str = "INFO"
    log_format: str = "%(asctime)s %(levelname)s %(name)s %(message)s"

    sentry_dsn: str | None = None
    environment: str = "development"

    @property
    def azure_rag_enabled(self) -> bool:
        return bool(self.azure_search_endpoint and (self.azure_ai_project_endpoint or self.azure_openai_endpoint))


settings = Settings()
