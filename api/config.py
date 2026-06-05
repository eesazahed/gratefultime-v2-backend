import os

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    secret_key: str
    gemini_api_key: str
    supabase_url: str
    supabase_secret_key: str = Field(
        validation_alias="SUPABASE_SECRET_KEY"
    )
    supabase_publishable_key: str = ""
    redis_url: str = ""
    gratefultime_dev_mode: bool = False
    apple_audience_v2: str = "app.gratefultime.v2"
    revenuecat_webhook_secret: str = ""
    free_ai_previews_per_month: int = 1
    gemini_model: str = "gemini-2.5-flash"

    @property
    def dev_mode(self) -> bool:
        return self.gratefultime_dev_mode

    @property
    def apple_audiences(self) -> list[str]:
        if self.dev_mode:
            return ["host.exp.Exponent", self.apple_audience_v2]
        return [self.apple_audience_v2]

    @model_validator(mode="before")
    @classmethod
    def resolve_supabase_secret_key(cls, values):
        if not isinstance(values, dict):
            return values

        secret_key = (
            values.get("supabase_secret_key")
            or os.getenv("SUPABASE_SECRET_KEY")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        if secret_key:
            values["supabase_secret_key"] = secret_key

        publishable_key = (
            values.get("supabase_publishable_key")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
        )
        if publishable_key:
            values["supabase_publishable_key"] = publishable_key

        return values


settings = Settings()
