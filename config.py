from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qr_manager_user:6Vnr63gWlKZvcfsvyF2W8BgxM3GkZQTw@dpg-d5ot6u24d50c739pp190-a.oregon-postgres.render.com:5432/qr_manager"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Server
    BASE_URL: str = "https://social-media-vmfr.onrender.com"
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()