import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    """
    Application-wide configuration variables.
    Reads from environment variables automatically.
    """
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "5000"))
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "fraud_history.db"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "suraksha-super-secret-key-change-in-prod")
    CORS_ORIGINS: list = field(default_factory=lambda: ["*"])
    
    # Rate Limiting
    RATELIMIT_STORAGE_URI: str = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    
    # NLP / ML Config
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "5000"))

# Instantiate a singleton settings object
settings = Settings()
