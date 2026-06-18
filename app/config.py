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

    # Recall-first: create an incident at >= incident_threshold, BELOW the
    # low/medium severity boundary. Missing fraud (false negative) is worse than
    # surfacing a borderline item for an analyst to dismiss. Incidents in the
    # 0.2-0.3 band are flagged as "low" severity = low-confidence, review.
    incident_threshold: float = 0.2

    # Telegram (Telethon) — uses Telegram Desktop public credentials by default
    tg_api_id: int = 2040
    tg_api_hash: str = "b18441a1ff607e10a989891a5462e627"
    tg_session_name: str = "fraud_monitor_tg"


settings = Settings()
