from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mega AI"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/megaai"
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000
    
    # Tuning configurations
    BUFFER_FLUSH_INTERVAL: float = 2.0  # seconds between background flushes
    BUFFER_MAX_SIZE: int = 50           # bulk insert trigger size
    ROI_SHIFT_THRESHOLD: float = 0.05   # % movement required to log ROI (0.05 = 5%)
    ROI_TIME_THRESHOLD: float = 1.0     # seconds before forcing an ROI log regardless of movement

    class Config:
        env_file = ".env"
        # Optional: enable this if we have docker-compose overriding things
        env_file_encoding = "utf-8"

settings = Settings()