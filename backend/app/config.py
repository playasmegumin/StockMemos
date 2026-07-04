"""应用配置，统一从 .env 文件读取"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库
    database_url: str = "postgresql+psycopg2://trading:changeme@db:5432/agent_trading"

    # TuShare
    tushare_token: str = ""

    # Finnhub（美股备选数据源）
    finnhub_api_key: str = ""

    # Market data source per exchange
    market_data_source_cn: str = "Tushare"
    market_data_source_hk: str = "yfinance"
    market_data_source_us: str = "yfinance"

    # LLM
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # 应用
    app_env: str = "development"
    app_port: int = 8080
    log_level: str = "INFO"

    # 邮件（可选）
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    @property
    def async_database_url(self) -> str:
        """异步数据库 URL（后续使用）"""
        return self.database_url.replace("postgresql+psycopg2", "postgresql+asyncpg")


settings = Settings()
