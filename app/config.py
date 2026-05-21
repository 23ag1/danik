from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        protected_namespaces=("settings_",),
    )

    app_name: str = "Fraud Monitor"
    database_url: str = "sqlite+aiosqlite:///./fraud_monitor.db"
    ml_artifacts_dir: str = "models"

    risk_weight_rule: float = 0.35
    risk_weight_ml: float = 0.35
    risk_weight_graph: float = 0.15
    risk_weight_anomaly: float = 0.15

    risk_threshold_low: float = 0.3
    risk_threshold_high: float = 0.7

    # Telegram (Telethon) — optional, leave empty to disable TG collector
    tg_api_id: int = 0
    tg_api_hash: str = ""
    tg_session_name: str = "fraud_monitor_tg"


settings = Settings()
