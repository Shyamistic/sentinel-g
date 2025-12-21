from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration from environment variables."""
    
    # Google Cloud
    gcp_project_id: str
    gcp_region: str = "us-central1"
    
    # Datadog
    datadog_api_key: str
    datadog_app_key: str
    datadog_site: str = "datadoghq.com"
    datadog_service_name: str = "sentinel-g"
    datadog_env: str = "dev"
    
    # Application
    app_name: str = "SENTINEL-G"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
