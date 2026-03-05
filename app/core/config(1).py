from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Magnitud 19"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str

    # Carga desde .env y acepta variables extra sin romper
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()
