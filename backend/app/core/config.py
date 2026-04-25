from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_db: str = "spendmetrics"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    redis_url: str = "redis://redis:6379"

    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    n8n_webhook_url: str = "http://n8n:5678/webhook"
    n8n_api_key: str = ""

    app_env: str = "development"


settings = Settings()
