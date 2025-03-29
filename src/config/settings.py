from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # AliExpress API Settings
    ALIEXPRESS_API_KEY: str
    ALIEXPRESS_AFFILIATE_ID: str
    ALIEXPRESS_APP_SECRET: str
    
    # Application Settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # Optional Settings
    LOG_LEVEL: str = "INFO"
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 