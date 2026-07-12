from pydantic import Field
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    secret_key: str = Field("change-me-in-production", alias="SECRET_KEY")
    algorithm: str = Field("HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="ALLOWED_ORIGINS",
    )

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}
