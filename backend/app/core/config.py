from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mega AI"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/megaai"
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        # Optional: enable this if we have docker-compose overriding things
        env_file_encoding = "utf-8"

settings = Settings()