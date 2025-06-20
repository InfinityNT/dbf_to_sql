from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "mysql+pymysql://sales_user:sales_pass@mysql:3306/sales_db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # DBF Files
    dbf_watch_path: str = "/app/data"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Create data directory if it doesn't exist
Path(settings.dbf_watch_path).mkdir(parents=True, exist_ok=True)