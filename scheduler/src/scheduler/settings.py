"""Application settings loaded from environment variables."""

from typing import Annotated

from annotated_types import Ge
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """SCRAM Scheduler settings."""

    celery_broker_url: str
    celery_result_backend: str
    scram_api_url: str

    process_updates_interval: Annotated[int, Ge(6)] = 30  # in seconds, minimum 6 (because of timeout logic)
    disable_process_updates: bool = False  # Can be used for debugging multi-scram stuff


settings = Settings()  # type: ignore[call-arg]
